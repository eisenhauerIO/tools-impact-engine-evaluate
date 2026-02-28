# Design: Agentic Review Assistant

## Motivation

Upstream pipeline stages produce structured artifacts — point estimates,
confidence intervals, model diagnostics — that require expert judgement to
interpret. Is the effect estimate plausible? Is the model type appropriate for
the data? Are the diagnostics healthy?

The evaluate package provides a general-purpose agentic review layer that
accepts any job directory conforming to the manifest convention. It loads the
manifest, selects the appropriate method reviewer, runs the LLM review, and
returns a structured, auditable confidence judgement.

## Architecture overview

![ReviewEngine architecture](img/review-engine.svg)

## Components

### Evaluate adapter

`Evaluate` is the pipeline component that drives the review. It reads the
manifest, selects a `MethodReviewer` by `model_type`, loads the artifact,
and delegates to `ReviewEngine`. `model_type` (from `manifest.json`) is the single lookup key: it selects the
method reviewer that bundles the confidence range, prompt templates, knowledge
base, and artifact loading logic for that methodology.

The result is written as `evaluate_result.json` and `review_result.json` to
the job directory. The manifest is treated as read-only.

`MethodReviewer` provides a default `load_artifact()` implementation that
reads all manifest files into an `ArtifactPayload`. Subclasses override only
when they need method-specific loading.

| File | Role |
|------|------|
| `models.py` | `EvaluateResult` dataclass (stage output) |
| `job_reader.py` | `load_scorer_event(manifest, job_dir)` — reads `impact_results.json` into an event dict |
| `adapter.py` | `Evaluate` PipelineComponent — selects reviewer, runs review, writes output |

### Review subsystem

| File | Role |
|------|------|
| `review/models.py` | Data models: `ReviewResult`, `ReviewDimension`, `ReviewResponse`, `ArtifactPayload`, `PromptSpec` |
| `review/engine.py` | `ReviewEngine` — orchestrates a single review: load prompt, render template, call `litellm.completion()` with structured output |
| `review/api.py` | Public `review(job_dir)` function — end-to-end review of a job directory |
| `review/manifest.py` | `Manifest` dataclass + `load_manifest()` (read-only) |
| `review/methods/base.py` | `MethodReviewer` base (default `load_artifact`) + `MethodReviewerRegistry` |
| `review/methods/experiment/` | Experiment (RCT) reviewer with prompt templates and knowledge |
| `config.py` | `ReviewConfig` — loads from YAML/dict/env vars |

### LLM backend

The review engine calls `litellm.completion()` directly with a Pydantic
`response_format` (`ReviewResponse`), producing structured JSON that maps
directly to dimension scores and an overall score. LiteLLM wraps 100+
providers, so any model supported by LiteLLM can be used by setting the
`model` field in config.

### Registry pattern

`MethodReviewerRegistry` uses a class decorator for registration.  Each
method reviewer subclass is tagged with its manifest `model_type` key:

```python
@MethodReviewerRegistry.register("experiment")
class ExperimentReviewer(MethodReviewer):
    ...
```

`MethodReviewerRegistry.create(model_type)` instantiates the matching
class, raising `KeyError` for unknown types.  Built-in reviewers are
auto-registered when `impact_engine_evaluate.review.methods` is imported,
so no explicit registration call is required at the call site.

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

`Evaluate.execute()` reads the manifest, selects the method reviewer by
`model_type`, loads the artifact, and runs the `ReviewEngine`. The result is an
`EvaluateResult` with `confidence = overall_score`, written to
`evaluate_result.json`.

### Impact results contract

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

The review path reads the same file as raw text via
`reviewer.load_artifact()`, so the full measure output (nested model params,
diagnostics, etc.) is preserved for the LLM reviewer even though the scorer
only uses the flat keys above.

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
    overall_score: float     # LLM-reported aggregate score
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

The engine uses LiteLLM's `response_format` with a Pydantic model
(`ReviewResponse`) to get structured JSON output directly from the LLM.
The response maps to dimension scores and an overall score without any
text parsing.

## Configuration

A single YAML file or dict configures the backend:

```yaml
backend:
  model: claude-sonnet-4-6
  temperature: 0.0
  max_tokens: 4096
```

Environment variable overrides: `REVIEW_BACKEND_MODEL`,
`REVIEW_BACKEND_TEMPERATURE`, `REVIEW_BACKEND_MAX_TOKENS`.

## Dependency strategy

| Component | Core dependency |
|-----------|----------------|
| LLM completions | `litellm` |
| Template rendering | `jinja2` |
| Config / prompt loading | `pyyaml` |

All review dependencies (`litellm`, `jinja2`, `pyyaml`) are core
requirements in `pyproject.toml`.

## Future directions

- **Rich artifact bridge**: Structured formatter that serializes complex
  upstream output (DataFrames, JSON, config) into reviewable text. Format TBD.
- **Vector knowledge base**: Wrap external vector stores (ChromaDB, Pinecone)
  for semantic retrieval of methodology references.
- **Multi-pass review**: Chain multiple prompts (study design → data quality →
  impact results) and aggregate into a composite review.
- **Review caching**: Cache reviews by content hash for reproducibility and
  cost control.
