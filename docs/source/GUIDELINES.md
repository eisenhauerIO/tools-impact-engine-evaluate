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
| `tutorials/demo_deterministic_scoring.ipynb` | Lightweight scoring path — no API key required. Executable. |
| `tutorials/llm/demo_ollama_review.ipynb` | LLM-powered review via local Ollama. Pre-computed output. Non-executable. |

---

## Sidebar structure

```
Guides     → usage, configuration, design, api_reference
Tutorials  → demo notebooks
```

---

## Tutorials

### Executable vs non-executable

Notebooks are split by directory following the ecosystem-wide convention:

- `tutorials/` — executable notebooks; self-contained, run on every commit via pytest
- `tutorials/llm/` — non-executable notebooks requiring live LLM backends; keep pre-rendered
  outputs (excluded from nbstripout); not in testpaths so CI never attempts to run them

Docs visitors see both in the sidebar — the directory split is invisible to them.
