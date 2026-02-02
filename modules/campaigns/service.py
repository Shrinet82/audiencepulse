from modules.campaigns.repository import CampaignRepository
from modules.campaigns.models import Campaign, CampaignCreate
from modules.core.session import SessionManager
import streamlit as st

class CampaignService:
    """
    Business Logic Layer for Campaigns.
    """
    def __init__(self):
        self.repo = CampaignRepository()

    def list_my_campaigns(self) -> list[Campaign]:
        user = SessionManager.get_user()
        if not user:
            return []
        return self.repo.get_all_by_user(user.email)

    def create_new_campaign(self, name: str, desc: str) -> bool:
        user = SessionManager.get_user()
        if not user:
            return False
        
        try:
            # Validate via Pydantic DTO
            dto = CampaignCreate(
                user_email=user.email,
                name=name,
                description=desc
            )
            # Call Repo
            new_campaign = self.repo.create(dto)
            
            # Select it automatically
            SessionManager.set_active_campaign_id(new_campaign.id)
            st.toast(f"✅ Campaign '{name}' created!")
            return True
            
        except ValueError as ve:
            st.warning(f"Validation Error: {ve}")
            return False
        except Exception as e:
            if "unique" in str(e).lower():
                st.toast(f"⚠️ Campaign '{name}' already exists.")
            else:
                st.error(f"Service Error: {e}")
            return False
