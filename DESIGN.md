# Design: Agentic Review Assistant for Impact Measurement Results

## Motivation

The impact engine pipeline produces causal effect estimates through
`tools-impact-engine-measure`. These results — point estimates, confidence
intervals, model diagnostics — require expert judgement to interpret. Is the
effect estimate plausible? Is the model type appropriate for the data? Are the
diagnostics healthy?

The deterministic confidence scorer (`scorer.py`) assigns a confidence band
based on methodology type alone. It cannot reason about the *content* of the
results. The agentic review layer adds LLM-powered evaluation of the actual
measurement artifacts, producing structured, auditable review judgements.

Together, the two layers form a complete EVALUATE stage:

```
MeasureResult ──► Deterministic Scorer ──► confidence score (0–1)
             └──► Agentic Reviewer    ──► per-dimension scores + justifications
```

## Architecture overview

```
┌─────────────────────────────────────────────────────┐
│                   ReviewEngine                       │
│                                                     │
│  ┌──────────┐   ┌──────────────┐   ┌────────────┐  │
│  │ Backend  │   │ PromptRegistry│   │KnowledgeBase│  │
│  │ Registry │   │ + Renderer   │   │ (optional) │  │
│  └────┬─────┘   └──────┬───────┘   └─────┬──────┘  │
│       │                │                  │         │
│       ▼                ▼                  ▼         │
│  ┌─────────┐   ┌─────────────┐   ┌────────────┐   │
│  │Anthropic│   │  YAML/Jinja │   │   Static   │   │
│  │ OpenAI  │   │  Templates  │   │  Markdown  │   │
│  │ LiteLLM │   └─────────────┘   │   Files    │   │
│  └─────────┘                     └────────────┘   │
└─────────────────────────────────────────────────────┘
         │
         ▼
   ReviewResult
   ├── dimensions[]  (name, score, justification)
   ├── overall_score
   └── raw_response  (audit trail)
```

## Components

### Existing — deterministic scorer

| File | Role |
|------|------|
| `scorer.py` | Pure function `score_initiative()` — maps `ModelType` to a confidence range via `CONFIDENCE_MAP`, draws a deterministic score seeded by `initiative_id` |
| `adapter.py` | `Evaluate` PipelineComponent wrapping the scorer |

These are unchanged by the review subsystem.

### Review subsystem

| File | Role |
|------|------|
| `review/models.py` | Data models: `ReviewResult`, `ReviewDimension`, `ArtifactPayload`, `PromptSpec` |
| `review/engine.py` | `ReviewEngine` — orchestrates a single review: load prompt, retrieve knowledge, render template, call backend, parse response |
| `review/backends/base.py` | `Backend` ABC + `BackendRegistry` (decorator-based registration) |
| `review/backends/anthropic_backend.py` | Anthropic Messages API backend |
| `review/backends/openai_backend.py` | OpenAI Chat Completions backend |
| `review/backends/litellm_backend.py` | LiteLLM unified backend (100+ providers) |
| `review/prompts/registry.py` | `PromptRegistry` — discovers YAML templates from built-in and user-supplied directories |
| `review/prompts/renderer.py` | Jinja2 template rendering (falls back to `str.format_map`) |
| `review/prompts/templates/*.yaml` | Built-in prompt templates |
| `review/knowledge/base.py` | `KnowledgeBase` ABC + `Chunk` dataclass |
| `review/knowledge/static.py` | `StaticKnowledgeBase` — keyword-overlap retrieval from `.md`/`.txt` files |
| `review/review_adapter.py` | `ArtifactReview` PipelineComponent wrapping `ReviewEngine` |
| `config.py` | `ReviewConfig` — loads from YAML/dict/env vars |

### Registry pattern

All three pluggable dimensions use the same idiom:

```python
@BackendRegistry.register("anthropic")
class AnthropicBackend(Backend): ...
```

This allows extension without modifying package code. Backends auto-register on
import; missing SDKs are silently skipped.

## Data flow

### Pipeline context

The orchestrator pipeline flows:

```
MEASURE ──► EVALUATE ──► ALLOCATE ──► SCALE
```

The Measure → Evaluate contract (from the orchestrator) passes:

| Field | Type | Description |
|-------|------|-------------|
| `initiative_id` | str | Unique identifier |
| `effect_estimate` | float | Point estimate of causal effect |
| `ci_lower` / `ci_upper` | float | Confidence interval bounds |
| `p_value` | float | Statistical significance |
| `sample_size` | int | Number of observations |
| `model_type` | ModelType | Methodology used |
| `diagnostics` | dict | Model fit diagnostics |

### Measure output structure

The `MeasureJobResult` from `tools-impact-engine-measure` contains richer data
than the orchestrator contract. The `impact_results.json` envelope:

```json
{
  "schema_version": "2.0",
  "model_type": "interrupted_time_series",
  "data": {
    "model_params": {
      "intervention_date": "2024-01-15",
      "dependent_variable": "revenue"
    },
    "impact_estimates": {
      "intervention_effect": 12.5,
      "pre_intervention_mean": 100.0,
      "post_intervention_mean": 112.5,
      "absolute_change": 12.5,
      "percent_change": 12.5
    },
    "model_summary": {
      "n_observations": 365,
      "pre_period_length": 200,
      "post_period_length": 165,
      "aic": 1234.5,
      "bic": 1245.8
    }
  },
  "metadata": {
    "executed_at": "2025-06-01T12:00:00+00:00"
  }
}
```

The review assistant operates on a text serialization of this data, passed as
`artifact_text` in the `ArtifactPayload`. The exact serialization format is
deferred to a later phase (see PLAN.md).

### Review input

The `ArtifactPayload` envelope:

```python
@dataclass
class ArtifactPayload:
    initiative_id: str
    artifact_text: str       # serialized measure results
    model_type: str          # methodology label
    sample_size: int
    metadata: dict           # additional context
```

### Review output

```python
@dataclass
class ReviewResult:
    initiative_id: str
    prompt_name: str         # which template was used
    prompt_version: str
    backend_name: str        # which LLM backend
    model: str               # which model
    dimensions: list[ReviewDimension]  # per-axis scores
    overall_score: float     # aggregated (mean of dimensions)
    raw_response: str        # full LLM output for audit
    timestamp: str           # ISO-8601
```

## Prompt template contract

Templates are YAML files with Jinja2 content:

```yaml
name: impact_results_review       # unique identifier
version: "1.0"                     # pinned for reproducibility
description: "Review impact measurement results"
dimensions:                        # scoring axes
  - estimate_plausibility
  - statistical_rigor
  - methodology_fit

system: |                          # Jinja2 system message
  You are a methodological reviewer...
  {{ knowledge_context }}

user: |                            # Jinja2 user message
  {{ artifact }}
  Model type: {{ model_type }}
```

The engine instructs the LLM to respond in a structured format:

```
DIMENSION: <name>
SCORE: <float 0.0–1.0>
JUSTIFICATION: <text>
...
OVERALL: <float>
```

JSON fallback parsing is also supported.

## Configuration

A single YAML file or dict configures the full stack:

```yaml
backend:
  type: anthropic
  model: claude-sonnet-4-5-20250929
  temperature: 0.0
  max_tokens: 4096

prompt:
  name: impact_results_review
  template_dirs:
    - ./custom_prompts

knowledge:
  type: static
  path: ./knowledge_base
  top_k: 5
```

Environment variable overrides: `REVIEW_BACKEND_TYPE`, `REVIEW_BACKEND_MODEL`,
`REVIEW_PROMPT_NAME`, etc.

## Dependency strategy

| Component | Core dependency | Optional extra |
|-----------|----------------|----------------|
| Engine, models | None | — |
| PromptRegistry, renderer | None | `jinja2` (graceful fallback) |
| StaticKnowledgeBase | None | — |
| AnthropicBackend | No | `anthropic` |
| OpenAIBackend | No | `openai` |
| LiteLLMBackend | No | `litellm` |

The core review subsystem has zero required dependencies beyond the standard
library. Backend SDKs and Jinja2 are optional extras in `pyproject.toml`.

## Future directions

- **MeasureJobResult → ArtifactPayload bridge**: Structured formatter that
  serializes the rich measure output (DataFrames, JSON, config) into reviewable
  text. Format TBD.
- **Vector knowledge base**: Wrap external vector stores (ChromaDB, Pinecone)
  for semantic retrieval of methodology references.
- **Multi-pass review**: Chain multiple prompts (study design → data quality →
  impact results) and aggregate into a composite review.
- **Review caching**: Cache reviews by content hash for reproducibility and
  cost control.
- **Structured output**: Use backend-native structured output (JSON mode) where
  supported, instead of text parsing.
