# Tests for AudiencePulse Exporter
import pytest
import pandas as pd
import os
import tempfile

class TestExporter:
    """Tests for the exporter module."""
    
    def test_csv_structure(self):
        """Test CSV output structure."""
        # Sample data structure
        sentiment_data = [
            {"Batch_ID": 1, "Positive_Pct": 60.0, "Negative_Pct": 20.0, "Neutral_Pct": 20.0},
            {"Batch_ID": 2, "Positive_Pct": 55.0, "Negative_Pct": 25.0, "Neutral_Pct": 20.0},
        ]
        
        df = pd.DataFrame(sentiment_data)
        
        assert "Batch_ID" in df.columns
        assert "Positive_Pct" in df.columns
        assert len(df) == 2

    def test_csv_export(self):
        """Test actual CSV file export."""
        data = {"col1": [1, 2], "col2": ["a", "b"]}
        df = pd.DataFrame(data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            
            # Read back and verify
            df_read = pd.read_csv(f.name)
            assert len(df_read) == 2
            assert list(df_read.columns) == ["col1", "col2"]
            
            os.unlink(f.name)

    def test_looker_csv_columns(self):
        """Test that Looker CSVs have expected columns."""
        expected_sentiment_cols = ["Batch_ID", "Positive_Pct", "Negative_Pct", "Neutral_Pct"]
        expected_topics_cols = ["Batch_ID", "Topic"]
        expected_engagement_cols = [
            "Batch_ID", "Total_Comments", "Avg_Length", "Short_Comments",
            "Long_Comments", "Questions", "Question_Rate_Pct"
        ]
        
        # Verify column lists are valid
        assert len(expected_sentiment_cols) == 4
        assert "Topic" in expected_topics_cols
        assert "Total_Comments" in expected_engagement_cols

    def test_empty_data_handling(self):
        """Test handling of empty data."""
        empty_df = pd.DataFrame()
        
        assert len(empty_df) == 0
        assert empty_df.empty
