import streamlit as st
import pandas as pd
from modules.campaigns.service import CampaignService
from modules.creators.service import CreatorService
from modules.core.session import SessionManager
from modules.ui.components import render_glass_card, render_hero_score

class CampaignViews:
    """
    Presentation Layer for Campaigns.
    Calls Service Layer.
    """
    def __init__(self):
        self.service = CampaignService()
        self.creator_service = CreatorService()

    def render_manager_sidebar(self):
        """Renders the Campaign Manager in the Sidebar."""
        st.sidebar.markdown("### 📂 My Campaigns")
        
        # 1. New Campaign Input
        with st.sidebar.expander("➕ New Campaign", expanded=False):
            with st.form("new_campaign_form"):
                new_name = st.text_input("Campaign Name", placeholder="e.g. Summer Launch '26")
                new_desc = st.text_area("Description")
                if st.form_submit_button("Create"):
                    if new_name:
                        self.service.create_new_campaign(new_name, new_desc)
                        st.rerun()

        # 2. Select Active Campaign
        active_id = SessionManager.get_active_campaign_id()
        campaigns = self.service.list_my_campaigns()
        
        if campaigns:
            # Map names to IDs for Selectbox
            options = {c.name: c.id for c in campaigns}
            
            # Find index of current active
            current_index = 0
            if active_id and active_id in options.values():
                # Reverse lookup
                 current_name = [k for k, v in options.items() if v == active_id][0]
                 current_index = list(options.keys()).index(current_name)
            
            selected_name = st.sidebar.selectbox(
                "Select Campaign", 
                list(options.keys()), 
                index=current_index,
                key="campaign_selector"
            )
            
            # Update Session on Change
            new_id = options[selected_name]
            if new_id != active_id:
                SessionManager.set_active_campaign_id(new_id)
                st.toast(f"Switched to '{selected_name}'")
                st.rerun()
        else:
            st.sidebar.info("No campaigns yet.")

    def render_dashboard_grid(self):
        """Renders the Campaign Grid (Project Selection)."""
        st.subheader("🚀 Active Missions")
        campaigns = self.service.list_my_campaigns()
        
        if not campaigns:
            render_glass_card("No campaigns found. Create one in the sidebar!", vibe="neutral")
            return

        cols = st.columns(3)
        for i, c in enumerate(campaigns):
            with cols[i % 3]:
                # Glass Card with click handler simulated via button
                st.markdown(f"""
                <div class="glass-card" style="margin-bottom:10px">
                    <h3>{c.name}</h3>
                    <p>{c.description or 'No brief'}</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Enter Mission: {c.name}", key=f"btn_enter_{c.id}", use_container_width=True):
                    SessionManager.set_active_campaign_id(c.id)
                    st.rerun()

    def render_workspace(self, campaign_id: str):
        """
        The 'Decision Hub' for a specific campaign.
        """
        # 1. Fetch Context
        campaigns = self.service.list_my_campaigns() # Inefficient but safe
        camp = next((c for c in campaigns if c.id == campaign_id), None)
        if not camp:
            st.error("Campaign not found.")
            return

        # 2. Logic: Fetch Roster
        roster = self.creator_service.get_enriched_campaign_roster(campaign_id)
        
        # 3. Hero Header
        st.markdown(f"<h1>📂 {camp.name}</h1>", unsafe_allow_html=True)
        st.caption(camp.description or "No mission brief set.")
        
        stats_cols = st.columns(4)
        with stats_cols[0]:
            st.metric("Candidates", len(roster))
        with stats_cols[1]:
            # Calculate Avg Match
            avg_match = 0
            scores = [item['analysis'].fit_score for item in roster if item['analysis'] and item['analysis'].fit_score]
            if scores:
                avg_match = int(sum(scores) / len(scores))
            st.metric("Avg Match", f"{avg_match}")
        with stats_cols[2]:
            st.metric("Budget Tier", "Premium") # Placeholder logic
        with stats_cols[3]:
            if st.button("➕ Add Creator", type="primary"):
                # Jump to Wizard
                # We need to signal app.py to switch view, or just rely on sidebar
                st.info("Use 'Creator Audit' in sidebar to add new candidates.")

        st.divider()
        
        # 4. Roster Table (Decision Surface)
        if not roster:
            st.info("No creators in this mission yet. Go to 'Creator Audit' to scout candidates.")
        else:
            # ----------------------------------------
            # COMPARISON ENGINE TRIGGER
            # ----------------------------------------
            st.subheader("⚔️ Battle Mode")
            # Create a simple name map
            roster_map = {item['creator'].name: item['creator'].id for item in roster}
            
            # Persist selection if possible, or just local
            selected_names = st.multiselect(
                "Select 2+ candidates to compare head-to-head:",
                options=list(roster_map.keys()),
                key="compare_multiselect"
            )
            
            if len(selected_names) >= 2:
                if st.button(f"⚔️ Compare {len(selected_names)} Creators", type="primary"):
                    # Get IDs
                    ids = [roster_map[n] for n in selected_names]
                    SessionManager.set_comparison_ids(ids)
                    st.query_params["view"] = "compare" # Optional
                    st.rerun()

            st.divider()
            st.subheader("Candidate Roster")
            
            # Custom Grid Rendering
            for item in roster:
                c = item['creator']
                run = item['analysis']
                score = run.fit_score if run else 0
                
                # Dynamic Border Color based on score
                border_color = "#334155"
                if score >= 80: border_color = "#10b981"
                elif score >= 50: border_color = "#f59e0b"
                
                col_c, col_s, col_a = st.columns([3, 1, 1])
                with col_c:
                    st.markdown(f"**{c.name}**")
                    st.caption(f"Subscriber Count: {c.subscriber_count or 'N/A'}")
                with col_s:
                     st.markdown(f"<div style='color:{border_color}; font-weight:bold; font-size:1.2rem'>{score}</div>", unsafe_allow_html=True)
                with col_a:
                    if st.button("Manage Profile", key=f"view_{c.id}"):
                         SessionManager.set_selected_creator_id(c.id)
                         st.query_params["view"] = "profile" # Optional deep link logic
                         # Force rerun to catch the session change in app.py
                         st.rerun()
                st.divider()
