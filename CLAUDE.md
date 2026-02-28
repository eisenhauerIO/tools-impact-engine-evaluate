# CLAUDE.md

## Project overview

Agentic review and confidence scoring for the impact engine pipeline. Implements
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

- `impact_engine_evaluate/scorer.py` — deterministic scoring for debugging/testing/illustration (pure functions, no orchestrator dependency)
- `impact_engine_evaluate/job_reader.py` — reads job directory artifacts into scorer event dicts
- `impact_engine_evaluate/adapter.py` — orchestrator integration (`Evaluate`), strategy dispatch
- `impact_engine_evaluate/config.py` — review configuration (YAML/dict/env vars)
- `impact_engine_evaluate/review/engine.py` — `ReviewEngine` orchestrates a single LLM review
- `impact_engine_evaluate/review/api.py` — public `review(job_dir)` entry point
- `impact_engine_evaluate/review/manifest.py` — `Manifest` dataclass, load/update helpers
- `impact_engine_evaluate/review/models.py` — data models (`ReviewResult`, `ArtifactPayload`, etc.)
- `impact_engine_evaluate/review/backends/` — LLM backend registry (Anthropic, OpenAI, LiteLLM)
- `impact_engine_evaluate/review/methods/` — method reviewer registry (experiment exemplar)
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
- Scorer is a pure function; adapter handles orchestrator integration
- `_external/` contains reference submodules — do not modify
