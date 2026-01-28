"""
AudiencePulse - Creator Vetting Platform
For Agencies deciding where to spend $50K on sponsorship
"""

import streamlit as st
import subprocess
import json
import os
import re
import pandas as pd
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ============================================
# CACHED MODEL LOADING
# ============================================

@st.cache_resource
def load_embedding_model():
    """Load SentenceTransformer model ONCE."""
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer('all-MiniLM-L6-v2')
    except Exception as e:
        st.warning(f"Embedding model failed: {e}")
        return None

embedding_model = load_embedding_model()


# ============================================
# PAGE CONFIG
# ============================================

st.set_page_config(
    page_title="AudiencePulse • Creator Vetting", 
    page_icon="🎯", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Premium Dark Theme
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #0a0a1a 0%, #1a1a2e 100%);
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .block-container {
        padding-top: 2rem;
        max-width: 1200px;
    }
    
    /* Fit Score Card */
    .fit-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #0f2027 100%);
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        border: 2px solid;
        margin-bottom: 2rem;
    }
    
    .fit-score {
        font-size: 4rem;
        font-weight: 800;
    }
    
    .fit-grade {
        font-size: 1.5rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }
    
    .fit-verdict {
        color: #8892b0;
        margin-top: 1rem;
        font-size: 1.1rem;
    }
    
    /* Metric Cards */
    .metric-card {
        background: rgba(45, 74, 106, 0.3);
        border: 1px solid #2d4a6a;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #00d4ff;
    }
    
    .metric-label {
        color: #8892b0;
        font-size: 0.85rem;
        margin-top: 0.3rem;
    }
    
    /* Section Headers */
    .section-header {
        font-size: 1.3rem;
        font-weight: 700;
        color: #e6f1ff;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #2d4a6a;
    }
    
    /* Persona Tags */
    .persona-tag {
        display: inline-block;
        background: rgba(139, 92, 246, 0.2);
        border: 1px solid #8b5cf6;
        border-radius: 20px;
        padding: 0.3rem 1rem;
        margin: 0.2rem;
        color: #c4b5fd;
        font-size: 0.85rem;
    }
    
    /* Brand Card */
    .brand-card {
        background: rgba(16, 185, 129, 0.1);
        border-left: 4px solid #10b981;
        padding: 0.8rem 1rem;
        margin: 0.3rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    /* Progress Bars */
    .progress-container {
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
        height: 12px;
        margin: 0.5rem 0;
        overflow: hidden;
    }
    
    .progress-fill {
        height: 100%;
        border-radius: 10px;
        transition: width 0.5s ease;
    }
    
    /* Trust Grades */
    .trust-a { color: #10b981; }
    .trust-b { color: #f59e0b; }
    .trust-c { color: #ef4444; }
    
    /* Text colors */
    .stMarkdown, p, span, label { color: #ccd6f6 !important; }
    h1, h2, h3 { color: #e6f1ff !important; }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #4a5568;
        padding: 2rem;
        font-size: 0.8rem;
        border-top: 1px solid #2d4a6a;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)


# ============================================
# SESSION STATE
# ============================================

if 'audit_results' not in st.session_state:
    st.session_state.audit_results = None
if 'video_metadata' not in st.session_state:
    st.session_state.video_metadata = None
if 'raw_comments' not in st.session_state:
    st.session_state.raw_comments = []


# ============================================
# HELPER FUNCTIONS
# ============================================

def fetch_all_data(url: str) -> dict:
    """Fetch comments and metadata."""
    metadata = {}
    try:
        from audiencepulse.video_analyzer import get_video_metadata
        metadata = get_video_metadata(url)
    except:
        pass
    
    comments = []
    subprocess.run(
        ["python3", "scraper.py", url, "-o", "temp_comments.jsonl"],
        capture_output=True, text=True, cwd=os.getcwd()
    )
    
    if os.path.exists('temp_comments.jsonl'):
        with open('temp_comments.jsonl', 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    comments.append(json.loads(line))
                except:
                    pass
    
    return {'comments': comments, 'metadata': metadata}


def get_fit_color(score: int) -> str:
    if score >= 75:
        return '#10b981'  # Green
    elif score >= 55:
        return '#f59e0b'  # Yellow
    else:
        return '#ef4444'  # Red


# ============================================
# HEADER
# ============================================

st.markdown("""
<div style="text-align: center; padding: 2rem 0;">
    <h1 style="font-size: 2.5rem; background: linear-gradient(90deg, #00d4ff, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        🎯 AudiencePulse
    </h1>
    <p style="color: #8892b0; font-size: 1.1rem;">Creator Vetting Platform • For Agency Sponsorship Decisions</p>
</div>
""", unsafe_allow_html=True)


# ============================================
# INPUT SECTION - MODE SELECTOR
# ============================================

analysis_mode = st.radio(
    "Analysis Mode",
    ["🎬 Single Video", "👤 Creator Profile (Multi-Video)"],
    horizontal=True,
    label_visibility="collapsed"
)

if analysis_mode == "🎬 Single Video":
    # Original single video mode
    col_url, col_btn = st.columns([4, 1])
    
    with col_url:
        url = st.text_input("YouTube URL", placeholder="Paste creator video URL...", label_visibility="collapsed", key="single_url")
    
    with col_btn:
        audit_clicked = st.button("🔍 Audit Creator", type="primary", use_container_width=True)
    
    # Product Context Expander
    with st.expander("📦 Product Context (Optional - for precise matching)", expanded=False):
        st.markdown("*Define your product for accurate fit scoring*")
        
        col_name, col_price, col_cat = st.columns([2, 1, 1])
        
        with col_name:
            product_name = st.text_input("Product Name", placeholder="e.g., Sony WH-1000XM5", key="prod_name")
        
        with col_price:
            product_price = st.number_input("Price (₹)", min_value=0, max_value=10000000, value=0, step=1000, key="prod_price")
        
        with col_cat:
            product_category = st.selectbox(
                "Category",
                ["Tech", "Fashion", "Beauty", "Gaming", "Lifestyle", "Finance", "Education", "Other"],
                key="prod_cat"
            )
        
        product_description = st.text_area(
            "Product Description / Target Audience",
            placeholder="e.g., Premium noise-cancelling headphones for audiophiles and frequent travelers",
            height=60,
            key="prod_desc"
        )
    
    # Determine product type from price
    if product_price > 0:
        if product_price >= 50000:
            product_type = "premium"
        elif product_price >= 15000:
            product_type = "mid_tier"
        else:
            product_type = "budget"
    else:
        product_type = "premium"  # Default
    
    # Store product context
    product_context = {
        'name': product_name if 'product_name' in dir() else '',
        'price': product_price if 'product_price' in dir() else 0,
        'category': product_category if 'product_category' in dir() else '',
        'description': product_description if 'product_description' in dir() else '',
        'tier': product_type
    }
    
    profile_mode = False

else:
    # Creator Profile mode (multi-video)
    st.markdown("### 👤 Creator Profile Builder")
    st.markdown("*Paste 3-5 video URLs from the same creator for comprehensive audience analysis*")
    
    col_name, col_product = st.columns([2, 1])
    
    with col_name:
        creator_name = st.text_input("Creator Name", placeholder="e.g., MKBHD", key="creator_name_input")
    
    with col_product:
        product_type = st.selectbox(
            "Product Type",
            ["premium", "mid_tier", "budget"],
            format_func=lambda x: {"premium": "💎 Premium", "mid_tier": "📊 Mid-Tier", "budget": "💰 Budget"}[x],
            key="profile_product"
        )
    
    video_urls = st.text_area(
        "Video URLs (one per line)",
        placeholder="https://youtube.com/watch?v=abc123\nhttps://youtube.com/watch?v=def456\nhttps://youtube.com/watch?v=ghi789",
        height=120,
        key="multi_urls"
    )
    
    col_build, col_compare = st.columns(2)
    
    with col_build:
        build_profile_clicked = st.button("🚀 Build Creator Profile", type="primary", use_container_width=True)
    
    with col_compare:
        if 'creator_profiles' in st.session_state and len(st.session_state.creator_profiles) >= 2:
            compare_clicked = st.button("⚔️ Compare Creators", use_container_width=True)
        else:
            st.button("⚔️ Compare (need 2+ profiles)", disabled=True, use_container_width=True)
            compare_clicked = False
    
    audit_clicked = False
    url = None
    profile_mode = True


# ============================================
# AUDIT EXECUTION
# ============================================

if audit_clicked and url:
    if not os.getenv("GROQ_API_KEY"):
        st.error("Please set GROQ_API_KEY in .env file")
    else:
        with st.spinner("🎯 Running Creator Audit..."):
            progress = st.progress(0, text="Fetching video data...")
            raw_data = fetch_all_data(url)
            
            st.session_state.video_metadata = raw_data['metadata']
            st.session_state.raw_comments = raw_data['comments']
            
            progress.progress(30, text=f"Analyzing {len(raw_data['comments'])} comments...")
            
            try:
                from audiencepulse.creator_audit import run_creator_audit
                
                results = run_creator_audit(
                    comments=raw_data['comments'],
                    video_metadata=raw_data['metadata'],
                    product_category=product_type,
                    embedding_model=embedding_model
                )
                
                st.session_state.audit_results = results
                
                with open('creator_audit_report.json', 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                
                progress.progress(100, text="Audit Complete!")
                
            except Exception as e:
                st.error(f"Audit failed: {e}")
                import traceback
                st.code(traceback.format_exc())


# ============================================
# CREATOR PROFILE EXECUTION (Multi-Video)
# ============================================

if 'profile_mode' in dir() and profile_mode:
    
    # Initialize creator profiles storage
    if 'creator_profiles' not in st.session_state:
        st.session_state.creator_profiles = []
    
    # Build Profile
    if 'build_profile_clicked' in dir() and build_profile_clicked:
        urls = [u.strip() for u in video_urls.strip().split('\n') if u.strip()]
        
        if len(urls) < 1:
            st.error("Please paste at least 1 video URL")
        elif not creator_name:
            st.error("Please enter a creator name")
        else:
            with st.spinner(f"🚀 Building profile for {creator_name}..."):
                progress = st.progress(0, text="Initializing...")
                
                try:
                    from audiencepulse.creator_profile import build_creator_profile
                    
                    def update_progress(msg):
                        progress.progress(50, text=msg)
                    
                    profile = build_creator_profile(
                        video_urls=urls,
                        creator_name=creator_name,
                        product_category=product_type,
                        embedding_model=embedding_model,
                        progress_callback=update_progress
                    )
                    
                    # Store profile
                    # Remove existing profile for same creator
                    st.session_state.creator_profiles = [
                        p for p in st.session_state.creator_profiles 
                        if p.get('creator_name') != creator_name
                    ]
                    st.session_state.creator_profiles.append(profile)
                    
                    # Also set as current audit results for display
                    st.session_state.audit_results = profile.get('merged_audit', {})
                    st.session_state.current_profile = profile
                    
                    progress.progress(100, text="Profile Complete!")
                    st.success(f"✅ Built profile for {creator_name}: {profile['total_comments']} comments from {len(profile['videos_analyzed'])} videos")
                    
                except Exception as e:
                    st.error(f"Profile build failed: {e}")
                    import traceback
                    st.code(traceback.format_exc())
    
    # Compare Creators
    if 'compare_clicked' in dir() and compare_clicked:
        from audiencepulse.creator_profile import compare_creators
        
        profiles = st.session_state.creator_profiles
        if len(profiles) >= 2:
            comparison = compare_creators(profiles[0], profiles[1], product_type)
            st.session_state.comparison_result = comparison
    
    # Display saved profiles
    if st.session_state.creator_profiles:
        st.markdown("### 📊 Saved Creator Profiles")
        
        cols = st.columns(len(st.session_state.creator_profiles[:3]))
        for i, profile in enumerate(st.session_state.creator_profiles[:3]):
            scores = profile.get('aggregate_scores', {})
            with cols[i]:
                grade = scores.get('grade', 'N/A')
                fit_color = get_fit_color(scores.get('fit_score', 0))
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value" style="color: {fit_color};">{grade}</div>
                    <div class="metric-label">{profile.get('creator_name', 'Unknown')}</div>
                    <small style="color: #6b7280;">{profile.get('total_comments', 0):,} comments • {len(profile.get('videos_analyzed', []))} videos</small>
                </div>
                """, unsafe_allow_html=True)
        
        if st.button("🗑️ Clear All Profiles"):
            st.session_state.creator_profiles = []
            st.rerun()
    
    # Display Comparison Result
    if 'comparison_result' in st.session_state:
        comp = st.session_state.comparison_result
        st.markdown("### ⚔️ Creator Comparison")
        
        col_a, col_vs, col_b = st.columns([2, 1, 2])
        
        with col_a:
            a = comp['creator_a']
            st.markdown(f"""
            **{a['name']}**
            - Fit: {a['fit_score']}% ({a['grade']})
            - Wallet: {a['wallet']}
            - Trust: {a['trust']}
            - Brand Tier: {a['brand_tier']}
            """)
        
        with col_vs:
            st.markdown("<div style='text-align: center; font-size: 2rem;'>⚔️</div>", unsafe_allow_html=True)
        
        with col_b:
            b = comp['creator_b']
            st.markdown(f"""
            **{b['name']}**
            - Fit: {b['fit_score']}% ({b['grade']})
            - Wallet: {b['wallet']}
            - Trust: {b['trust']}
            - Brand Tier: {b['brand_tier']}
            """)
        
        winner_color = "#10b981" if comp['creator_a']['fit_score'] >= comp['creator_b']['fit_score'] else "#3b82f6"
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: rgba(16, 185, 129, 0.1); border-radius: 10px; margin-top: 1rem;">
            <strong style="color: {winner_color}; font-size: 1.2rem;">🏆 WINNER: {comp['winner']}</strong>
            <br><small>{' • '.join(comp['reasoning'])}</small>
        </div>
        """, unsafe_allow_html=True)


# ============================================
# RESULTS DISPLAY
# ============================================

if st.session_state.audit_results:
    results = st.session_state.audit_results
    fit = results.get('creator_fit', {})
    dna = results.get('audience_dna', {})
    brand = results.get('brand_affinity', {})
    health = results.get('community_health', {})
    
    # ========================================
    # FIT SCORE HERO
    # ========================================
    fit_color = get_fit_color(fit.get('score', 0))
    failure_reason = fit.get('failure_reason', '')
    
    # Get product context if available
    prod_ctx = product_context if 'product_context' in dir() else {}
    prod_name = prod_ctx.get('name', '')
    prod_price = prod_ctx.get('price', 0)
    
    # Product context display
    product_display = ""
    if prod_name or prod_price:
        price_str = f"₹{prod_price:,}" if prod_price else ""
        product_display = f'<div style="color: #8892b0; font-size: 0.9rem; margin-top: 0.5rem;">Testing for: <strong>{prod_name or "Your Product"}</strong> {price_str}</div>'
    
    # Price compatibility analysis
    price_compat = ""
    if prod_price > 0:
        wallet_score = dna.get('spending_power', {}).get('premium_score', 50)
        
        # Calculate recommended max price based on wallet depth
        if wallet_score >= 60:
            recommended_max = 100000
            compat_msg = "✅ Good fit for this price range"
            compat_color = "#10b981"
        elif wallet_score >= 40:
            recommended_max = 40000
            if prod_price > recommended_max:
                compat_msg = f"⚠️ Price may be too high (audience prefers under ₹{recommended_max:,})"
                compat_color = "#f59e0b"
            else:
                compat_msg = "✅ Price is within audience comfort zone"
                compat_color = "#10b981"
        else:
            recommended_max = 20000
            if prod_price > recommended_max:
                compat_msg = f"❌ Price too high (audience budget-conscious, prefers under ₹{recommended_max:,})"
                compat_color = "#ef4444"
            else:
                compat_msg = "✅ Price matches budget audience"
                compat_color = "#10b981"
        
        price_compat = f'<div style="color: {compat_color}; font-size: 0.9rem; margin-top: 0.5rem;">{compat_msg}</div>'
    
    st.markdown(f"""
    <div class="fit-card" style="border-color: {fit_color};">
        <div class="fit-score" style="color: {fit_color};">{fit.get('score', 0)}%</div>
        <div class="fit-grade" style="color: {fit_color};">Grade: {fit.get('grade', 'N/A')}</div>
        <div class="fit-verdict">{fit.get('verdict', '')}</div>
        {product_display}
        {price_compat}
        {'<div style="color: #ef4444; margin-top: 1rem; font-size: 0.95rem;">⚠️ ' + failure_reason + '</div>' if failure_reason else ''}
    </div>
    """, unsafe_allow_html=True)
    
    # Save to Shortlist button
    col_info, col_save = st.columns([3, 1])
    
    # Video info
    with col_info:
        if st.session_state.video_metadata:
            meta = st.session_state.video_metadata
            st.markdown(f"**Channel:** {meta.get('channel', 'Unknown')} • **Views:** {meta.get('view_count', 0):,} • **Comments Analyzed:** {results.get('total_comments', 0):,}")
    
    with col_save:
        if st.button("📌 Save to Shortlist", use_container_width=True):
            # Initialize shortlist
            if 'shortlist' not in st.session_state:
                st.session_state.shortlist = []
            
            # Add current result
            entry = {
                'channel': st.session_state.video_metadata.get('channel', 'Unknown') if st.session_state.video_metadata else 'Unknown',
                'score': fit.get('score', 0),
                'grade': fit.get('grade', 'N/A'),
                'wallet': dna.get('spending_power', {}).get('verdict', 'N/A'),
                'trust': health.get('trust', {}).get('score', 'N/A'),
                'tier': brand.get('dominant_tier', 'N/A'),
                'product_type': fit.get('product_type', 'premium')
            }
            
            # Avoid duplicates
            if not any(e['channel'] == entry['channel'] for e in st.session_state.shortlist):
                st.session_state.shortlist.append(entry)
                st.success(f"✅ Added {entry['channel']} to shortlist!")
            else:
                st.info("Already in shortlist")
    
    # ========================================
    # COMPARISON TABLE (if shortlist exists)
    # ========================================
    if 'shortlist' in st.session_state and len(st.session_state.shortlist) > 1:
        st.markdown('<div class="section-header">📊 Creator Comparison</div>', unsafe_allow_html=True)
        
        comparison_df = pd.DataFrame(st.session_state.shortlist)
        comparison_df = comparison_df.rename(columns={
            'channel': 'Creator',
            'score': 'Fit Score',
            'grade': 'Grade',
            'wallet': 'Wallet Depth',
            'trust': 'Trust',
            'tier': 'Brand Tier'
        })
        
        st.dataframe(comparison_df[['Creator', 'Fit Score', 'Grade', 'Wallet Depth', 'Trust', 'Brand Tier']], 
                     use_container_width=True, hide_index=True)
        
        if st.button("🗑️ Clear Shortlist"):
            st.session_state.shortlist = []
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ========================================
    # TABS
    # ========================================
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💰 Audience Psychology", "🏷️ Brand Affinity", "🛡️ Community Health", "🔮 Pain Clusters", "💬 Chat"
    ])
    
    # ----------------------------------------
    # TAB 1: AUDIENCE PSYCHOLOGY
    # ----------------------------------------
    with tab1:
        st.markdown('<div class="section-header">Audience DNA Profile</div>', unsafe_allow_html=True)
        
        spending = dna.get('spending_power', {})
        literacy = dna.get('tech_literacy', {})
        personas = dna.get('personas', {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Wallet Depth
            st.markdown("### 💰 Wallet Depth")
            premium_pct = spending.get('premium_score', 50)
            st.markdown(f"**{spending.get('verdict', 'MEDIUM')}** - {premium_pct}% premium buyers")
            
            st.markdown(f"""
            <div class="progress-container">
                <div class="progress-fill" style="width: {premium_pct}%; background: linear-gradient(90deg, #10b981, #3b82f6);"></div>
            </div>
            <small style="color: #6b7280;">Budget ← → Premium</small>
            """, unsafe_allow_html=True)
            
            if spending.get('premium_examples'):
                st.markdown("**Premium signals:**")
                for ex in spending.get('premium_examples', [])[:2]:
                    st.markdown(f"> _{ex[:80]}..._")
        
        with col2:
            # Tech Savviness
            st.markdown("### 🧠 Tech Savviness")
            expert_pct = literacy.get('expert_score', 50)
            st.markdown(f"**{literacy.get('verdict', 'ENTHUSIAST')}** - {expert_pct}% technical")
            
            st.markdown(f"""
            <div class="progress-container">
                <div class="progress-fill" style="width: {expert_pct}%; background: linear-gradient(90deg, #8b5cf6, #ec4899);"></div>
            </div>
            <small style="color: #6b7280;">Casual ← → Expert</small>
            """, unsafe_allow_html=True)
            
            if literacy.get('technical_terms'):
                st.markdown(f"**Terms detected:** {', '.join(literacy.get('technical_terms', [])[:5])}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Buyer Personas
        st.markdown("### 👥 Buyer Personas")
        persona_list = personas.get('personas', [])
        if persona_list:
            cols = st.columns(min(len(persona_list), 3))
            for i, persona in enumerate(persona_list[:3]):
                with cols[i]:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{persona.get('percentage', 0)}%</div>
                        <div class="metric-label">{persona.get('name', 'Unknown')}</div>
                        <small style="color: #6b7280;">{persona.get('description', '')[:40]}</small>
                    </div>
                    """, unsafe_allow_html=True)
    
    # ----------------------------------------
    # TAB 2: BRAND AFFINITY
    # ----------------------------------------
    with tab2:
        st.markdown('<div class="section-header">Brand Orbit</div>', unsafe_allow_html=True)
        
        tier_dist = brand.get('tier_distribution', {})
        
        # Tier distribution
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: #10b981;">{tier_dist.get('premium', 0)}%</div>
                <div class="metric-label">Premium Brands</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: #3b82f6;">{tier_dist.get('mid', 0)}%</div>
                <div class="metric-label">Mid-Tier</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: #f59e0b;">{tier_dist.get('budget', 0)}%</div>
                <div class="metric-label">Budget Brands</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown(f"**{brand.get('recommendation', '')}**")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Brand mentions
        st.markdown("### Top Brand Mentions")
        orbit = brand.get('brand_orbit', [])
        if orbit:
            for b in orbit[:8]:
                sentiment_color = '#10b981' if b.get('positive_pct', 50) >= 60 else '#f59e0b' if b.get('positive_pct', 50) >= 40 else '#ef4444'
                tier_badge = {'premium': '💎', 'mid': '📊', 'budget': '💰'}.get(b.get('tier', ''), '📦')
                
                st.markdown(f"""
                <div class="brand-card">
                    <strong>{tier_badge} {b.get('brand', 'Unknown')}</strong>
                    <span style="float: right; color: {sentiment_color};">{b.get('positive_pct', 50)}% positive</span>
                    <br><small style="color: #6b7280;">{b.get('count', 0)} mentions • {b.get('tier', 'unknown').title()} tier</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No brand mentions detected")
    
    # ----------------------------------------
    # TAB 3: COMMUNITY HEALTH
    # ----------------------------------------
    with tab3:
        st.markdown('<div class="section-header">Trust & Safety Check</div>', unsafe_allow_html=True)
        
        trust = health.get('trust', {})
        toxicity = health.get('toxicity', {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            trust_score = trust.get('score', 'B')
            trust_class = 'trust-a' if trust_score in ['A+', 'A'] else 'trust-b' if trust_score in ['B', 'C'] else 'trust-c'
            
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value {trust_class}">{trust_score}</div>
                <div class="metric-label">Trust Score</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"**{trust.get('verdict', '')}**")
            
            st.markdown(f"- Loyalty signals: {trust.get('loyalty_count', 0)}")
            st.markdown(f"- Skepticism signals: {trust.get('skepticism_count', 0)}")
        
        with col2:
            tox_level = toxicity.get('toxicity_level', 'LOW')
            tox_color = '#10b981' if tox_level == 'LOW' else '#f59e0b' if tox_level == 'MEDIUM' else '#ef4444'
            
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: {tox_color};">{tox_level}</div>
                <div class="metric-label">Toxicity Level</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"**Toxic comments:** {toxicity.get('toxic_pct', 0)}%")
            st.markdown(f"**Brand Safe:** {'✅ Yes' if toxicity.get('is_safe', True) else '❌ No'}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"### Recommendation\n\n{health.get('sponsor_recommendation', '')}")
    
    # ----------------------------------------
    # TAB 4: PAIN CLUSTERS
    # ----------------------------------------
    with tab4:
        st.markdown('<div class="section-header">Audience Pain Points</div>', unsafe_allow_html=True)
        
        clusters = results.get('pain_clusters', {})
        top_clusters = clusters.get('top_clusters', [])
        
        if top_clusters:
            st.markdown(f"**{clusters.get('cluster_count', 0)} distinct themes** found")
            
            for i, c in enumerate(top_clusters[:5]):
                st.markdown(f"""
                <div class="metric-card" style="text-align: left;">
                    <strong>Cluster #{i+1}</strong> ({c.get('size', 0)} comments)
                    <br><span style="color: #8892b0;">"{c.get('representative', '')[:120]}..."</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Not enough comments to form clusters")
    
    # ----------------------------------------
    # TAB 5: CHAT
    # ----------------------------------------
    with tab5:
        st.markdown('<div class="section-header">Ask Questions About This Analysis</div>', unsafe_allow_html=True)
        
        # Initialize chat history
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        # Display chat history
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
        
        # Chat input
        user_question = st.chat_input("Ask anything about the analysis...")
        
        if user_question:
            st.session_state.chat_history.append({"role": "user", "content": user_question})
            
            # Build context from results
            context = f"""
            Creator Audit Results:
            - Total Comments: {results.get('total_comments', 0)}
            - Fit Score: {fit.get('score', 0)}% (Grade: {fit.get('grade', 'N/A')})
            - Verdict: {fit.get('verdict', '')}
            - Failure Reason: {fit.get('failure_reason', 'None')}
            
            Audience DNA:
            - Wallet Depth: {dna.get('spending_power', {}).get('verdict', 'N/A')} ({dna.get('spending_power', {}).get('premium_score', 0)}% premium buyers)
            - Tech Level: {dna.get('tech_literacy', {}).get('verdict', 'N/A')} ({dna.get('tech_literacy', {}).get('expert_score', 0)}% expert)
            - Top Personas: {[p.get('name', '') for p in dna.get('personas', {}).get('personas', [])[:3]]}
            
            Brand Affinity:
            - Dominant Tier: {brand.get('dominant_tier', 'N/A')}
            - Top Brands: {[b.get('brand', '') for b in brand.get('brand_orbit', [])[:5]]}
            
            Community Health:
            - Trust Score: {health.get('trust', {}).get('score', 'N/A')}
            - {health.get('sponsor_recommendation', '')}
            """
            
            try:
                client = Groq(api_key=os.getenv("GROQ_API_KEY"))
                response = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": f"You are an expert agency analyst helping interpret creator audience data. Use this analysis to answer questions:\n\n{context}"},
                        {"role": "user", "content": user_question}
                    ],
                    model="llama-3.1-8b-instant",
                    temperature=0.5,
                    max_tokens=512
                )
                answer = response.choices[0].message.content
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
                st.rerun()
            except Exception as e:
                st.error(f"Chat error: {e}")
        
        # Clear chat button
        if st.session_state.chat_history:
            if st.button("🗑️ Clear Chat"):
                st.session_state.chat_history = []
                st.rerun()
    
    # ========================================
    # EXPORT
    # ========================================
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">📝 Export Strategy Deck</div>', unsafe_allow_html=True)
    
    # Agency input fields
    col_client, col_notes = st.columns([1, 2])
    
    with col_client:
        client_name = st.text_input("Client Name (White Label)", value="Agency Client", key="client_name")
    
    with col_notes:
        strategist_notes = st.text_area(
            "Strategist Notes", 
            value="", 
            placeholder="Add your analysis notes here. These will appear in the Strategy Deck.",
            height=80,
            key="strat_notes"
        )
    
    # Export buttons
    col_pdf, col_json, col_csv = st.columns(3)
    
    with col_pdf:
        if st.button("📄 Generate PDF Deck", type="primary", use_container_width=True):
            try:
                from audiencepulse.report_engine import generate_pdf_report, package_audit_for_pdf
                
                # Package data
                pdf_data = package_audit_for_pdf(results)
                
                # Generate PDF
                pdf_buffer = generate_pdf_report(pdf_data, client_name, strategist_notes)
                
                # Store in session for download
                st.session_state['pdf_buffer'] = pdf_buffer.getvalue()
                st.session_state['pdf_client'] = client_name
                st.success("✅ PDF Generated!")
                
            except Exception as e:
                st.error(f"PDF generation failed: {e}")
    
    # Download button (appears after generation)
    if 'pdf_buffer' in st.session_state:
        st.download_button(
            label="⬇️ Download Strategy Deck PDF",
            data=st.session_state['pdf_buffer'],
            file_name=f"Strategy_Audit_{st.session_state.get('pdf_client', 'Client')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    
    with col_json:
        if os.path.exists('creator_audit_report.json'):
            with open('creator_audit_report.json', 'rb') as f:
                st.download_button("📥 JSON Report", f, "creator_audit.json", "application/json", use_container_width=True)
    
    with col_csv:
        summary = {
            'Metric': ['Fit Score', 'Wallet Depth', 'Tech Level', 'Trust Score', 'Dominant Tier'],
            'Value': [
                f"{fit.get('score', 0)}% ({fit.get('grade', 'N/A')})",
                dna.get('spending_power', {}).get('verdict', 'N/A'),
                dna.get('tech_literacy', {}).get('verdict', 'N/A'),
                health.get('trust', {}).get('score', 'N/A'),
                brand.get('dominant_tier', 'N/A')
            ]
        }
        st.download_button("📥 Summary CSV", pd.DataFrame(summary).to_csv(index=False), "audit_summary.csv", "text/csv", use_container_width=True)


# Footer
st.markdown('<div class="footer">🎯 AudiencePulse • Creator Vetting Platform for Agencies</div>', unsafe_allow_html=True)
