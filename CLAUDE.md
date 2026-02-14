# CLAUDE.md

## Project overview

Confidence scoring for the impact engine pipeline. Implements deterministic
confidence scoring by model type, wrapped as a `PipelineComponent` for the orchestrator.

## Development setup

```bash
pip install -e ".[dev]"
```

## Common commands

- `hatch run test` — run pytest suite
- `hatch run lint` — check with ruff
- `hatch run format` — auto-format with ruff

## Architecture

- `impact_engine_evaluate/scorer.py` — core scoring logic (pure functions, no orchestrator dependency)
- `impact_engine_evaluate/adapter.py` — orchestrator integration (`Evaluate`)
- `impact_engine_evaluate/tests/` — unit tests

## Key conventions

- NumPy-style docstrings
- Logging via `logging.getLogger(__name__)` (no print statements)
- Scorer is a pure function; adapter handles orchestrator integration
- `_external/` contains reference submodules — do not modify
