"""Knowledge base abstraction for domain-specific retrieval."""

from impact_engine_evaluate.review.knowledge.base import Chunk, KnowledgeBase
from impact_engine_evaluate.review.knowledge.static import StaticKnowledgeBase

__all__ = ["Chunk", "KnowledgeBase", "StaticKnowledgeBase"]
