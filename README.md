# Impact Engine — Evaluate

[![CI](https://github.com/eisenhauerIO/tools-impact-engine-evaluate/actions/workflows/ci.yaml/badge.svg)](https://github.com/eisenhauerIO/tools-impact-engine-evaluate/actions/workflows/ci.yaml)
[![Docs](https://github.com/eisenhauerIO/tools-impact-engine-evaluate/actions/workflows/docs.yaml/badge.svg?branch=main)](https://github.com/eisenhauerIO/tools-impact-engine-evaluate/actions/workflows/docs.yaml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/eisenhauerIO/tools-impact-engine-evaluate/blob/main/LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Slack](https://img.shields.io/badge/Slack-Join%20Us-4A154B?logo=slack)](https://join.slack.com/t/eisenhauerioworkspace/shared_invite/zt-3lxtc370j-XLdokfTkno54wfhHVxvEfA)

*Confidence scoring and agentic review for causal impact estimates*

How much you trust a causal estimate depends on the method that produced it. A randomized experiment with thousands of observations produces stronger evidence than a time series model on sparse data — but most pipelines treat all estimates equally.

**Impact Engine — Evaluate** scores each estimate for reliability based on its measurement design. A deterministic scorer assigns confidence from methodology-specific ranges. An agentic reviewer sends the actual measurement artifacts to an LLM for structured, per-dimension evaluation. Both paths produce the same output contract, and the resulting confidence score directly penalizes return estimates downstream: low confidence pulls returns toward worst-case scenarios, making the allocator conservative where evidence is weak and aggressive where evidence is strong.

## Installation

```bash
pip install impact-engine-evaluate
```

For LLM-powered review, install with a backend extra:

```bash
pip install "impact-engine-evaluate[anthropic]"   # or [openai], [litellm], [all]
```

## Quick Start

**Deterministic scoring** — no external dependencies, fully reproducible:

```python
from impact_engine_evaluate import score_initiative

result = score_initiative(
    event={
        "initiative_id": "initiative-abc-123",
        "model_type": "experiment",
        "ci_upper": 15.0,
        "effect_estimate": 10.0,
        "ci_lower": 5.0,
        "cost_to_scale": 100.0,
        "sample_size": 500,
    },
    confidence_range=(0.85, 1.0),
)
```

**Agentic review** — LLM-powered evaluation of measurement artifacts:

```python
from impact_engine_evaluate import review

result = review("path/to/job-impact-engine-XXXX/")
```

**Orchestrator integration** — unified adapter for the pipeline:

```python
from impact_engine_evaluate import Evaluate

evaluator = Evaluate(config={"backend": {"type": "anthropic"}})
result = evaluator.execute({"job_dir": "path/to/job-impact-engine-XXXX/"})
```

## Development

```bash
pip install -e ".[dev]"
hatch run test       # run pytest suite
hatch run lint       # check with ruff
hatch run format     # auto-format with ruff
```

Visit our [documentation](https://eisenhauerio.github.io/tools-impact-engine-evaluate/) for details.
