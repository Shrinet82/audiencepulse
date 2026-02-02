from modules.core.config import AppConfig
from modules.campaigns.models import Campaign, CampaignCreate
import streamlit as st

class CampaignRepository:
    """
    Data Access Layer for Campaigns.
    Directly talks to Supabase.
    """
    def __init__(self):
        self.client = AppConfig.get_supabase_client()

    def get_all_by_user(self, user_email: str) -> list[Campaign]:
        """Fetch all campaigns for a user."""
        try:
            res = self.client.table('campaigns').select("*").eq('user_email', user_email).execute()
            return [Campaign(**c) for c in res.data]
        except Exception as e:
            st.error(f"DB Error: {e}")
            return []

    def create(self, campaign: CampaignCreate) -> Campaign:
        """Insert a new campaign."""
        data = campaign.dict()
        res = self.client.table('campaigns').insert(data).execute()
        if res.data:
            return Campaign(**res.data[0])
        raise Exception("Insert failed")
