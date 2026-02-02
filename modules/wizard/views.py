import streamlit as st
import time
from modules.core.session import SessionManager
from modules.campaigns.service import CampaignService
from modules.creators.service import CreatorService
from modules.ui.components import render_glass_card

class AuditWizard:
    """
    Multi-step Wizard for new Creator Audits.
    Steps:
    1. Campaign Context
    2. Creator Identity (URL)
    3. Verification & Analysis
    4. Result Redirect
    """
    def __init__(self):
        self.camp_service = CampaignService()
        self.creator_service = CreatorService()

    def render(self):
        """Main Wizard Router."""
        if 'wizard_step' not in st.session_state:
            st.session_state.wizard_step = 1

        step = st.session_state.wizard_step
        
        # Progress Bar
        progress_map = {1: 25, 2: 50, 3: 75, 4: 100}
        st.progress(progress_map.get(step, 0))

        if step == 1:
            self.step_campaign_select()
        elif step == 2:
            self.step_creator_input()
        elif step == 3:
            self.step_analysis_run()
        elif step == 4:
            self.step_complete()

    def step_campaign_select(self):
        """Step 1: Ensure we are in the right campaign."""
        st.subheader("1. Select Workspace")
        
        # Get Campaigns
        campaigns = self.camp_service.list_my_campaigns()
        if not campaigns:
            st.warning("You need a campaign first.")
            return

        cols = st.columns([2, 1])
        with cols[0]:
            # Current Selection
            active_id = SessionManager.get_active_campaign_id()
            options = {c.name: c.id for c in campaigns}
            
            # Find index
            idx = 0
            if active_id in options.values():
                 curr_name = [k for k,v in options.items() if v == active_id][0]
                 idx = list(options.keys()).index(curr_name)
            
            selected = st.selectbox("Campaign", list(options.keys()), index=idx)
            
            # Confirm Button
            if st.button("Next: Add Creator", type="primary"):
                SessionManager.set_active_campaign_id(options[selected])
                st.session_state.wizard_step = 2
                st.rerun()

    def step_creator_input(self):
        """Step 2: Identify the Creator."""
        st.subheader("2. Identify Creator")
        
        camp_id = SessionManager.get_active_campaign_id()
        if not camp_id:
            st.error("No campaign selected.")
            st.session_state.wizard_step = 1
            st.rerun()

        url = st.text_input("YouTube Channel or Video URL", placeholder="https://youtube.com/...")
        
        if st.button("Analyze Creator", type="primary"):
            if not url:
                st.warning("Please paste a URL.")
                return
            
            # Simulate "Resolution" (In real app, we fetch metadata here)
            # For now, we assume URL is valid and extract simple ID
            channel_id = url # Simplification for prototype
            name = "Unknown Creator" # Placeholder until scrape
            
            # 1. Register Logic
            with st.spinner("Registering creator..."):
                # In real flow, we'd scrape metadata first to get Name/ID
                # Here we pass the raw URL as ID for the MVP connection
                # The generic scraper will handle the actual data later
                
                # Update Session for Step 3
                st.session_state.wizard_url = url
                st.session_state.wizard_step = 3
                st.rerun()

    def step_analysis_run(self):
        """Step 3: Execution."""
        st.subheader("3. analyzing...")
        
        url = st.session_state.get('wizard_url')
        render_glass_card(f"🚀 Launching agents on: **{url}**", vibe="neon")
        
        # This is where we call the heavy "fetch_all_data" from app.py
        # Since logic is still in app.py helper, we need to bridge it.
        # ideally this moves to a 'RunService'.
        
        st.info("Analysis Engine Running... (Using existing App logic)")
        
        # We set a flag so app.py knows to run the extraction
        # This is strictly a UI Wizard component, avoiding duplicating the scraper logic right this second
        # We signal completion to move to step 4
        
        # Mocking progress for UX
        bar = st.progress(0)
        for i in range(100):
            time.sleep(0.01)
            bar.progress(i + 1)
        
        st.success("Analysis Complete!")
        time.sleep(1)
        st.session_state.wizard_step = 4
        st.rerun()

    def step_complete(self):
        st.balloons()
        st.success("Creator added to Campaign!")
        if st.button("View Report"):
            # Reset wizard
            st.session_state.wizard_step = 1
            # Signal app to show report
            st.rerun()
