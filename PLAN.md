# Implementation Plan: Agentic Review Assistant

Phased roadmap for building out the agentic review assistant. Each phase is a
self-contained deliverable. See DESIGN.md for architectural context.

## Current state

The evaluate package is complete through Phase 1.5 (74 tests passing):

- Unified `Evaluate` adapter with deterministic and agentic strategy dispatch
- `MethodReviewer` registry as single source of truth for model types
- Review engine with `from_config()` and `review()`
- Three LLM backends (Anthropic, OpenAI, LiteLLM) via registry
- Experiment (RCT) reviewer with prompt templates and knowledge base
- Unified configuration with YAML + env var support

## Phase 0 — Design docs

**Status**: complete

- [x] `DESIGN.md` — architectural design document
- [x] `PLAN.md` — this implementation roadmap

## Phase 1 — Method reviewer registry + job directory API

**Status**: complete

**Goal**: Introduce method as the primary extensibility dimension with a
registration pattern, and expose a job-directory-based public API. An external
package points at a job output directory and gets a methodology-specific review.
The experiment (RCT) reviewer is the first registered method, serving as the
exemplar for all future methods.

### Design principles

- **Same job directory convention as measure**: the producer writes artifacts +
  `manifest.json` to a job directory; the evaluate package reads from and writes
  to that same directory. Output always lives alongside the input artifacts.
- **Decoupled from upstream packages**: no code dependency on
  `tools-impact-engine-measure` or any other producer. The `manifest.json`
  format is the shared contract.
- **Two extensibility dimensions, same pattern**: backend (how to call an LLM)
  and method (what to ask + how to read artifacts + domain knowledge) both use
  decorator-based registries mirroring `BackendRegistry`.
- **Self-contained method packages**: each method reviewer bundles its own
  prompt template, knowledge base content, and artifact loading logic. External
  packages follow the same structure.

### Public API

```python
import impact_engine_evaluate

result = impact_engine_evaluate.review("job-impact-engine-XXXX/")
```

### Architecture

```
job-impact-engine-XXXX/         # created by any producer
├── manifest.json               # model_type, files mapping
├── impact_results.json         # producer's output
└── ...

impact_engine_evaluate.review("job-impact-engine-XXXX/")
  │
  ├─ 1. Read manifest.json
  │     → model_type: "experiment"
  │     → files: { impact_results: impact_results.json, ... }
  │
  ├─ 2. MethodReviewerRegistry.create("experiment")
  │     → ExperimentReviewer (brings own prompt, knowledge, load logic)
  │
  ├─ 3. reviewer.load_artifact(manifest) → ArtifactPayload
  │     → reads files per manifest, serializes to text
  │
  ├─ 4. Assemble engine (backend from config, prompt + knowledge from reviewer)
  │
  ├─ 5. engine.review(payload) → ReviewResult
  │
  ├─ 6. Write review_result.json to job directory
  │     → update manifest.json with new files entry
  │
  └─ 7. Return ReviewResult
```

### Extensibility dimensions

| Dimension | ABC | Registry | What it provides |
|-----------|-----|----------|-----------------|
| **Backend** | `Backend` | `BackendRegistry` | *How* to call an LLM |
| **Method** | `MethodReviewer` | `MethodReviewerRegistry` | *What* to ask + how to read artifacts + domain knowledge |

### Manifest convention

The `manifest.json` format is a shared convention (not owned by any single
package):

```json
{
  "schema_version": "2.0",
  "model_type": "experiment",
  "created_at": "2025-06-01T12:00:00+00:00",
  "files": {
    "impact_results": {"path": "impact_results.json", "format": "json"},
    "config": {"path": "config.yaml", "format": "yaml"}
  }
}
```

- `model_type` → selects the registered method reviewer (required)
- `files` → maps logical names to `{path, format}` entries (required)
- `schema_version` → versioning (required)

After review, the evaluate package appends its output to the same manifest:

```json
{
  "files": {
    "impact_results": {"path": "impact_results.json", "format": "json"},
    "review_result": {"path": "review_result.json", "format": "json"}
  }
}
```

### MethodReviewer interface

```python
class MethodReviewer(ABC):
    name: str = ""
    prompt_name: str = ""
    description: str = ""
    confidence_range: tuple[float, float] = (0.0, 0.0)  # added in Phase 1.5

    @abstractmethod
    def load_artifact(self, manifest: Manifest, job_dir: Path) -> ArtifactPayload:
        """Read artifact files per manifest, serialize to text."""
        ...

    def prompt_template_dir(self) -> Path | None:
        """Directory containing this reviewer's .yaml prompt templates."""
        return None

    def knowledge_content_dir(self) -> Path | None:
        """Directory containing this reviewer's .md knowledge files."""
        return None
```

### Self-contained method packages

Each method reviewer is a subpackage that bundles everything it needs:

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

External packages follow the same structure. Resource location via
`Path(__file__).parent`.

### Experiment exemplar — review dimensions

| Dimension | What it checks |
|-----------|---------------|
| `randomization_integrity` | Covariate balance between treatment/control |
| `specification_adequacy` | OLS formula, covariates, functional form |
| `statistical_inference` | CIs, p-values, F-statistic, multiple testing |
| `threats_to_validity` | Attrition, non-compliance, spillover, SUTVA |
| `effect_size_plausibility` | Whether the treatment effect is realistic |

### Experiment exemplar — knowledge base

| File | Content |
|------|---------|
| `design.md` | RCT fundamentals — SUTVA, exchangeability, randomization, ITT, power |
| `diagnostics.md` | OLS output interpretation — R-squared, F-statistic, robust SEs, residuals |
| `pitfalls.md` | Common threats — attrition, non-compliance, spillover, multiple testing |

### Deliverables

| File | Role |
|------|------|
| `review/manifest.py` | `Manifest` dataclass + `load_manifest()` + `update_manifest()` |
| `review/methods/base.py` | `MethodReviewer` ABC + `MethodReviewerRegistry` |
| `review/methods/__init__.py` | Package init, imports experiment to trigger registration |
| `review/methods/experiment/reviewer.py` | `ExperimentReviewer` with `@register("experiment")` |
| `review/methods/experiment/templates/experiment_review.yaml` | RCT-specific prompt template |
| `review/methods/experiment/knowledge/*.md` | Domain knowledge (3 files) |
| `review/api.py` | Top-level `review(job_dir)` function |
| `__init__.py` | Expose `review` in public API |
| `tests/test_manifest.py` | Manifest loading, validation, update |
| `tests/test_method_registry.py` | Registry mechanics |
| `tests/test_experiment_review.py` | Experiment reviewer, prompt, knowledge |
| `tests/test_review_api.py` | End-to-end API test |

## Phase 1.5 — Unified strategy dispatch

**Status**: complete

**Goal**: Merge the deterministic scorer and agentic review into a single
`Evaluate.execute()` that reads a job directory, selects a strategy from the
manifest, and returns a common output contract.

### Key changes

- **`Manifest.evaluate_strategy`**: new field (default `"agentic"`) that
  controls which evaluation path to use.
- **`MethodReviewer.confidence_range`**: each reviewer declares its
  deterministic confidence bounds. The `ModelType` enum and `CONFIDENCE_MAP`
  dict are removed — the registry is the single source of truth.
- **`score_initiative(event, confidence_range)`**: takes an explicit range
  parameter instead of looking up `model_type` in `CONFIDENCE_MAP`.
- **`load_scorer_event(manifest, job_dir)`**: shared reader that builds a
  flat scorer event dict from `impact_results.json`.
- **`Evaluate` adapter**: reads manifest, dispatches on `evaluate_strategy`,
  both paths return the same 8-key dict.

### Confidence semantic

- **Deterministic path**: confidence is drawn from the reviewer's
  `confidence_range`, seeded by `initiative_id` (reproducible).
- **Agentic path**: confidence is the LLM-derived `overall_score` from
  `ReviewResult` (non-deterministic, content-aware).

## Phase 2 — Additional method reviewers

**Goal**: Register method reviewers for the remaining implemented model types,
each with methodology-specific prompt templates and knowledge base content.

**Deliverables**:

- Method reviewer packages for:
  - Interrupted time series (SARIMAX diagnostics, stationarity, autocorrelation)
  - Synthetic control (pre-treatment fit, donor pool selection, placebo tests)
  - Nearest-neighbour matching (balance diagnostics, caliper choices)
  - Subclassification (propensity score stratification, within-stratum effects)
  - Metrics approximation (appropriateness, response function validation)
- Each follows the self-contained package pattern established in Phase 1

## Phase 3 — Multi-prompt review orchestration

**Goal**: Run multiple review prompts in sequence or parallel and aggregate
results into a composite review.

**Deliverables**:

- Review orchestration layer (run N prompts per artifact)
- Aggregation logic: combine per-prompt `ReviewResult` into a composite score
- Prompt chaining: study_design → data_quality → method-specific
- Updated `review()` API to support multi-prompt mode

## Phase 4 — Advanced backends and retrieval

**Goal**: Production-grade features.

**Deliverables**:

- Vector knowledge base (ChromaDB or similar)
- Review caching by content hash
- Structured output mode (JSON schema enforcement where backends support it)
- Rate limiting and retry logic for backend calls
- Batch review mode for multiple job directories
