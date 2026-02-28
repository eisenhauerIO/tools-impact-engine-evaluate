# Implementation Plan: Agentic Review Assistant

Phased roadmap for building out the agentic review assistant. Each phase is a
self-contained deliverable. See DESIGN.md for architectural context.

## Current state

The review subsystem scaffolding is complete and tested (45 tests passing):

- Review engine with `from_config()` and `review()`
- Three LLM backends (Anthropic, OpenAI, LiteLLM) via registry
- Prompt registry with Jinja2 rendering and two generic templates
- Static keyword-based knowledge base
- `ArtifactReview` pipeline component adapter
- Unified configuration with YAML + env var support

## Phase 0 — Design docs + measure-aware prompt

**Status**: in progress

**Goal**: Document the architecture and create the first prompt template that
understands measure output structure.

**Deliverables**:

- [x] `DESIGN.md` — architectural design document
- [x] `PLAN.md` — this implementation roadmap
- [ ] `impact_engine_evaluate/review/prompts/templates/impact_results.yaml` —
  prompt template for reviewing `impact_results.json` output from measure

**Prompt dimensions**:

| Dimension | What it evaluates |
|-----------|-------------------|
| `estimate_plausibility` | Is the effect estimate plausible? Are the confidence intervals reasonable? Is the percent change realistic? |
| `statistical_rigor` | Sample size adequacy, pre/post period balance, model diagnostics (AIC/BIC) |
| `methodology_fit` | Is the chosen model type appropriate for the data characteristics? |

**No source code changes** — the new template is auto-discovered by
`PromptRegistry`.

## Phase 1 — MeasureJobResult formatter

**Goal**: Bridge the structured `MeasureJobResult` from `tools-impact-engine-measure`
into the review system.

**Deliverables**:

- Formatter module that serializes `impact_results.json` + `model_summary` into
  a clean text representation for `ArtifactPayload.artifact_text`
- Decision on whether to extend `ArtifactPayload` with structured fields or
  keep text-only (deferred from Phase 0)
- Unit tests for the formatter

**Key design questions** (to resolve before implementation):

1. Should the formatter live in this package or in an integration layer?
2. How much of `MeasureJobResult` should be serialized? Just `impact_results`,
   or also DataFrame summaries (row counts, column stats)?
3. Should the formatter produce Markdown, YAML, or plain text?

## Phase 2 — Domain knowledge base content

**Goal**: Populate the static knowledge base with causal inference methodology
references so the reviewer has domain context.

**Deliverables**:

- `knowledge/` directory with Markdown files covering:
  - Interrupted time series: assumptions, diagnostics, common pitfalls
  - Synthetic control: donor pool selection, pre-treatment fit
  - Nearest-neighbour matching: balance diagnostics, caliper choices
  - Subclassification: propensity score stratification guidelines
  - Metrics approximation: when it's appropriate, limitations
  - Experiment (RCT): randomization checks, attrition, spillover
- Updated default config pointing to the bundled knowledge directory

## Phase 3 — Multi-prompt review orchestration

**Goal**: Run multiple review prompts in sequence or parallel and aggregate
results into a composite review.

**Deliverables**:

- Review orchestration layer (run N prompts per artifact)
- Aggregation logic: combine per-prompt `ReviewResult` into a composite score
- Prompt chaining: study_design → data_quality → impact_results
- Updated `ArtifactReview` adapter to support multi-prompt mode

## Phase 4 — Review result persistence and reporting

**Goal**: Store review results for audit trails and generate human-readable
reports.

**Deliverables**:

- Result serialization (JSON output alongside measure artifacts)
- Report renderer (Markdown or HTML summary of review findings)
- Integration with the orchestrator's storage layer

## Phase 5 — Advanced backends and retrieval

**Goal**: Production-grade features.

**Deliverables**:

- Vector knowledge base (ChromaDB or similar)
- Review caching by content hash
- Structured output mode (JSON schema enforcement where backends support it)
- Rate limiting and retry logic for backend calls
- Batch review mode for multiple initiatives
