from modules.creators.repository import CreatorRepository
from modules.creators.models import Creator, CreatorCreate, AnalysisRun
from modules.core.session import SessionManager
import streamlit as st

class CreatorService:
    def __init__(self):
        self.repo = CreatorRepository()

    def get_or_register_creator(self, channel_id: str, name: str, handle: str = None) -> Creator:
        """
        Ensures a creator exists in our registry.
        """
        existing = self.repo.get_by_channel_id(channel_id)
        if existing:
            return existing
        
        # Create new
        new_creator = CreatorCreate(
            channel_id=channel_id,
            name=name,
            handle=handle,
            subscriber_count=0 
            # In a real app, we'd fetch sub count here from metadata
        )
        return self.repo.create(new_creator)

    def add_creator_to_campaign(self, creator: Creator) -> bool:
        """Links a creator to the active campaign."""
        camp_id = SessionManager.get_active_campaign_id()
        if not camp_id:
            st.warning("No active campaign selected.")
            return False
            
        return self.repo.link_to_campaign(camp_id, creator.id)

    def record_analysis_result(self, creator: Creator, analysis_data: dict):
        """
        Saves the results of an audit to the history.
        Decouples 'Identity' from 'Analysis'.
        """
        camp_id = SessionManager.get_active_campaign_id()
        fit = analysis_data.get('creator_fit', {})
        score = fit.get('score', 0)
        
        self.repo.log_analysis(
            creator_id=creator.id,
            campaign_id=camp_id,
            analysis_data=analysis_data,
            score=score
        )
        
    def get_campaign_roster(self) -> list[Creator]:
        """Get all creators in the current campaign."""
        camp_id = SessionManager.get_active_campaign_id()
        if not camp_id:
            return []
        return self.repo.get_campaign_roster(camp_id)

    def get_creator_full_profile(self, creator_id: str) -> dict:
        """
        Aggregates all intelligence on a creator.
        Returns: {
            'identity': Creator,
            'history': List[AnalysisRun],
            'campaigns': List[dict],
            'stats': dict
        }
        """
        creator = self.repo.get_by_id(creator_id)
        if not creator:
            # Fallback for old IDs that might be channel_ids
            creator = self.repo.get_by_channel_id(creator_id)
        
        # history = self.repo.get_analysis_history(creator_id)
        # Fix: handle case where creator might be None
        if not creator:
            return None
            
        history = self.repo.get_analysis_history(creator.id)
        usage = self.repo.get_campaign_usage(creator.id)
        
        # Calculate Stats
        avg_score = 0
        if history:
            scores = [r.fit_score for r in history if r.fit_score]
            if scores:
                avg_score = int(sum(scores) / len(scores))
        
        return {
            "identity": creator,
            "history": history,
            "campaigns": usage,
            "stats": {
                "latest_score": history[0].fit_score if history else 0,
                "avg_score": avg_score,
                "total_audits": len(history)
            }
        }

    def get_enriched_campaign_roster(self, campaign_id: str) -> list[dict]:
        """
        Returns creators + their specific score for this campaign.
        """
        return self.repo.get_campaign_roster_stats(campaign_id)
