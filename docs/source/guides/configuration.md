# Configuration

## Overview

Configuration controls the LLM backend used by the agentic review path. The
deterministic scoring path requires no configuration. Settings can be provided
as a YAML file, a Python dict, or environment variables.

---

## YAML configuration

```yaml
backend:
  type: anthropic
  model: claude-sonnet-4-5-20250929
  temperature: 0.0
  max_tokens: 4096
```

Pass the file path to `review()` or `Evaluate()`:

```python
from impact_engine_evaluate import review

result = review("path/to/job-dir/", config="review_config.yaml")
```

---

## Dict configuration

```python
from impact_engine_evaluate import Evaluate

evaluator = Evaluate(config={
    "backend": {
        "type": "openai",
        "model": "gpt-4o",
        "temperature": 0.0,
        "max_tokens": 4096,
    }
})
```

---

## Environment variables

Environment variables override any values from YAML or dict sources. Pass
`config=None` (the default) to use environment variables alone.

| Variable | Description | Default |
|----------|-------------|---------|
| `REVIEW_BACKEND_TYPE` | Registered backend name | `anthropic` |
| `REVIEW_BACKEND_MODEL` | Model identifier | `claude-sonnet-4-5-20250929` |
| `REVIEW_BACKEND_TEMPERATURE` | Sampling temperature | `0.0` |
| `REVIEW_BACKEND_MAX_TOKENS` | Maximum tokens per completion | `4096` |

```bash
export REVIEW_BACKEND_TYPE=openai
export REVIEW_BACKEND_MODEL=gpt-4o
```

---

## Backend parameter reference

| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | str | Registered backend name. One of `"anthropic"`, `"openai"`, or `"litellm"`. |
| `model` | str | Model identifier passed to the backend SDK. |
| `temperature` | float | Sampling temperature. `0.0` produces deterministic output. |
| `max_tokens` | int | Maximum tokens in the LLM response. |

Additional backend-specific keys are forwarded as keyword arguments to the backend
constructor via the `extra` dict.

---

## Optional dependencies

The core package has zero required dependencies. Backend SDKs and the template
renderer are optional extras.

| Extra | Installs | Use case |
|-------|----------|----------|
| `review` | [Jinja2](https://jinja.palletsprojects.com/) | Prompt template rendering |
| `anthropic` | Jinja2 + [anthropic](https://docs.anthropic.com/en/docs/sdks) | Anthropic Messages API |
| `openai` | Jinja2 + [openai](https://platform.openai.com/docs/) | OpenAI Chat Completions |
| `litellm` | Jinja2 + [litellm](https://docs.litellm.ai/) | 100+ LLM providers via unified API |
| `all` | All of the above | Full backend support |

```bash
pip install "impact-engine-evaluate[anthropic]"
```

---

## Precedence

When the same parameter appears in multiple sources, the resolution order is:

1. Environment variables (highest priority)
2. YAML file or dict values
3. Built-in defaults (lowest priority)
