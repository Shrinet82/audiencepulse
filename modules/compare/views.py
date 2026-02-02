import streamlit as st
from modules.creators.service import CreatorService
from modules.ui.components import render_glass_card, render_hero_score
from modules.ui.charts import render_comparison_radar

class CompareViews:
    def __init__(self):
        self.creator_service = CreatorService()

    def render_battle_mode(self, creator_ids: list[str]):
        """
        Renders a side-by-side comparison of selected creators.
        """
        if not creator_ids or len(creator_ids) < 2:
            st.warning("Select at least 2 creators to compare.")
            return

        # Fetch Data
        profiles = []
        for cid in creator_ids:
            p = self.creator_service.get_creator_full_profile(cid)
            if p:
                profiles.append(p)

        st.markdown("## ⚔️ Comparison Battle Mode")
        
        # 0. Battle Radar (Overlay)
        radar_data = []
        colors = ['#10b981', '#3b82f6', '#f59e0b', '#ec4899']
        
        for i, p in enumerate(profiles):
            # Extract stats
            latest_run = p['history'][0] if p['history'] else None
            if latest_run and latest_run.report_json:
                dna = latest_run.report_json.get('audience_dna', {})
                health = latest_run.report_json.get('community_health', {})
                trust_grade = health.get('trust', {}).get('score', 'C')
                trust_map = {'A': 95, 'B': 80, 'C': 60, 'D': 40, 'F': 20}
                
                radar_data.append({
                    'name': p['identity'].name,
                    'values': [
                        dna.get('spending_power', {}).get('budget_score', 50),
                        dna.get('tech_literacy', {}).get('expert_score', 50),
                        trust_map.get(trust_grade, 50),
                        75, # Mock Loyalty
                        65  # Mock Trend
                    ],
                    'color': colors[i % len(colors)]
                })
        
        if radar_data:
            render_comparison_radar(
                categories=['Spending', 'Tech Savvy', 'Brand Trust', 'Loyalty', 'Trendiness'],
                series=radar_data
            )
            st.divider()

        # Layout: Dynamic based on count (max 3 recommended)
        cols = st.columns(len(profiles))
        
        # 1. Header (Identity & Score)
        for i, p in enumerate(profiles):
            with cols[i]:
                c = p['identity']
                stats = p['stats']
                
                # Avatar & Name
                st.markdown(f"<h3 style='text-align:center'>{c.name}</h3>", unsafe_allow_html=True)
                if c.avatar_url:
                    st.markdown(f"<div style='display:flex;justify-content:center'><img src='{c.avatar_url}' width='80' style='border-radius:50%'></div>", unsafe_allow_html=True)
                
                st.divider()
                
                # Hero Score
                score = stats.get('latest_score', 0)
                render_hero_score(score, "A" if score > 80 else "B", "Fit Score")

        st.divider()

        # 2. Risk & Safety (Critical)
        st.subheader("🛡️ Risk Analysis")
        risk_cols = st.columns(len(profiles))
        for i, p in enumerate(profiles):
            with risk_cols[i]:
                # Mocking risk extraction from latest run report
                latest_run = p['history'][0] if p['history'] else None
                risk_status = "Unknown"
                if latest_run and latest_run.report_json:
                    # deeply nested safety extraction
                    safety = latest_run.report_json.get('brand_safety', {})
                    is_safe = safety.get('brand_safety', {}).get('is_safe', True)
                    risk_status = "✅ Safe" if is_safe else "❌ High Risk"
                
                st.markdown(f"<div style='text-align:center; font-size:1.2rem; font-weight:bold'>{risk_status}</div>", unsafe_allow_html=True)

        st.divider()

        # 3. Audience Wallet (Buying Power)
        st.subheader("💰 Buying Power")
        wallet_cols = st.columns(len(profiles))
        for i, p in enumerate(profiles):
             with wallet_cols[i]:
                latest_run = p['history'][0] if p['history'] else None
                wallet_verdict = "N/A"
                if latest_run and latest_run.report_json:
                     wallet = latest_run.report_json.get('audience_dna', {}).get('spending_power', {})
                     wallet_verdict = wallet.get('verdict', 'Moderate')
                
                st.markdown(f"<div style='text-align:center'>{wallet_verdict}</div>", unsafe_allow_html=True)

        st.divider()

        # 4. Decision Actions
        act_cols = st.columns(len(profiles))
        for i, p in enumerate(profiles):
            with act_cols[i]:
                if st.button(f"🏆 Pick {p['identity'].name}", key=f"pick_{p['identity'].id}", use_container_width=True):
                    st.balloons()
                    st.toast(f"Recommended {p['identity'].name}!")
