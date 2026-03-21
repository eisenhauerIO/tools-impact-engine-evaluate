# Documentation Guidelines — Evaluate

Ecosystem-wide conventions: see `docs/GUIDELINES.md` at the workspace root.
This file documents conventions specific to the evaluate component.

---

## Page map

| Page | Purpose |
|------|---------|
| `README.md` | Package positioning and quick start. Also the docs landing page. |
| `guides/usage.md` | General workflow for both evaluation paths (deterministic and LLM-powered). |
| `guides/configuration.md` | Parameter reference for review backend configuration (model, temperature, etc.). |
| `guides/design.md` | Architecture, strategy dispatch, registry pattern, data flow. |
| `guides/api_reference.rst` | Auto-generated from source. Do not hand-edit. |
| `tutorials/demo_deterministic_scoring.ipynb` | Lightweight scoring path — no API key required. |
| `tutorials/demo_agentic_review.ipynb` | LLM-powered review via Anthropic API. Pre-computed output. |
| `tutorials/demo_ollama_review.ipynb` | LLM-powered review via local Ollama. Pre-computed output. |

---

## Sidebar structure

```
Guides     → usage, configuration, design, api_reference
Tutorials  → demo notebooks
```

---

## Tutorials

### Executable vs non-executable

- `demo_deterministic_scoring.ipynb` — no external dependencies, executes on every Sphinx build.
- `demo_agentic_review.ipynb` and `demo_ollama_review.ipynb` — require live LLM backends.
  These include pre-computed output and are marked non-executable via notebook metadata
  (`nbsphinx_execute = "never"` in the notebook's metadata block). They are excluded from
  the Sphinx build via `conf.py` `exclude_patterns` to avoid execution errors in CI.

This split ensures CI passes without API keys while still shipping runnable notebooks
for users who have the backends configured.
