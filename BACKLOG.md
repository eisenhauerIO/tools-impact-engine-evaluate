# Backlog: impact-engine-evaluate

Prioritized work queue for package improvements. See DESIGN.md for
architectural context.

## Current state

The package provides two evaluation strategies (`score` and `review`),
a registry-based method reviewer system, and a litellm-backed LLM
pipeline. CI (ruff linting) and documentation (Sphinx + GitHub Pages)
are operational.

## Phase 0 — Interface improvements

**Status**: planned

- Accept `Path` objects in `evaluate_confidence()` — currently requires
  `str(job_dir)`. Detect `pathlib.Path` and convert internally for a
  cleaner caller interface.
