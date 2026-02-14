# Architecture Proposal: Multi-Backend Agentic Artifact Review

## Motivation

The current package provides **deterministic confidence scoring** based on model
type. We want to add an **agentic review layer** that uses LLMs to evaluate
artifacts (e.g. study designs, data quality, methodology descriptions) and
produce structured review judgements. This requires pluggable LLM backends,
managed prompt templates, and domain-specific knowledge bases.

## Design Principles

1. **Preserve existing architecture** — scorer.py and adapter.py stay untouched.
2. **Pure logic separate from integration** — review logic is backend-agnostic;
   adapters handle orchestrator wiring.
3. **Registry pattern for extensibility** — backends, knowledge bases, and prompt
   sets are registered, not hard-coded.
4. **Determinism where possible** — seeded sampling, pinned prompt versions,
   cached reviews for reproducibility.
5. **Minimal dependencies in core** — backend-specific SDKs are optional extras.

---

## Proposed Package Layout

```
impact_engine_evaluate/
├── __init__.py                     # existing public API + new exports
├── scorer.py                       # existing (unchanged)
├── adapter.py                      # existing (unchanged)
│
├── review/                         # NEW — agentic review subpackage
│   ├── __init__.py                 # public API: ReviewEngine, ReviewResult
│   │
│   ├── engine.py                   # ReviewEngine — orchestrates a review run
│   │                               #   accepts: artifact, backend, prompt, kb
│   │                               #   returns: ReviewResult
│   │
│   ├── models.py                   # data models (dataclasses / pydantic-free)
│   │                               #   - ReviewResult
│   │                               #   - ReviewDimension (sub-score per rubric axis)
│   │                               #   - ArtifactPayload (typed input envelope)
│   │                               #   - PromptSpec (template + version metadata)
│   │
│   ├── backends/                   # LLM backend abstraction
│   │   ├── __init__.py             # BackendRegistry + base class
│   │   ├── base.py                 # abstract Backend protocol
│   │   │                           #   - complete(messages, config) -> str
│   │   │                           #   - supports structured output flag
│   │   ├── anthropic.py            # Anthropic (Claude) backend
│   │   ├── openai.py               # OpenAI / Azure OpenAI backend
│   │   └── litellm.py             # LiteLLM catch-all backend (100+ providers)
│   │
│   ├── prompts/                    # prompt management
│   │   ├── __init__.py             # PromptRegistry + loader
│   │   ├── registry.py             # discover / register / version prompts
│   │   ├── templates/              # YAML/Jinja2 prompt template files
│   │   │   ├── study_design.yaml   # example: study design review rubric
│   │   │   └── data_quality.yaml   # example: data quality review rubric
│   │   └── renderer.py            # template rendering (Jinja2-based)
│   │
│   ├── knowledge/                  # knowledge base abstraction
│   │   ├── __init__.py             # KnowledgeRegistry + base class
│   │   ├── base.py                 # abstract KnowledgeBase protocol
│   │   │                           #   - retrieve(query, top_k) -> list[Chunk]
│   │   ├── static.py              # static KB: loads markdown/text files
│   │   └── vector.py              # vector KB: wraps external vector stores
│   │
│   └── review_adapter.py          # PipelineComponent wrapper: ArtifactReview
│                                   #   wires ReviewEngine into orchestrator
│
├── config.py                       # NEW — unified config loader
│                                   #   reads YAML / env vars / dict
│                                   #   provides typed ReviewConfig
│
└── tests/
    ├── ... (existing tests unchanged)
    ├── test_engine.py              # ReviewEngine unit tests
    ├── test_backends.py            # backend contract tests (mock-based)
    ├── test_prompts.py             # prompt loading / rendering tests
    ├── test_knowledge.py           # knowledge base tests
    └── test_review_adapter.py      # integration test with orchestrator
```

---

## Core Abstractions

### 1. `Backend` (Protocol)

```python
class Backend(Protocol):
    """LLM backend that can produce completions."""

    name: str

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        response_format: dict | None = None,
    ) -> str:
        """Return the assistant's text response."""
        ...
```

Each concrete backend (`AnthropicBackend`, `OpenAIBackend`, `LiteLLMBackend`)
implements this protocol. Backend-specific SDKs are **optional extras** in
`pyproject.toml`:

```toml
[project.optional-dependencies]
anthropic = ["anthropic>=0.40"]
openai    = ["openai>=1.50"]
litellm   = ["litellm>=1.50"]
all       = ["anthropic>=0.40", "openai>=1.50", "litellm>=1.50"]
```

### 2. `KnowledgeBase` (Protocol)

```python
class KnowledgeBase(Protocol):
    """Retrieval interface for domain knowledge."""

    name: str

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 5,
    ) -> list[Chunk]:
        """Return relevant chunks for the query."""
        ...

@dataclass
class Chunk:
    content: str
    source: str
    score: float | None = None
```

- **`StaticKnowledgeBase`** — loads `.md` / `.txt` files from a directory,
  simple keyword matching. Zero external dependencies.
- **`VectorKnowledgeBase`** — wraps a vector store client (e.g. ChromaDB,
  Pinecone). Optional dependency.

### 3. `PromptSpec` + `PromptRegistry`

Prompts are YAML files with Jinja2 templates:

```yaml
# prompts/templates/study_design.yaml
name: study_design_review
version: "1.0"
description: "Review study design quality"
dimensions:
  - internal_validity
  - external_validity
  - statistical_power

system: |
  You are a methodological reviewer for causal inference studies.
  Score each dimension from 0.0 to 1.0 with justification.
  {% if knowledge_context %}
  Use the following reference material:
  {{ knowledge_context }}
  {% endif %}

user: |
  Review the following artifact:
  ---
  {{ artifact }}
  ---
  Model type: {{ model_type }}
  Sample size: {{ sample_size }}
```

`PromptRegistry` discovers templates from:
1. Built-in `templates/` directory (shipped with package)
2. User-supplied directory (via config)

### 4. `ReviewEngine`

The central orchestrator for a single review:

```python
class ReviewEngine:
    """Execute an artifact review using configured backend, prompt, and KB."""

    def __init__(
        self,
        backend: Backend,
        prompt_registry: PromptRegistry,
        knowledge_base: KnowledgeBase | None = None,
    ) -> None: ...

    def review(
        self,
        artifact: ArtifactPayload,
        prompt_name: str = "study_design_review",
    ) -> ReviewResult: ...
```

Flow:
1. Load `PromptSpec` from registry by name.
2. If a knowledge base is configured, retrieve context for the artifact.
3. Render the prompt template with artifact data + knowledge context.
4. Call `backend.complete()` with rendered messages.
5. Parse structured response into `ReviewResult`.

### 5. `ReviewResult`

```python
@dataclass
class ReviewResult:
    initiative_id: str
    prompt_name: str
    prompt_version: str
    backend_name: str
    model: str
    dimensions: list[ReviewDimension]
    overall_score: float          # aggregated from dimensions
    raw_response: str             # full LLM output for audit
    timestamp: str                # ISO-8601

@dataclass
class ReviewDimension:
    name: str
    score: float                  # 0.0 – 1.0
    justification: str
```

### 6. `ArtifactReview` (PipelineComponent)

Thin adapter — same pattern as the existing `Evaluate`:

```python
class ArtifactReview(PipelineComponent):
    """Pipeline component that performs an agentic artifact review."""

    def __init__(self, config: ReviewConfig) -> None:
        self._engine = ReviewEngine.from_config(config)

    def execute(self, event: dict) -> dict:
        payload = ArtifactPayload.from_event(event)
        result = self._engine.review(payload)
        return asdict(result)
```

---

## Configuration (`ReviewConfig`)

A single YAML file (or dict) configures the full review stack:

```yaml
# review_config.yaml
backend:
  type: anthropic            # registered backend name
  model: claude-sonnet-4-5-20250929
  temperature: 0.0
  max_tokens: 4096

prompt:
  name: study_design_review
  template_dirs:             # optional extra template dirs
    - ./custom_prompts

knowledge:
  type: static               # or "vector"
  path: ./knowledge_base     # directory of .md files
  top_k: 5
```

`config.py` loads this into a typed `ReviewConfig` dataclass, with environment
variable overrides (`REVIEW_BACKEND_TYPE`, `REVIEW_BACKEND_MODEL`, etc.).

---

## Registry Pattern

All three pluggable dimensions use the same registry idiom:

```python
class BackendRegistry:
    _backends: dict[str, type[Backend]] = {}

    @classmethod
    def register(cls, name: str):
        """Decorator to register a backend class."""
        def decorator(klass):
            cls._backends[name] = klass
            return klass
        return decorator

    @classmethod
    def create(cls, name: str, **kwargs) -> Backend:
        return cls._backends[name](**kwargs)

# Usage:
@BackendRegistry.register("anthropic")
class AnthropicBackend:
    ...
```

Same for `PromptRegistry` and `KnowledgeRegistry`. This allows third-party
extensions to register new backends / KBs without modifying package code.

---

## Dependency Strategy

| Component         | Core dep? | Optional extra   |
|-------------------|-----------|------------------|
| Engine / models   | Yes       | —                |
| PromptRegistry    | Yes       | `jinja2`         |
| StaticKB          | Yes       | —                |
| AnthropicBackend  | No        | `anthropic`      |
| OpenAIBackend     | No        | `openai`         |
| LiteLLMBackend    | No        | `litellm`        |
| VectorKB          | No        | `chromadb` / ... |

```toml
[project.optional-dependencies]
review    = ["jinja2>=3.1"]
anthropic = ["jinja2>=3.1", "anthropic>=0.40"]
openai    = ["jinja2>=3.1", "openai>=1.50"]
litellm   = ["jinja2>=3.1", "litellm>=1.50"]
all       = ["jinja2>=3.1", "anthropic>=0.40", "openai>=1.50", "litellm>=1.50"]
```

---

## How It Fits the Existing Architecture

| Existing pattern                | New equivalent                            |
|---------------------------------|-------------------------------------------|
| `scorer.py` (pure logic)        | `review/engine.py` (pure review logic)    |
| `adapter.py` (PipelineComponent)| `review/review_adapter.py`                |
| `ModelType` enum                | `PromptSpec` + backend name               |
| `CONFIDENCE_MAP` dict           | `PromptRegistry` + `BackendRegistry`      |
| `EvaluateResult` dataclass      | `ReviewResult` dataclass                  |
| `score_initiative()` function   | `ReviewEngine.review()` method            |

The deterministic scorer and the agentic reviewer can run independently or be
composed in sequence inside the orchestrator pipeline (score first, then review,
or vice versa).

---

## Implementation Phases

| Phase | Scope                                     | Deliverable                          |
|-------|-------------------------------------------|--------------------------------------|
| 1     | Data models + engine skeleton + config    | `models.py`, `engine.py`, `config.py`|
| 2     | Prompt registry + template rendering      | `prompts/` subpackage                |
| 3     | Backend abstraction + Anthropic backend   | `backends/` subpackage               |
| 4     | Static knowledge base                     | `knowledge/` subpackage              |
| 5     | Pipeline adapter + integration tests      | `review_adapter.py`, tests           |
| 6     | Additional backends (OpenAI, LiteLLM)     | extra backend modules                |
| 7     | Vector knowledge base                     | `vector.py` + optional deps          |
