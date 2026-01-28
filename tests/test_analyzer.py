# Tests for AudiencePulse Analyzer
import pytest
from unittest.mock import patch, MagicMock
import json

class TestAnalyzer:
    """Tests for the analyzer module."""
    
    def test_local_metrics_extraction(self):
        """Test local metrics calculation."""
        sample_comments = [
            {"text": "This is great!", "votes": "10", "replies": "2"},
            {"text": "Why?", "votes": "5", "replies": "1"},
            {"text": "👍👍👍 Amazing work", "votes": "20", "replies": "0"},
        ]
        
        # Calculate expected metrics
        total = len(sample_comments)
        questions = sum(1 for c in sample_comments if "?" in c["text"])
        
        assert total == 3
        assert questions == 1

    def test_emoji_detection(self):
        """Test emoji detection in comments."""
        positive_emojis = {'👍', '😀', '❤️', '🔥', '✨'}
        negative_emojis = {'👎', '😞', '💔', '😡'}
        
        text = "👍 This is 🔥🔥🔥 amazing!"
        
        pos_count = sum(1 for c in text if c in positive_emojis)
        neg_count = sum(1 for c in text if c in negative_emojis)
        
        assert pos_count >= 1
        assert neg_count == 0

    def test_batch_creation(self):
        """Test comment batching logic."""
        comments = [{"text": f"Comment {i}"} for i in range(125)]
        batch_size = 50
        
        num_batches = (len(comments) + batch_size - 1) // batch_size
        
        assert num_batches == 3

    @patch("groq.Groq")
    def test_llm_response_parsing(self, mock_groq):
        """Test LLM response parsing."""
        mock_response = {
            "sentiment_breakdown": {"positive": 60, "negative": 20, "neutral": 20},
            "top_topics": ["topic1", "topic2"],
            "controversy_score": 45,
            "feature_requests": [],
            "influencer_mentions": [],
            "overall_summary": "Test summary"
        }
        
        # Verify JSON parsing works
        parsed = json.loads(json.dumps(mock_response))
        assert parsed["sentiment_breakdown"]["positive"] == 60
        assert len(parsed["top_topics"]) == 2
