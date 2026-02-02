import streamlit as st
from typing import Optional, Dict, Any

class SessionManager:
    """
    Central logic for Session State.
    Prevents key errors and manages state lifecycle.
    """
    
    @staticmethod
    def init():
        """Initialize default session state keys."""
        defaults = {
            "user": None,
            "selected_campaign_id": None,
            "selected_creator_id": None,
            "comparison_ids": [],
            "audit_results": None,
            "creator_profiles": [],
            "shortlist": [],
            "video_metadata": None,
            "chat_history": []
        }
        for key, val in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = val

    @staticmethod
    def get_user() -> Optional[Dict[str, Any]]:
        return st.session_state.get("user")

    @staticmethod
    def set_user(user_data: Dict[str, Any]):
        st.session_state["user"] = user_data

    @staticmethod
    def get_active_campaign_id() -> Optional[str]:
        return st.session_state.get("selected_campaign_id")
    
    @staticmethod
    def set_active_campaign_id(campaign_id: str):
        st.session_state["selected_campaign_id"] = campaign_id

    @staticmethod
    def get_selected_creator_id() -> Optional[str]:
        return st.session_state.get("selected_creator_id")

    @staticmethod
    def set_selected_creator_id(creator_id: str):
        st.session_state["selected_creator_id"] = creator_id

    @staticmethod
    def get_comparison_ids() -> list[str]:
        return st.session_state.get("comparison_ids", [])

    @staticmethod
    def set_comparison_ids(ids: list[str]):
        st.session_state["comparison_ids"] = ids

    @staticmethod
    def clear_audit_session():
        """Reset current audit data."""
        st.session_state["audit_results"] = None
        st.session_state["video_metadata"] = None
