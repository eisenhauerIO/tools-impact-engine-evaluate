# Documentation Guidelines

## Docs Structure

Each page serves a distinct purpose. Method-specific details belong in tutorials, not in guides.

| Page | Purpose |
|------|---------|
| `README.md` | Package positioning and quick start. Also the docs landing page via `index.md`. |
| `design.md` | Architecture, extensibility, data flow, registry patterns. |
| `usage.md` | General workflow for both evaluation paths. Links to tutorials for examples. |
| `configuration.md` | Parameter reference tables for review backend configuration. |
| `api_reference.rst` | Auto-generated from source. Do not hand-edit. |
| Tutorials | Runnable walkthroughs of specific features (scoring, review). |

---

## Writing Style

All documentation pages follow the tone set by `design.md`.

- Narrative prose with complete sentences. No sentence fragments or bullet-only pages.
- Succinct — every sentence earns its place. No filler, no restating the obvious.
- Structured — use headings, horizontal rules, tables, and code blocks to make pages scannable.
- Symmetric — when multiple items follow a pattern (backends, methods, strategies), present them in parallel structure (same heading depth, same format, same level of detail).

---

## Text Formatting Conventions

| Category | Format | Examples |
|----------|--------|----------|
| Product name | title case first mention, "the engine" after | "Impact Engine evaluates...", then "the engine scores..." |
| External libraries (first mention) | linked | `[statsmodels](https://www.statsmodels.org/)` |
| External libraries (subsequent) | plain text, lowercase | statsmodels |
| Library classes/functions | backticks, linked when useful | `` [`ols()`](url) `` |
| Functions/methods | backticks with parens | `score_initiative()`, `review()` |
| Variables/column names | backticks | `initiative_id`, `confidence` |
| Config keys/values | backticks | `backend`, `temperature` |
| File names (no link) | backticks | `manifest.json`, `config.yaml` |
| Adapter/class names | backticks | `Evaluate`, `ReviewEngine` |
| Classes/interfaces (with source) | markdown link | [ReviewEngine](path), [MethodReviewer](path) |
| Files (with source) | markdown link | [scorer.py](path) |
| Statistical acronyms | plain text, all caps | ATT, ATE, OLS, RCT |
| Design patterns | bold | **adapter pattern**, **registry pattern** |
| Key architectural concepts | bold | **strategy dispatch**, **method reviewer** |
| Tools/services | plain text | GitHub Actions, S3 |
| File formats | plain text | YAML, JSON |

1. Use backticks for any code identifier that appears inline in prose.
2. Use markdown links when referencing source files, classes, or interfaces that readers might want to navigate to.
3. Use bold sparingly for design patterns and key concepts being introduced or emphasized.
4. Keep tool and format names in plain text for readability.
5. Write in narrative prose with complete sentences. Avoid semicolons and colons.
6. Always title-case "Impact Engine" on first mention per page. Use "the engine" as shorthand after.
7. Link external library names on first mention per page. Use plain text after.

---

## Tutorials

### Structure

Every tutorial notebook follows this general sequence:

1. **Title and Overview** — what the tutorial demonstrates and why it matters.
2. **Setup** — imports and any prerequisite configuration.
3. **Worked Example** — step-by-step walkthrough with code and output.
4. **Inspection** — examine the results in detail.
5. **Summary** — recap of key takeaways.

### Executable vs non-executable

Tutorials that require no external services (deterministic scoring) are executable (`nbsphinx_execute = "always"`). Tutorials that require LLM API keys (agentic review) include pre-computed output and are marked non-executable via notebook metadata.

### Sphinx integration

- Notebooks must be registered in `index.md` under the Tutorials toctree.
- Shared helper functions live in `tutorials/notebook_support.py`.
