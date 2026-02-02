import streamlit as st
import pandas as pd
from modules.creators.service import CreatorService
from modules.reports.exports import generate_agency_brief
from modules.ui.components import render_glass_card, render_hero_score
from modules.ui.charts import render_radar_chart, render_trend_line

class CreatorViews:
    def __init__(self):
        self.service = CreatorService()

    def render_profile(self, creator_id: str):
        """
        Renders the Full Intelligence Profile for a creator.
        """
        # 1. Fetch Data
        data = self.service.get_creator_full_profile(creator_id)
        creator = data['identity']
        history = data['history']
        stats = data['stats']
        
        if not creator:
            st.error("Creator not found.")
            return

        # 2. Hero Header
        col_img, col_info, col_score = st.columns([1, 3, 2])
        
        with col_img:
            # Avatar placeholder if none
            avatar = creator.avatar_url or "https://ui-avatars.com/api/?name=" + creator.name
            st.image(avatar, width=100)
            
        with col_info:
            st.title(creator.name)
            st.caption(f"YouTube • {creator.channel_id}")
            if creator.handle:
                st.markdown(f"**{creator.handle}**")
            
            # Badges
            st.markdown(f"""
            <span style="background:rgba(16, 185, 129, 0.2); color:#10b981; padding:4px 8px; border-radius:4px; font-size:0.8rem">✅ Vetted</span>
            <span style="background:rgba(59, 130, 246, 0.2); color:#3b82f6; padding:4px 8px; border-radius:4px; font-size:0.8rem; margin-left:8px">{stats['total_audits']} Audits</span>
            """, unsafe_allow_html=True)
            
        with col_score:
            latest_score = stats['latest_score']
            render_hero_score(latest_score, "A" if latest_score > 80 else "B", "Latest Audit")

        st.divider()

        # 3. Intelligence Summary (Tabs)
        tab_overview, tab_history, tab_campaigns = st.tabs(["🧠 Intelligence", "📜 Audit History", "📂 Campaigns"])
        
        with tab_overview:
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                render_glass_card(f"**Average Score**<br><h1>{stats['avg_score']}</h1>", vibe="neutral")
            with sc2:
                 # Extract latest DNA for Radar
                latest_run = history[0] if history else None
                if latest_run and latest_run.report_json:
                    dna = latest_run.report_json.get('audience_dna', {})
                    health = latest_run.report_json.get('community_health', {})
                    
                    # Map values
                    budget = dna.get('spending_power', {}).get('budget_score', 50)
                    tech = dna.get('tech_literacy', {}).get('expert_score', 50)
                    
                    # Map Trust Grade to Int
                    trust_grade = health.get('trust', {}).get('score', 'C')
                    trust_map = {'A': 95, 'B': 80, 'C': 60, 'D': 40, 'F': 20}
                    trust = trust_map.get(trust_grade, 50)
                    
                    # Render Radar
                    render_radar_chart(
                        categories=['Spending', 'Tech Savvy', 'Brand Trust', 'Loyalty', 'Trendiness'],
                        values=[budget, tech, trust, 75, 65], # Partial mock for Loyalty/Trend
                        title="Audience Matrix"
                    )
                else:
                    render_glass_card(f"**Audience DNA**<br><small>No data</small>", vibe="neutral")
            with sc3:
                risk_status = "✅ Safe"
                # Check safety
                if latest_run and latest_run.report_json:
                    safe = latest_run.report_json.get('community_health', {}).get('toxicity', {}).get('is_safe', True)
                    if not safe: risk_status = "❌ High Risk"
                render_glass_card(f"**Risk Status**<br><h2>{risk_status}</h2>", vibe="success" if "Safe" in risk_status else "danger")

        with tab_history:
            if not history:
                st.info("No analysis history.")
            else:
                # Add Trend Line
                st.markdown("### 📈 Verification History")
                render_trend_line(history)
                st.divider()
                
                for run in history:
                    with st.expander(f"{run.created_at[:10]} • Score: {run.fit_score}"):
                        st.json(run.report_json)

        with tab_campaigns:
            if not data['campaigns']:
                st.info("Not used in any campaigns yet.")
            else:
                for camp in data['campaigns']:
                    st.markdown(f"📁 **{camp['name']}**")
        
        st.divider()
        
        # 4. Export Actions
        c1, c2 = st.columns([3, 1])
        with c1:
             st.caption("Ready to share this audit with the client?")
        with c2:
             if history:
                 # Generate on fly or check state
                 # For simplicity, generate when clicked -> download button appears
                 if st.button("📄 Prepare PDF Brief", key=f"gen_pdf_{creator.id}"):
                     try:
                         # Prepare data
                         latest_run = history[0]
                         pdf_bytes = generate_agency_brief(
                             creator_name=creator.name,
                             product_name="Current Pilot", # In a real app, pass campaign/product context
                             score=latest_run.fit_score,
                             analysis=latest_run.report_json
                         )
                         st.download_button(
                             label="⬇️ Download Brief",
                             data=pdf_bytes,
                             file_name=f"{creator.name}_Audit.pdf",
                             mime="application/pdf",
                             type="primary"
                         )
                     except Exception as e:
                         st.error(f"Export Failed: {e}")
