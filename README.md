# Impact Engine Evaluate

Confidence scoring for the impact engine pipeline.

## Overview

This package implements deterministic confidence scoring based on the causal inference
model type used during measurement. It plugs into the
[impact engine orchestrator](https://github.com/eisenhauerIO/tools-impact-engine-orchestrator)
as the **EVALUATE** component.

## Key Features

- **Model-type confidence scoring** — each causal method maps to a confidence range
- **Deterministic results** — same initiative always produces the same confidence
- **Orchestrator integration** via `Evaluate` pipeline component

## Installation

```bash
pip install -e .
```

For development:

```bash
pip install -e ".[dev]"
```

## Quick Start

### Standalone scorer

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

### As orchestrator component

```python
from impact_engine_evaluate import Evaluate

evaluator = Evaluate()

event = {
    "initiative_id": "init-001",
    "model_type": ModelType.EXPERIMENT,
    "ci_upper": 15.0,
    "effect_estimate": 10.0,
    "ci_lower": 5.0,
    "cost_to_scale": 100.0,
    "sample_size": 50,
}

result = evaluator.execute(event)
# {"initiative_id": "init-001", "confidence": 0.92, "cost": 100.0, ...}
```

## Development

```bash
hatch run test      # Run tests
hatch run lint      # Run linter
hatch run format    # Format code
```
