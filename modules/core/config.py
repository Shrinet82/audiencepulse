import os
import streamlit as st
from supabase import create_client, Client

class AppConfig:
    """Central configuration loader."""
    
    @staticmethod
    def get_supabase_client() -> Client:
        # Load secrets from Streamlit secrets or Env vars
        try:
            # Try loading from streamlit secrets (lowercase nested)
            if "supabase" in st.secrets:
                url = st.secrets["supabase"]["url"]
                key = st.secrets["supabase"]["key"]
                return create_client(url, key)
            
            # Fallback to env vars or uppercase keys (legacy)
            url = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
            key = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")
            
            if url and key:
                return create_client(url, key)
                
            return None
        except Exception as e:
            st.error(f"AppConfig Init Failed: {e}")
            return None

    @staticmethod
    def is_dev_mode() -> bool:
        return os.environ.get("ENV") == "development"
