# Tests for AudiencePulse Models
import pytest
from audiencepulse.models import (
    Comment, CommentBatch, SentimentBreakdown,
    LocalMetrics, LLMMetrics, AnalysisResult
)

class TestModels:
    """Tests for Pydantic models."""
    
    def test_comment_model(self):
        """Test Comment model creation."""
        comment = Comment(text="Hello world!", author="TestUser")
        assert comment.text == "Hello world!"
        assert comment.author == "TestUser"
        assert comment.likes == 0  # Default value

    def test_comment_batch_model(self):
        """Test CommentBatch model creation."""
        comments = [
            Comment(text="Comment 1", author="User1"),
            Comment(text="Comment 2", author="User2"),
        ]
        batch = CommentBatch(batch_id=1, comments=comments)
        
        assert batch.batch_id == 1
        assert len(batch.comments) == 2

    def test_sentiment_breakdown_model(self):
        """Test SentimentBreakdown model."""
        sentiment = SentimentBreakdown(positive=60.0, negative=20.0, neutral=20.0)
        
        assert sentiment.positive == 60.0
        assert sentiment.positive + sentiment.negative + sentiment.neutral == 100.0

    def test_local_metrics_model(self):
        """Test LocalMetrics model."""
        metrics = LocalMetrics(
            batch_id=1,
            total_comments=50,
            avg_length=75.5,
            questions=5,
            question_rate=10.0
        )
        
        assert metrics.batch_id == 1
        assert metrics.total_comments == 50

    def test_llm_metrics_model(self):
        """Test LLMMetrics model."""
        metrics = LLMMetrics(
            batch_id=1,
            sentiment_breakdown=SentimentBreakdown(positive=60, negative=20, neutral=20),
            top_topics=["topic1", "topic2"],
            controversy_score=45.0,
            overall_summary="Test summary"
        )
        
        assert metrics.batch_id == 1
        assert len(metrics.top_topics) == 2
        assert metrics.controversy_score == 45.0

    def test_analysis_result_model(self):
        """Test AnalysisResult model."""
        result = AnalysisResult(
            llm_analysis=[],
            local_metrics=[]
        )
        
        assert len(result.llm_analysis) == 0
        assert len(result.local_metrics) == 0
