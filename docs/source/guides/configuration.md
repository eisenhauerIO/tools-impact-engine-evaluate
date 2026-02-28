# Configuration

## Overview

Configuration controls the LLM backend used by the review path. The
deterministic scoring path (used for debugging, testing, and illustration)
requires no configuration. Settings can be provided as a YAML file, a Python
dict, or environment variables.

---

## YAML configuration

Create a config file and pass the path to `evaluate_confidence()` or `Evaluate()`:

```python
from impact_engine_evaluate import evaluate_confidence

result = evaluate_confidence("review_config.yaml", "path/to/job-dir/")
```

**Anthropic:**

```yaml
backend:
  model: claude-sonnet-4-6
  temperature: 0.0
  max_tokens: 4096
```

**Ollama (local):**

```yaml
backend:
  model: ollama_chat/llama3.2   # routes to http://localhost:11434
  temperature: 0.0
  max_tokens: 2048
  # api_base: "http://my-ollama-server:11434"  # custom endpoint
```

The `ollama_chat/<model>` prefix is routed to `http://localhost:11434` by
litellm automatically. Any extra keys (e.g. `api_base`) are forwarded as
kwargs to `litellm.completion()`.

---

## Dict configuration

```python
from impact_engine_evaluate import evaluate_confidence

result = evaluate_confidence(
    {"backend": {"model": "gpt-4o", "temperature": 0.0, "max_tokens": 4096}},
    "path/to/job-dir/",
)
```

---

## Environment variables

Environment variables override any values from YAML or dict sources. Pass
`config=None` (the default) to use environment variables alone.

| Variable | Description | Default |
|----------|-------------|---------|
| `REVIEW_BACKEND_MODEL` | Model identifier (any LiteLLM-supported model) | `claude-sonnet-4-5-20250929` |
| `REVIEW_BACKEND_TEMPERATURE` | Sampling temperature | `0.0` |
| `REVIEW_BACKEND_MAX_TOKENS` | Maximum tokens per completion | `4096` |

```bash
export REVIEW_BACKEND_MODEL=gpt-4o
```

---

## Backend parameter reference

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` | str | Model identifier passed to `litellm.completion()`. Any model supported by [LiteLLM](https://docs.litellm.ai/). |
| `temperature` | float | Sampling temperature. `0.0` produces deterministic output. |
| `max_tokens` | int | Maximum tokens in the LLM response. |

Additional keys are forwarded as keyword arguments to `litellm.completion()`
via the `extra` dict.

---

## Dependencies

All review dependencies are core requirements (installed automatically):

| Package | Role |
|---------|------|
| [LiteLLM](https://docs.litellm.ai/) | 100+ LLM providers via unified API |
| [Jinja2](https://jinja.palletsprojects.com/) | Prompt template rendering |
| [PyYAML](https://pyyaml.org/) | YAML config and prompt loading |

```bash
pip install impact-engine-evaluate
```

---

## Precedence

When the same parameter appears in multiple sources, the resolution order is:

1. Environment variables (highest priority)
2. YAML file or dict values
3. Built-in defaults (lowest priority)
