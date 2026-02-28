"""Data models for artifact review."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ReviewDimension:
    """A single scored dimension of an artifact review.

    Parameters
    ----------
    name : str
        Dimension identifier (e.g. ``"internal_validity"``).
    score : float
        Score between 0.0 and 1.0.
    justification : str
        Free-text explanation of the score.
    """

    name: str
    score: float
    justification: str


@dataclass
class ReviewResult:
    """Complete result of an artifact review.

    Parameters
    ----------
    initiative_id : str
        Identifier of the reviewed initiative.
    prompt_name : str
        Name of the prompt template used.
    prompt_version : str
        Version string of the prompt template.
    backend_name : str
        Registered name of the LLM backend.
    model : str
        Model identifier used for completion.
    dimensions : list[ReviewDimension]
        Per-dimension scores and justifications.
    overall_score : float
        Aggregated score across dimensions (mean).
    raw_response : str
        Full LLM output retained for audit.
    timestamp : str
        ISO-8601 timestamp of the review.
    """

    initiative_id: str
    prompt_name: str
    prompt_version: str
    backend_name: str
    model: str
    dimensions: list[ReviewDimension] = field(default_factory=list)
    overall_score: float = 0.0
    raw_response: str = ""
    timestamp: str = ""


@dataclass
class ArtifactPayload:
    """Typed input envelope for an artifact to review.

    Parameters
    ----------
    initiative_id : str
        Unique initiative identifier.
    artifact_text : str
        The artifact content to review.
    model_type : str
        Causal inference methodology label.
    sample_size : int
        Sample size of the study.
    metadata : dict
        Additional key-value pairs forwarded to the prompt template.
    """

    initiative_id: str
    artifact_text: str
    model_type: str = ""
    sample_size: int = 0
    metadata: dict = field(default_factory=dict)

    @classmethod
    def from_event(cls, event: dict) -> ArtifactPayload:
        """Construct a payload from a pipeline event dict.

        Parameters
        ----------
        event : dict
            Pipeline event. Must contain ``initiative_id`` and
            ``artifact_text``.  All other keys are passed through
            as ``metadata``.

        Returns
        -------
        ArtifactPayload
        """
        known = {"initiative_id", "artifact_text", "model_type", "sample_size"}
        return cls(
            initiative_id=event["initiative_id"],
            artifact_text=event["artifact_text"],
            model_type=event.get("model_type", ""),
            sample_size=event.get("sample_size", 0),
            metadata={k: v for k, v in event.items() if k not in known},
        )


@dataclass
class PromptSpec:
    """Metadata and template content for a review prompt.

    Parameters
    ----------
    name : str
        Unique prompt identifier.
    version : str
        Semver-style version string.
    description : str
        Human-readable description.
    dimensions : list[str]
        Names of scoring dimensions this prompt expects.
    system_template : str
        Jinja2 template for the system message.
    user_template : str
        Jinja2 template for the user message.
    """

    name: str
    version: str
    description: str
    dimensions: list[str] = field(default_factory=list)
    system_template: str = ""
    user_template: str = ""
