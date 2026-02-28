# Design

## Motivation

The impact engine pipeline produces causal effect estimates through the measure
stage. These results require expert judgement to interpret. Is the effect
estimate plausible? Is the model type appropriate for the data? Are the
diagnostics healthy?

The deterministic confidence scorer assigns a confidence band based on
methodology type alone. It cannot reason about the content of the results. The
agentic review layer adds LLM-powered evaluation of the actual measurement
artifacts, producing structured, auditable review judgements.

Together, the two layers form a complete evaluate stage:

```
MeasureResult ──► Deterministic Scorer ──► confidence score (0–1)
             └──► Agentic Reviewer    ──► per-dimension scores + justifications
```

---

## Architecture

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

---

## Components

### Unified Evaluate adapter

The `Evaluate` pipeline component uses two-step dispatch: **strategy first,
then model type**.

1. `evaluate_strategy` (from `manifest.json`) controls *how* to evaluate
   (deterministic vs agentic).
2. `model_type` controls *what* to do within that strategy.

Both strategies return the same 8-key output dict for downstream allocation.

`MethodReviewer` subclasses are the single source of truth for each model type.
Each declares `confidence_range` (used by the deterministic path) and bundles
prompt templates, knowledge files, and artifact loading logic (used by the
agentic path).

| File | Role |
|------|------|
| `scorer.py` | Pure function `score_initiative()` — draws a deterministic score seeded by `initiative_id` |
| `job_reader.py` | `load_scorer_event()` — reads `impact_results.json` and builds a flat scorer event dict |
| `adapter.py` | `Evaluate` PipelineComponent — reads manifest, dispatches on strategy, returns common output |

### Review subsystem

| File | Role |
|------|------|
| `review/models.py` | Data models: `ReviewResult`, `ReviewDimension`, `ArtifactPayload`, `PromptSpec` |
| `review/engine.py` | `ReviewEngine` — orchestrates a single review: load prompt, render, call backend, parse |
| `review/api.py` | Public `review()` function — end-to-end review of a job directory |
| `review/manifest.py` | `Manifest` dataclass + `load_manifest()` + `update_manifest()` |
| `review/backends/base.py` | `Backend` ABC + `BackendRegistry` |
| `review/backends/anthropic_backend.py` | Anthropic Messages API backend |
| `review/backends/openai_backend.py` | OpenAI Chat Completions backend |
| `review/backends/litellm_backend.py` | LiteLLM unified backend (100+ providers) |
| `review/methods/base.py` | `MethodReviewer` ABC + `MethodReviewerRegistry` |
| `review/methods/experiment/` | Experiment (RCT) reviewer with prompt templates and knowledge |
| `config.py` | `ReviewConfig` — loads from YAML, dict, or env vars |

---

## Registry pattern

Both pluggable dimensions use the same decorator-based idiom:

```python
@BackendRegistry.register("anthropic")
class AnthropicBackend(Backend): ...

@MethodReviewerRegistry.register("experiment")
class ExperimentReviewer(MethodReviewer): ...
```

This allows extension without modifying package code. Backends auto-register on
import. Missing SDKs are silently skipped.

| Dimension | ABC | Registry | What it provides |
|-----------|-----|----------|-----------------|
| **Backend** | `Backend` | `BackendRegistry` | *How* to call an LLM |
| **Method** | `MethodReviewer` | `MethodReviewerRegistry` | *What* to ask + how to read artifacts + domain knowledge |

---

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
| `cost_to_scale` | float | Optional override for cost from the orchestrator |

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

---

## Prompt template contract

Templates are YAML files with Jinja2 content:

```yaml
name: experiment_review
version: "1.0"
description: "Review experimental impact measurement results"
dimensions:
  - randomization_integrity
  - specification_adequacy
  - statistical_inference
  - threats_to_validity
  - effect_size_plausibility

system: |
  You are a methodological reviewer...
  {{ knowledge_context }}

user: |
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

---

## Manifest convention

The `manifest.json` format is a shared convention between the measure and
evaluate stages:

```json
{
  "schema_version": "2.0",
  "model_type": "experiment",
  "evaluate_strategy": "agentic",
  "created_at": "2025-06-01T12:00:00+00:00",
  "files": {
    "impact_results": {"path": "impact_results.json", "format": "json"}
  }
}
```

After review, the evaluate stage appends its output:

```json
{
  "files": {
    "impact_results": {"path": "impact_results.json", "format": "json"},
    "review_result": {"path": "review_result.json", "format": "json"}
  }
}
```

---

## Dependency strategy

| Component | Core dependency | Optional extra |
|-----------|----------------|----------------|
| Scorer, models | None | — |
| Template rendering | None | `jinja2` (graceful fallback) |
| AnthropicBackend | No | `anthropic` |
| OpenAIBackend | No | `openai` |
| LiteLLMBackend | No | `litellm` |

The core review subsystem has zero required dependencies beyond the standard
library. Backend SDKs and Jinja2 are optional extras.

---

## Method reviewer packages

Each method reviewer is a self-contained subpackage:

```
review/methods/experiment/
├── __init__.py
├── reviewer.py              # @register("experiment") class
├── templates/
│   └── experiment_review.yaml
└── knowledge/
    ├── design.md
    ├── diagnostics.md
    └── pitfalls.md
```

The experiment reviewer evaluates five dimensions:

| Dimension | What it checks |
|-----------|---------------|
| `randomization_integrity` | Covariate balance between treatment and control |
| `specification_adequacy` | OLS formula, covariates, functional form |
| `statistical_inference` | CIs, p-values, F-statistic, multiple testing |
| `threats_to_validity` | Attrition, non-compliance, spillover, SUTVA |
| `effect_size_plausibility` | Whether the treatment effect is realistic |
