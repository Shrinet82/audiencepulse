import subprocess
import os
import streamlit as st
from modules.creators.service import CreatorService

class AnalysisService:
    """
    Orchestrates the scraping and AI analysis.
    Moves logic out of app.py.
    """
    
    @staticmethod
    def run_full_audit(url: str, creator_service: CreatorService):
        """
        Runs scraper.py, builds creator profile, and saves results.
        Returns the result dict.
        """
        # 1. Scrape
        try:
            result = subprocess.run(
                ["python3", "scraper.py", url, "-o", "temp_comments.jsonl"],
                capture_output=True, text=True, cwd=os.getcwd()
            )
            if result.returncode != 0:
                raise Exception(f"Scraper failed: {result.stderr}")
        except Exception as e:
            st.error(str(e))
            return None

        # 2. Analyze (Mocking the complex 'run_creator_audit' logic from app.py for now)
        # In a full refactor, 'run_creator_audit' should be moved here.
        # For this phase, we mostly validate the workflow connection.
        
        return {"status": "success", "comments_count": 0} # Placeholder
