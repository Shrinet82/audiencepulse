from modules.core.config import AppConfig
from modules.creators.models import Creator, CreatorCreate, AnalysisRun
import streamlit as st

class CreatorRepository:
    def __init__(self):
        self.client = AppConfig.get_supabase_client()

    def get_by_channel_id(self, channel_id: str) -> Creator:
        """Find creator by ID."""
        try:
            res = self.client.table('creators').select("*").eq('channel_id', channel_id).execute()
            if res.data:
                return Creator(**res.data[0])
            return None
        except Exception as e:
            # st.error(f"Creator Lookup Error: {e}")
            return None

    def get_by_id(self, pk: str) -> Creator:
        """Find creator by UUID."""
        try:
            res = self.client.table('creators').select("*").eq('id', pk).execute()
            if res.data:
                return Creator(**res.data[0])
            return None
        except Exception:
            return None

    def create(self, dto: CreatorCreate) -> Creator:
        """Register a new creator."""
        data = dto.dict(exclude_none=True)
        res = self.client.table('creators').insert(data).execute()
        if res.data:
            return Creator(**res.data[0])
        raise Exception("Creator insert failed")

    def link_to_campaign(self, campaign_id: str, creator_id: str):
        """Add to campaign junction table."""
        try:
            data = {"campaign_id": campaign_id, "creator_id": creator_id}
            self.client.table('campaign_creators').insert(data).execute()
            return True
        except Exception:
            return False # Likely duplicate link

    def log_analysis(self, creator_id: str, campaign_id: str, analysis_data: dict, score: int):
        """Create a new AnalysisRun record."""
        run_data = {
            "creator_id": creator_id,
            "campaign_id": campaign_id,
            "status": "completed",
            "fit_score": score,
            "report_json": analysis_data
        }
        res = self.client.table('analysis_runs').insert(run_data).execute()
        return res.data[0] if res.data else None

    def get_campaign_creators(self, campaign_id: str) -> list[Creator]:
        """Fetch all creators in a campaign."""
        # Supabase Join: campaign_creators -> creators
        try:
            res = self.client.table('campaign_creators').select("creator_id, creators(*)").eq('campaign_id', campaign_id).execute()
            # Parse nested response
            creators = []
            for row in res.data:
                if row.get('creators'):
                    creators.append(Creator(**row['creators']))
            return creators
        except Exception as e:
            # print(f"Fetch Error: {e}")
            return []

    def get_analysis_history(self, creator_id: str) -> list[AnalysisRun]:
        """Fetch all analysis runs for a creator, ordered latest first."""
        try:
            res = self.client.table('analysis_runs').select("*").eq('creator_id', creator_id).order('created_at', desc=True).execute()
            return [AnalysisRun(**r) for r in res.data]
        except Exception:
            return []

    def get_campaign_usage(self, creator_id: str) -> list[dict]:
        """Fetch all campaigns a creator belongs to."""
        try:
            # Join campaign_creators -> campaigns
            res = self.client.table('campaign_creators').select("campaign_id, campaigns(name)").eq('creator_id', creator_id).execute()
            # Flatten structure
            usage = []
            for row in res.data:
                if row.get('campaigns'):
                    usage.append({
                        "id": row['campaign_id'],
                        "name": row['campaigns']['name']
                    })
            return usage
        except Exception as e:
            # st.write(f"Usage Fetch Error: {e}")
            return []
            
    def get_latest_analysis(self, creator_id: str) -> AnalysisRun:
        """Get the single most recent analysis for header snapshots."""
        history = self.get_analysis_history(creator_id)
        return history[0] if history else None

    def get_campaign_roster_stats(self, campaign_id: str) -> list[dict]:
        """
        Fetches creators in a campaign AND their analysis stats for that campaign.
        Returns list of dicts: { 'creator': Creator, 'latest_run': AnalysisRun | None }
        """
        try:
            # 1. Get creators in campaign
            creators = self.get_campaign_creators(campaign_id)
            roster = []
            
            for c in creators:
                # 2. Get analysis for this specific campaign
                # This is N+1, but fine for MVP scale (usually < 50 creators per camp)
                # Optimization: Could do single complex query later
                res = self.client.table('analysis_runs')\
                    .select("*")\
                    .eq('campaign_id', campaign_id)\
                    .eq('creator_id', c.id)\
                    .order('created_at', desc=True)\
                    .limit(1)\
                    .execute()
                
                run = None
                if res.data:
                    run = AnalysisRun(**res.data[0])
                
                roster.append({
                    "creator": c,
                    "analysis": run
                })
            return roster
        except Exception as e:
            # st.error(f"Roster Error: {e}")
            return []
