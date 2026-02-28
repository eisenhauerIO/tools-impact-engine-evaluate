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

## Verification

After implementation, run in order:

1. `hatch run test` — all tests pass
2. `hatch run lint` — no ruff violations
3. Launch **code-reviewer** subagent (`.claude/subagents/code-reviewer.md`) on the diff
4. Launch **design-reviewer** subagent (`.claude/subagents/design-reviewer.md`) on the diff
5. Push to branch and confirm GitHub Actions CI passes

A plan is not complete until all steps are green.

## Key conventions

- NumPy-style docstrings
- Logging via `logging.getLogger(__name__)` (no print statements)
- Scorer is a pure function; adapter handles orchestrator integration
- `_external/` contains reference submodules — do not modify
