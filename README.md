# Impact Engine — Evaluate

[![CI](https://github.com/eisenhauerIO/tools-impact-engine-evaluate/actions/workflows/ci.yaml/badge.svg)](https://github.com/eisenhauerIO/tools-impact-engine-evaluate/actions/workflows/ci.yaml)
[![Docs](https://github.com/eisenhauerIO/tools-impact-engine-evaluate/actions/workflows/docs.yml/badge.svg?branch=main)](https://github.com/eisenhauerIO/tools-impact-engine-evaluate/actions/workflows/docs.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/eisenhauerIO/tools-impact-engine-evaluate/blob/main/LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Slack](https://img.shields.io/badge/Slack-Join%20Us-4A154B?logo=slack)](https://join.slack.com/t/eisenhauerioworkspace/shared_invite/zt-3lxtc370j-XLdokfTkno54wfhHVxvEfA)

*Confidence scoring for causal impact estimates*

How much you trust a causal estimate depends on the method that produced it. A randomized experiment with thousands of observations produces stronger evidence than a time series model on sparse data — but most pipelines treat all estimates equally.

**Impact Engine — Evaluate** scores each estimate for reliability based on its measurement design. That score directly penalizes return estimates downstream: low confidence pulls returns toward worst-case scenarios, making the allocator conservative where evidence is weak and aggressive where evidence is strong.

## Quick Start

```bash
pip install git+https://github.com/eisenhauerIO/tools-impact-engine-evaluate.git
```

```python
from impact_engine_evaluate import score_initiative, ModelType

result = score_initiative({
    "initiative_id": "test-1",
    "model_type": ModelType.EXPERIMENT,
    "ci_upper": 15.0,
    "effect_estimate": 10.0,
    "ci_lower": 5.0,
    "cost_to_scale": 100.0,
    "sample_size": 50,
})
print(result["confidence"])  # 0.85–1.0 for experiments
```

## Documentation

| Guide | Description |
|-------|-------------|
| [Usage](https://eisenhauerio.github.io/tools-impact-engine-evaluate/usage.html) | Getting started with basic workflow |
| [Configuration](https://eisenhauerio.github.io/tools-impact-engine-evaluate/configuration.html) | All configuration options |
| [Design](https://eisenhauerio.github.io/tools-impact-engine-evaluate/design.html) | System design and architecture |

## Development

```bash
hatch run test        # Run tests
hatch run lint        # Run linter
hatch run format      # Format code
hatch run docs:build  # Build documentation
```
