# Usage

## Overview

Impact Engine Evaluate scores causal effect estimates for reliability. It reads
a job directory conforming to the manifest convention and assigns a confidence
score that penalizes downstream return estimates in the allocator.

The package provides two evaluation strategies. **Agentic review** sends the
measurement artifacts to an LLM for structured, per-dimension evaluation.
**Deterministic scoring** is a lightweight alternative for debugging, testing,
and illustration — it draws a reproducible confidence score from a
methodology-specific range without calling an LLM. Both strategies return the
same 8-key output dict, making them interchangeable from the allocator's
perspective.

---

## Deterministic scoring (debug / test)

The deterministic path is useful for debugging, testing, and illustrating the
pipeline without an LLM. It requires no external dependencies and assigns
confidence based on the measurement methodology alone, without examining the
content of the results.

```python
from impact_engine_evaluate import score_initiative

event = {
    "initiative_id": "initiative-abc-123",
    "model_type": "experiment",
    "ci_upper": 15.0,
    "effect_estimate": 10.0,
    "ci_lower": 5.0,
    "cost_to_scale": 100.0,
    "sample_size": 500,
}

result = score_initiative(event, confidence_range=(0.85, 1.0))
```

`score_initiative()` is a pure function. It hashes the `initiative_id` to seed
a random number generator, then draws a confidence value uniformly within the
given range. The same `initiative_id` always produces the same score.

The `confidence_range` is declared by each registered method reviewer. An
experiment (RCT) uses `(0.85, 1.0)` because randomized designs produce the
strongest causal evidence. A less rigorous methodology would declare a lower
range.

The returned dict contains eight keys:

| Key | Description |
|-----|-------------|
| `initiative_id` | Initiative identifier |
| `confidence` | Confidence score (0.0–1.0) |
| `cost` | Cost to scale |
| `return_best` | Upper confidence interval bound |
| `return_median` | Point estimate |
| `return_worst` | Lower confidence interval bound |
| `model_type` | Measurement methodology label |
| `sample_size` | Study sample size |

---

## Agentic review

The agentic path sends the actual measurement artifacts to an LLM and parses a
structured review with per-dimension scores and justifications. It requires an
LLM backend SDK and an API key.

```python
from impact_engine_evaluate import review

result = review("path/to/job-impact-engine-XXXX/")
```

`review()` performs the following steps:

1. **Read manifest.** Loads `manifest.json` from the job directory to determine
   the `model_type` and locate artifact files.
2. **Select method reviewer.** Dispatches on `model_type` to a registered
   `MethodReviewer` (e.g. `"experiment"` selects `ExperimentReviewer`).
3. **Load artifact.** The reviewer reads all files listed in the manifest and
   serializes them into an `ArtifactPayload`.
4. **Load prompt and knowledge.** The reviewer provides its own prompt template
   (YAML with Jinja2) and domain knowledge files (Markdown).
5. **Run review.** The `ReviewEngine` renders the prompt, calls the backend, and
   parses the response into per-dimension scores.
6. **Write results.** Saves `review_result.json` to the job directory.

The returned `ReviewResult` contains per-dimension scores, an overall score (the
mean), and the raw LLM response for audit. See [Configuration](configuration.md)
for backend setup.

---

## Orchestrator integration

Within the full pipeline, the orchestrator calls `Evaluate.execute()` rather
than invoking `score_initiative()` or `review()` directly. The adapter reads the
manifest, dispatches on `evaluate_strategy`, and returns the common 8-key output.

```python
from impact_engine_evaluate import Evaluate

evaluator = Evaluate(config={"backend": {"model": "claude-sonnet-4-5-20250929"}})

result = evaluator.execute({
    "job_dir": "path/to/job-impact-engine-XXXX/",
})
```

The `evaluate_strategy` field in `manifest.json` controls the path:

| Strategy | Behavior |
|----------|----------|
| `"agentic"` | Runs the full LLM review pipeline (default) |
| `"deterministic"` | Lightweight scorer for debugging and testing |

Both strategies produce the same 8-key output dict, so the downstream allocator
does not need to know which path was used. When the agentic path runs, the
`confidence` value is the LLM-derived `overall_score` from the review rather
than a draw from the confidence range.

---

## Pipeline context

The orchestrator pipeline flows through four stages:

```
MEASURE ──► EVALUATE ──► ALLOCATE ──► SCALE
```

The upstream stage writes a job directory with `manifest.json` and
`impact_results.json`. The evaluate stage reads that directory, scores it, and
passes the result to the allocator. Low confidence pulls returns toward
worst-case scenarios, making the allocator conservative where evidence is weak
and aggressive where evidence is strong.
