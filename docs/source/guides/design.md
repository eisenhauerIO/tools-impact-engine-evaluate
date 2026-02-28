# Design

## Motivation

Upstream pipeline stages produce structured artifacts — point estimates,
confidence intervals, model diagnostics — that require expert judgement to
interpret. Is the effect estimate plausible? Is the model type appropriate for
the data? Are the diagnostics healthy?

The evaluate package provides a general-purpose agentic review layer that
accepts any job directory conforming to the manifest convention, producing
structured, auditable review judgements. A lightweight deterministic scorer is
included for debugging, testing, and illustration — it assigns a confidence band
based on methodology type alone without examining the content of the results.

```
Artifacts ──► Review strategy   ──► per-dimension scores + justifications
          └──► Score strategy   ──► confidence score (0–1)  [debug/test]
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

### Symmetric Evaluate adapter

The `Evaluate` pipeline component uses symmetric strategy dispatch.  Both
strategies share the **same flow** — only the confidence source differs:

```
manifest → reviewer → scorer_event → [confidence source] → EvaluateResult → write → return
```

1. `evaluate_strategy` (from `manifest.json`) controls *how* to compute
   confidence (score vs review).
2. `model_type` selects the `MethodReviewer` (single source of truth for
   confidence range, prompt templates, knowledge, artifact loading).

Both strategies construct the same `EvaluateResult`, write
`evaluate_result.json` to the job directory, and return the same 8-key
output dict for downstream allocation. The manifest is treated as read-only.

Each strategy also writes its own strategy-specific result file:
- Score: `score_result.json` (`ScoreResult` — confidence + audit fields)
- Review: `review_result.json` (`ReviewResult` — dimensions + justifications)

`MethodReviewer` provides a default `load_artifact()` implementation (reads
all manifest files, extracts `sample_size` from JSON).  Subclasses override
only when they need method-specific loading.

| File | Role |
|------|------|
| `models.py` | `EvaluateResult` dataclass (shared stage output) |
| `score/scorer.py` | `ScoreResult` dataclass + `score_confidence()` — seeded by `initiative_id` |
| `job_reader.py` | `load_scorer_event()` — reads `impact_results.json` and builds a flat scorer event dict |
| `adapter.py` | `Evaluate` PipelineComponent — symmetric dispatch, shared `EvaluateResult` construction and I/O |

### Review subsystem

| File | Role |
|------|------|
| `review/models.py` | Data models: `ReviewResult`, `ReviewDimension`, `ReviewResponse`, `ArtifactPayload`, `PromptSpec` |
| `review/engine.py` | `ReviewEngine` — orchestrates a single review: load prompt, render, call `litellm.completion()` with structured output |
| `review/api.py` | Public `review()` function — end-to-end review of a job directory |
| `review/manifest.py` | `Manifest` dataclass + `load_manifest()` (read-only) |
| `review/methods/base.py` | `MethodReviewer` base (default `load_artifact`) + `MethodReviewerRegistry` |
| `review/methods/experiment/` | Experiment (RCT) reviewer with prompt templates and knowledge |
| `config.py` | `ReviewConfig` — loads from YAML, dict, or env vars |

### LLM backend

The review engine calls `litellm.completion()` directly with a Pydantic
`response_format` (`ReviewResponse`), producing structured JSON that maps
directly to dimension scores and an overall score. LiteLLM wraps 100+
providers, so any model supported by LiteLLM can be used by setting the
`model` field in config.

---

## Registry pattern

Method reviewers use decorator-based registration:

```python
@MethodReviewerRegistry.register("experiment")
class ExperimentReviewer(MethodReviewer): ...
```

This allows extension without modifying package code.

| Dimension | ABC | Registry | What it provides |
|-----------|-----|----------|-----------------|
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

### Score output

```python
@dataclass
class ScoreResult:
    initiative_id: str
    confidence: float              # deterministic draw
    confidence_range: tuple[float, float]  # bounds used
```

### Review input

The `ArtifactPayload` envelope:

```python
@dataclass
class ArtifactPayload:
    initiative_id: str
    artifact_text: str       # serialized upstream results
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

The engine uses LiteLLM's `response_format` with a Pydantic model
(`ReviewResponse`) to get structured JSON output directly from the LLM.
The response maps to dimension scores and an overall score without any
text parsing.

---

## Manifest convention

The `manifest.json` format is a shared convention (not owned by any single
package):

```json
{
  "schema_version": "2.0",
  "model_type": "experiment",
  "evaluate_strategy": "review",
  "created_at": "2025-06-01T12:00:00+00:00",
  "files": {
    "impact_results": {"path": "impact_results.json", "format": "json"}
  }
}
```

The evaluate stage treats the manifest as **read-only**. Output files are
written to the job directory by convention (fixed filenames), not registered
in the manifest:

```
job-impact-engine-XXXX/
├── manifest.json          # read-only (created by the producer)
├── impact_results.json    # upstream output
├── evaluate_result.json   # written by evaluate (both strategies)
├── score_result.json      # written by evaluate (score strategy only)
└── review_result.json     # written by evaluate (review strategy only)
```

---

## Dependency strategy

| Component | Core dependency |
|-----------|----------------|
| Scorer, models | `numpy` |
| LLM completions | `litellm` |
| Template rendering | `jinja2` |
| Config / prompt loading | `pyyaml` |

All review dependencies (`litellm`, `jinja2`, `pyyaml`) are core
requirements in `pyproject.toml`.

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
