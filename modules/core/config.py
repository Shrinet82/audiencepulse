import os
import streamlit as st
from supabase import create_client, Client

class AppConfig:
    """Central configuration loader."""
    
    @staticmethod
    def get_supabase_client() -> Client:
        # Load secrets from Streamlit secrets or Env vars
        try:
            # 1. Try Environment Variables (Azure/Prod)
            url = os.environ.get("SUPABASE_URL")
            key = os.environ.get("SUPABASE_KEY")
            
            # 2. Try Streamlit Secrets (Local Dev) - Only if Env Vars missing
            if not url or not key:
                try:
                    # Safe access to st.secrets
                    if "supabase" in st.secrets:
                        url = st.secrets["supabase"]["url"]
                        key = st.secrets["supabase"]["key"]
                except FileNotFoundError:
                    pass # Secrets file not found (normal in Prod)
                except Exception:
                    pass # Handle other secrets access errors gracefully

            if url and key:
                return create_client(url, key)
                
            return None
        except Exception as e:
            st.error(f"AppConfig Init Failed: {e}")
            return None

    @staticmethod
    def is_dev_mode() -> bool:
        return os.environ.get("ENV") == "development"
