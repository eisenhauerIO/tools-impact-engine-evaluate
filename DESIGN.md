# Design: Agentic Review Assistant for Impact Measurement Results

## Motivation

The impact engine pipeline produces causal effect estimates through
`tools-impact-engine-measure`. These results — point estimates, confidence
intervals, model diagnostics — require expert judgement to interpret. Is the
effect estimate plausible? Is the model type appropriate for the data? Are the
diagnostics healthy?

The agentic review layer adds LLM-powered evaluation of the actual measurement
artifacts, producing structured, auditable review judgements. A lightweight
deterministic scorer (`scorer.py`) is included for debugging, testing, and
illustration — it assigns a confidence band based on methodology type alone
without examining the content of the results.

```
MeasureResult ──► Agentic Reviewer      ──► per-dimension scores + justifications
             └──► Deterministic Scorer  ──► confidence score (0–1)  [debug/test]
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

### Unified Evaluate adapter

The `Evaluate` pipeline component uses two-step dispatch: **strategy first,
then model type**.

1. `evaluate_strategy` (from `manifest.json`) → *how* to evaluate
   (deterministic vs agentic)
2. `model_type` → *what* to do within that strategy

Both strategies return the same 8-key output dict for downstream ALLOCATE.

`MethodReviewer` subclasses are the single source of truth for each model
type. Each declares `confidence_range` (used by the deterministic path) and
bundles prompt templates + knowledge + artifact loading (used by the agentic
path). The `ModelType` enum and `CONFIDENCE_MAP` dict have been removed —
the registry keys (strings) are the canonical model type identifiers.

| File | Role |
|------|------|
| `scorer.py` | Pure function `score_initiative(event, confidence_range)` — deterministic score for debugging, testing, and illustration; seeded by `initiative_id` |
| `job_reader.py` | `load_scorer_event(manifest, job_dir)` — reads `impact_results.json` and builds a flat scorer event dict |
| `adapter.py` | `Evaluate` PipelineComponent — reads manifest, dispatches on `evaluate_strategy`, returns common output |

### Review subsystem

| File | Role |
|------|------|
| `review/models.py` | Data models: `ReviewResult`, `ReviewDimension`, `ArtifactPayload`, `PromptSpec` |
| `review/engine.py` | `ReviewEngine` — orchestrates a single review: load prompt, render template, call backend, parse response |
| `review/api.py` | Public `review(job_dir)` function — end-to-end review of a job directory |
| `review/manifest.py` | `Manifest` dataclass + `load_manifest()` + `update_manifest()` |
| `review/backends/base.py` | `Backend` ABC + `BackendRegistry` (decorator-based registration) |
| `review/backends/anthropic_backend.py` | Anthropic Messages API backend |
| `review/backends/openai_backend.py` | OpenAI Chat Completions backend |
| `review/backends/litellm_backend.py` | LiteLLM unified backend (100+ providers) |
| `review/methods/base.py` | `MethodReviewer` ABC + `MethodReviewerRegistry` |
| `review/methods/experiment/` | Experiment (RCT) reviewer with prompt templates and knowledge |
| `config.py` | `ReviewConfig` — loads from YAML/dict/env vars |

### Registry pattern

Both pluggable dimensions use the same idiom:

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

The orchestrator passes a job directory reference to `Evaluate.execute()`:

| Field | Type | Description |
|-------|------|-------------|
| `job_dir` | str | Path to the job directory containing `manifest.json` |
| `cost_to_scale` | float | (optional) Override for cost from the orchestrator |

The manifest's `evaluate_strategy` field (default: `"agentic"`) controls
the evaluation approach. Both deterministic and agentic paths read scenario
returns from `impact_results.json` via `load_scorer_event()`.

The `evaluate_strategy` field in `manifest.json`:
- `"deterministic"` — lightweight scorer for debugging and testing
- `"agentic"` — runs the full LLM review pipeline (default)

### Scorer event contract

`load_scorer_event()` reads flat top-level keys from `impact_results.json`:

```json
{
  "ci_upper": 15.0,
  "effect_estimate": 10.0,
  "ci_lower": 5.0,
  "cost_to_scale": 100.0,
  "sample_size": 50
}
```

The agentic review path reads the same file as raw text via
`reviewer.load_artifact()`, so the full measure output (nested model params,
diagnostics, etc.) is preserved for the LLM reviewer even though the scorer
only uses the flat keys above.

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

A single YAML file or dict configures the backend:

```yaml
backend:
  type: anthropic
  model: claude-sonnet-4-5-20250929
  temperature: 0.0
  max_tokens: 4096
```

Environment variable overrides: `REVIEW_BACKEND_TYPE`, `REVIEW_BACKEND_MODEL`,
`REVIEW_BACKEND_TEMPERATURE`, `REVIEW_BACKEND_MAX_TOKENS`.

## Dependency strategy

| Component | Core dependency | Optional extra |
|-----------|----------------|----------------|
| Engine, models | None | — |
| Template rendering | None | `jinja2` (graceful fallback) |
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
