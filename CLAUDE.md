# CLAUDE.md

## Project overview

Artifact review and confidence scoring for the impact engine pipeline. Implements
LLM-powered methodology review and a lightweight deterministic scorer (for
debugging, testing, and illustration), wrapped as a `PipelineComponent` for
the orchestrator.

## Development setup

```bash
pip install -e ".[dev]"
```

## Common commands

- `hatch run test` — run pytest suite
- `hatch run lint` — check with ruff
- `hatch run format` — auto-format with ruff

## Architecture

- `impact_engine_evaluate/models.py` — `EvaluateResult` dataclass (shared stage output)
- `impact_engine_evaluate/score/scorer.py` — `ScoreResult` dataclass + `score_confidence()` (pure, no orchestrator dependency)
- `impact_engine_evaluate/job_reader.py` — reads job directory artifacts into scorer event dicts
- `impact_engine_evaluate/adapter.py` — orchestrator integration (`Evaluate`), symmetric strategy dispatch + shared I/O
- `impact_engine_evaluate/config.py` — review configuration (YAML/dict/env vars)
- `impact_engine_evaluate/review/engine.py` — `ReviewEngine` calls `litellm.completion()` with structured output
- `impact_engine_evaluate/review/api.py` — public `review(job_dir)` entry point
- `impact_engine_evaluate/review/manifest.py` — `Manifest` dataclass, `load_manifest()` (read-only)
- `impact_engine_evaluate/review/models.py` — data models (`ReviewResult`, `ReviewResponse`, `ArtifactPayload`, etc.)
- `impact_engine_evaluate/review/methods/` — method reviewer registry; base class provides default `load_artifact`
- `tests/` — unit tests

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
- Symmetric strategy dispatch: both paths share setup, output construction, and job dir I/O
- Strategy names: `"score"` (deterministic) and `"review"` (LLM-powered)
- `_external/` contains reference submodules — do not modify
