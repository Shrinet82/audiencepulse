# Pydantic Data Contracts for AudiencePulse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class Comment(BaseModel):
    """Single YouTube comment."""
    author: str = ""
    text: str
    likes: int = 0
    replies: int = 0
    timestamp: Optional[str] = None

class CommentBatch(BaseModel):
    """Batch of comments for processing."""
    batch_id: int
    comments: List[Comment]

class SentimentBreakdown(BaseModel):
    """Sentiment percentages."""
    positive: float = 0.0
    negative: float = 0.0
    neutral: float = 0.0

class LocalMetrics(BaseModel):
    """Metrics extracted locally (no LLM)."""
    batch_id: int
    total_comments: int = 0
    avg_length: float = 0.0
    short_comments: int = 0
    long_comments: int = 0
    questions: int = 0
    question_rate: float = 0.0
    positive_emojis: int = 0
    negative_emojis: int = 0
    total_votes: int = 0
    total_replies: int = 0
    potential_spam: int = 0

class LLMMetrics(BaseModel):
    """Metrics extracted via LLM."""
    batch_id: int
    sentiment_breakdown: SentimentBreakdown
    top_topics: List[str] = []
    controversy_score: float = Field(default=0.0, ge=0, le=100)
    feature_requests: List[str] = []
    influencer_mentions: List[str] = []
    overall_summary: str = ""
    sample_comments: List[str] = []  # Provenance for explainability

class AnalysisResult(BaseModel):
    """Combined analysis output."""
    llm_analysis: List[LLMMetrics] = []
    local_metrics: List[LocalMetrics] = []
