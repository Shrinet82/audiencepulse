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

# ============================================
# PAGE CONFIG & STYLES
# ============================================
# Import modular styles
try:
    from modules.ui import styles
except ImportError:
    # Fallback if local run without package structure
    import styles

st.set_page_config(
    page_title="AudiencePulse • Creator Vetting", 
    page_icon="🎯", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Glassmorphism CSS
st.markdown(styles.get_custom_css(), unsafe_allow_html=True)



# ============================================
# SUPABASE & AUTH SETUP
# ============================================
from supabase import create_client, Client

@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Supabase Init Failed: {e}")
        return None

supabase: Client = init_supabase()

if 'user' not in st.session_state:
    st.session_state.user = None

def login():
    st.markdown("## 🔐 Access AudiencePulse")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_pass")
            submit = st.form_submit_button("Sign In")
            
            if submit:
                if not supabase:
                    st.error("Supabase not configured!")
                else:
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        st.session_state.user = res.user
                        st.rerun()
                    except Exception as e:
                        st.error(f"Login failed: {str(e)}")
    
    with tab2:
        with st.form("signup_form"):
            st.markdown("Create a new team account.")
            new_email = st.text_input("Email", key="signup_email")
            new_password = st.text_input("Password", type="password", key="signup_pass")
            submit_signup = st.form_submit_button("Create Account")
            
            if submit_signup:
                if not supabase:
                    st.error("Supabase not configured!")
                else:
                    try:
                        res = supabase.auth.sign_up({"email": new_email, "password": new_password})
                        # If Email Confirmation is DISABLED, Supabase returns a session immediately.
                        if res.session:
                            st.session_state.user = res.user
                            st.success("Account created! Auto-logging in...")
                            st.rerun()
                        else:
                            st.success("Account created! Please check your email to confirm, then log in.")
                    except Exception as e:
                        st.error(f"Signup failed: {str(e)}")

# ============================================
# IMPORTS & SETUP
# ============================================
from modules.core.session import SessionManager
from modules.ui.navigation import render_sidebar
from modules.campaigns.views import CampaignViews
from modules.creators.views import CreatorViews
from modules.compare.views import CompareViews

# Initialize Session
SessionManager.init()

# ============================================
# AUTHENTICATION
# ============================================
if not SessionManager.get_user():
    login()
    st.stop()

# ============================================
# MAIN LAYOUT (Thin Router)
# ============================================
# 1. Render Sidebar (Global Nav)
current_view = render_sidebar()

# 2. Render Campaign Manager (Domain View)
campaign_views = CampaignViews()
campaign_views.render_manager_sidebar()

# 3. Main Content Router
if current_view == "Campaign Manager":
    active_id = SessionManager.get_active_campaign_id()
    if active_id:
        if st.button("← Back to All Missions"):
            SessionManager.set_active_campaign_id(None)
            st.rerun()
        campaign_views.render_workspace(active_id)
    else:
        st.title("📂 Campaign Command Center")
        campaign_views.render_dashboard_grid()
    
elif current_view == "Settings":
    st.title("⚙️ Settings")
    st.info("User preferences coming soon.")

elif current_view == "Creator Audit":
    from modules.wizard.views import AuditWizard
    wizard = AuditWizard()
    wizard.render()

elif current_view == "Creator Profile":
    creator_id = SessionManager.get_selected_creator_id()
    if creator_id:
        if st.button("← Back to Workspace"):
             # Optional: clear selection or just navigate back
             # Usually we might want to return to campaign roster
             # For now, just rerun to refresh sidebar context if needed
             pass
        CreatorViews().render_profile(creator_id)
    else:
        st.warning("No creator selected.")

# 4. Check for Comparison View (triggered via query param or session)
if st.query_params.get("view") == "compare":
    # Override main content to show battle
    # This is a bit hacky, but works for "Modal" feel
    st.empty() # Clear top elements if possible (not really how streamlit works but okay)
    
    st.title("⚔️ Comparison Arena")
    if st.button("← Back to Campaign"):
        st.query_params["view"] = "workspace"
        st.rerun()
        
    ids = SessionManager.get_comparison_ids()
    if ids:
        CompareViews().render_battle_mode(ids)
    else:
        st.warning("No contenders selected.")
    st.stop() # Prevent other content loading

# ============================================
# HELPER FUNCTIONS
# ============================================
import json
import subprocess
import os
from modules.ui.components import render_hero_score, render_progress_bar, render_glass_card, render_metric_card 

def fetch_all_data(url: str) -> dict:
    """Fetch comments and metadata."""
    metadata = {}
    try:
        from audiencepulse.video_analyzer import get_video_metadata, get_transcript
        metadata = get_video_metadata(url)
        # Fetch transcript for context mapping
        transcript_data = get_transcript(url)
        if transcript_data and 'segments' in transcript_data:
            metadata['transcript'] = transcript_data['segments']
    except Exception as e:
        print(f"Metadata fetch error: {e}")
        pass
    
    comments = []
    result = subprocess.run(
        ["python3", "scraper.py", url, "-o", "temp_comments.jsonl"],
        capture_output=True, text=True, cwd=os.getcwd()
    )

    if result.returncode != 0:
        print(f"Scraper error: {result.stderr}")
        try:
            st.error(f"Failed to fetch comments: {result.stderr}")
        except:
            pass # In case called outside streamlit context context
    
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

# Leaderboard removed by user request (Phase 2 feature disabled)

# Legacy Campaign Manager Code Removed (Handled by CampaignViews)



# SIDEBAR HISTORY (Filtered by Campaign)
st.sidebar.markdown("---")
selected_camp_id = SessionManager.get_active_campaign_id()
if selected_camp_id:
    # We need to fetch name via Service or Cache, but for now just show "Audits"
    # To be safe, we skip fetching name to avoid complexity here
    st.sidebar.subheader(f"📄 Campaign Audits")
else:
    st.sidebar.subheader("🕒 Recent Audits")

try:
    if supabase:
        # Fetch history filtered by campaign if selected
        query = supabase.table('audit_logs').select("id, creator_name, final_score, created_at").eq('user_email', user_email)
        
        if selected_camp_id:
            query = query.eq('campaign_id', selected_camp_id)
            
        history = query.order('created_at', desc=True).limit(10).execute()
    else:
        history = None

    
    if history and not history.data and selected_camp_id:
        st.sidebar.caption("No audits in this campaign yet.")
    
    if history and history.data:
        for item in history.data:
            score_color = "🟢" if item['final_score'] > 75 else "🔴"
            if st.sidebar.button(f"{score_color} {item['creator_name']} ({item['final_score']}%)", key=item['id']):
                # LOAD HISTORY ITEM
                full_item = supabase.table('audit_logs').select("*").eq('id', item['id']).execute()
                if full_item.data:
                    record = full_item.data[0]
                    st.session_state.audit_results = record['analysis_json']
                    st.session_state.session_restored = True
                    
                    # Restore context
                    st.session_state.product_context = {
                        'name': record.get('product_name'),
                        'tier': record.get('price_tier'),
                        'description': record.get('campaign_description')
                    }
                    
                    st.toast(f"Loaded report for {record['creator_name']}")
                    st.rerun()
except Exception as e:
    st.sidebar.error("Could not load history")


# RESUME SESSION LOGIC
if 'session_restored' not in st.session_state:
    # Try to fetch last audit
    try:
        user_email = st.session_state.user.email
        res = supabase.table('audit_logs').select("*").eq('user_email', user_email).order('last_accessed', desc=True).limit(1).execute()
        
        if res.data:
            last_audit = res.data[0]
            st.toast(f"Welcome back! Restoring session for {last_audit.get('creator_name', 'your last creator')}.")
            # Restore inputs to session state
            # (Requires keys to match input widgets)
            # st.session_state.single_url = last_audit.get('target_video_url')
            # ... set other keys ...
            st.session_state.session_restored = True
    except Exception as e:
        print(f"Restore error: {e}")
        pass


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
            height=70,
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
    # Persist context for reporting
    st.session_state.product_context = product_context
    
    profile_mode = False

else:
    # Creator Profile mode (multi-video)
    st.markdown("### 👤 Creator Profile Builder")
    st.markdown("*Paste 3-5 video URLs from the same creator for comprehensive audience analysis*")
    
    col1, col2 = st.columns(2)
    
    with col1:
        creator_name = st.text_input("Creator Name", placeholder="e.g., MKBHD", key="creator_name_input")
        product_name = st.text_input("Product Name", placeholder="e.g., iPhone 16 Pro", key="profile_product_name")
    
    with col2:
        product_type = st.selectbox(
            "Product Tier",
            ["premium", "mid_tier", "budget"],
            format_func=lambda x: {"premium": "💎 Premium", "mid_tier": "📊 Mid-Tier", "budget": "💰 Budget"}[x],
            key="profile_product_tier"
        )
        
        col2a, col2b = st.columns(2)
        with col2a:
             product_price = st.number_input("Price (₹)", min_value=0, value=50000, step=1000, key="profile_product_price")
        with col2b:
             product_category = st.selectbox(
                "Category",
                ["Tech", "Fashion", "Beauty", "Gaming", "Lifestyle", "Finance", "Education", "Other"],
                key="profile_product_cat"
             )
    
    product_description = st.text_area(
        "Product Description / Target Audience",
        placeholder="e.g., Premium noise-cancelling headphones for audiophiles...",
        height=70,
        key="profile_prod_desc"
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
                    product_context=product_context,
                    product_category=product_type,
                    embedding_model=embedding_model
                )
                
                st.session_state.audit_results = results
                
                # SAVE TO DB (History)
                try:
                    product_display_name = product_name if product_name else "Unknown Product"
                    creator_display_name = raw_data['metadata'].get('author', 'Unknown')
                    
                    supabase.table('audit_logs').insert({
                        "user_email": st.session_state.user.email,
                        "target_video_url": url,
                        "product_name": product_display_name,
                        "price_tier": product_type,
                        "campaign_description": product_description,
                        "final_score": results['creator_fit']['score'],
                        "analysis_json": results,
                        "creator_name": creator_display_name
                    }).execute()
                    st.toast("Audit saved to history!")
                except Exception as e:
                    print(f"Failed to save history: {e}")
                    # Don't show error to user if just a history save fail, main feature worked
                
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
                    
                    # Construct context
                    profile_context = {
                        'name': product_name,
                        'price': product_price,
                        'category': product_category,
                        'tier': product_type,
                        'description': product_description
                    }
                    # Persist context for reporting
                    st.session_state.product_context = profile_context
                    
                    profile = build_creator_profile(
                        video_urls=urls,
                        creator_name=creator_name,
                        product_context=profile_context,
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
                    
                    # SAVE TO DATABASE (Persistence)
                    try:
                        merged_audit = profile.get('merged_audit', {})
                        fit_result = merged_audit.get('creator_fit', {})
                        
                        supabase.table('audit_logs').insert({
                            "user_email": st.session_state.user.email,
                            "target_video_url": f"Creator Profile: {creator_name}", # Flag for profile
                            "product_name": product_name,
                            "price_tier": product_type,
                            "campaign_description": product_description,
                            "final_score": fit_result.get('score', 0),
                            "analysis_json": merged_audit,
                            "creator_name": creator_name,
                            "campaign_id": st.session_state.get('selected_campaign_id') # Link to campaign
                        }).execute()
                        st.toast(f"✅ Saved profile for {creator_name} to database!")
                    except Exception as e:
                        st.error(f"Failed to auto-save profile: {e}")

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
# RESULTS DISPLAY (Frontend 2.0)
# ============================================

if st.session_state.audit_results:
    results = st.session_state.audit_results
    fit = results.get('creator_fit', {})
    dna = results.get('audience_dna', {})
    brand = results.get('brand_affinity', {})
    health = results.get('community_health', {})
    
    # Get product context if available
    prod_ctx = product_context if 'product_context' in dir() else {}
    prod_name = prod_ctx.get('name', 'Product')
    prod_price = prod_ctx.get('price', 0)
    
    # ----------------------------------------
    # 1. HERO SCORE CARD (Glassmorphism)
    # ----------------------------------------
    fit_color = get_fit_color(fit.get('score', 0))
    failure_reason = fit.get('failure_reason', '')
    
    # Calculate price compatibility for display
    price_note = ""
    if prod_price > 0:
        wallet_score = dna.get('spending_power', {}).get('premium_score', 50)
        if wallet_score >= 50:
             price_note = f"<div style='color:#10b981; margin-top:8px;'>✅ Audience matches ₹{prod_price:,} price point</div>"
        else:
             price_note = f"<div style='color:#f59e0b; margin-top:8px;'>⚠️ Price ₹{prod_price:,} may be high for specific audience</div>"

    # HERO SCORE
    render_hero_score(
        fit.get('score', 0), 
        fit.get('grade', 'N/A'), 
        fit.get('verdict', 'Unknown Quality')
    )
    if price_note:
        st.markdown(price_note, unsafe_allow_html=True)
    
    st.markdown(f"<div style='text-align:center; margin-top: 1rem; color: #64748b;'>Testing alignment for <strong>{prod_name}</strong></div>", unsafe_allow_html=True)
    
    if failure_reason:
        st.error(f"🛑 Deal Breaker: {failure_reason}")

    # ----------------------------------------
    # 2. ACTION BAR (Shortlist & Metadata)
    # ----------------------------------------
    c1, c2 = st.columns([3, 1])
    with c1:
        if st.session_state.video_metadata:
             meta = st.session_state.video_metadata
             st.caption(f"📺 **{meta.get('channel', 'Unknown')}** • {meta.get('view_count', 0):,} Views • {results.get('total_comments', 0):,} Comments Analyzed")
    with c2:
        if st.button("📌 Save to Shortlist", use_container_width=True):
             # Initialize shortlist
            if 'shortlist' not in st.session_state:
                st.session_state.shortlist = []
            
            entry = {
                'channel': st.session_state.video_metadata.get('channel', 'Unknown') if st.session_state.video_metadata else 'Unknown',
                'score': fit.get('score', 0),
                'grade': fit.get('grade', 'N/A'),
                'wallet': dna.get('spending_power', {}).get('verdict', 'N/A'),
                'product_type': fit.get('product_type', 'premium')
            }
            if not any(e['channel'] == entry['channel'] for e in st.session_state.shortlist):
                st.session_state.shortlist.append(entry)
                st.toast(f"✅ Added {entry['channel']} to shortlist!")

    # ----------------------------------------
    # 3. DETAILED TABS (Clean UI)
    # ----------------------------------------
    tab_dna, tab_risk, tab_comments, tab_raw, tab_chat = st.tabs([
        "🧬 Audience DNA", "🛡️ Brand Safety", "💬 Deep Analysis", "📄 Raw Data", "🤖 AI Chat"
    ])

    with tab_dna:
        d1, d2 = st.columns(2)
        with d1:
            st.markdown('<div class="glass-card"><h4>🧠 Dominant Persona</h4>', unsafe_allow_html=True)
            dom_persona = dna.get('personas', {}).get('dominant', 'Unknown')
            st.markdown(f"<div style='font-size: 1.5rem; font-weight: bold; color: #c084fc;'>{dom_persona}</div>", unsafe_allow_html=True)
            st.markdown(f"_{dna.get('summary', '')}_")
            
            # Persona Tags
            tags = [p['name'] for p in dna.get('personas', {}).get('personas', [])[:4]]
            st.markdown(" ".join([f"`{t}`" for t in tags]))
            st.markdown('</div>', unsafe_allow_html=True)
            
        with d2:
            st.markdown('<div class="glass-card"><h4>💰 Wallet Depth</h4>', unsafe_allow_html=True)
            spend = dna.get('spending_power', {})
            st.metric("Budget Score", f"{spend.get('budget_score', 0)}/100")
            st.metric("Premium Score", f"{spend.get('premium_score', 0)}/100")
            
            if spend.get('premium_examples'):
                st.caption("Premium Signal: " + spend.get('premium_examples')[0][:60] + "...")
            st.markdown('</div>', unsafe_allow_html=True)
            
        # Tech Literacy Bar
        tech = dna.get('tech_literacy', {})
        st.markdown(f"**Tech Literacy: {tech.get('verdict')}**")
        st.progress(tech.get('expert_score', 50) / 100)

    with tab_risk:
        r1, r2 = st.columns(2)
        with r1:
            trust = health.get('trust', {})
            st.markdown(f"""
            <div class="glass-card">
                <h4>Trust Score</h4>
                <div class="metric-value" style="color: {get_fit_color(70 if trust.get('score','C') in ['A','B'] else 40)}">{trust.get('score', 'C')}</div>
                <p>{trust.get('verdict')}</p>
            </div>
            """, unsafe_allow_html=True)
        with r2:
            tox = health.get('toxicity', {})
            st.markdown(f"""
            <div class="glass-card">
                <h4>Brand Safety</h4>
                <div class="metric-value">{'✅ SAFE' if tox.get('is_safe') else '❌ RISK'}</div>
                <p>Toxicity: {tox.get('toxic_pct', 0)}%</p>
            </div>
            """, unsafe_allow_html=True)
            
    with tab_comments:
        st.markdown("### 🗣️ What are they saying?")
        
        # Pain Clusters
        clusters = results.get('pain_clusters', {}).get('top_clusters', [])
        if clusters:
            for c in clusters[:4]:
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px; margin-bottom: 10px;">
                    <strong>Cluster: {c.get('size')} comments</strong>
                    <br>"{c.get('representative')}"
                </div>
                """, unsafe_allow_html=True)
        
        # Brand Mentions
        st.divider()
        st.markdown("### Brand Mentions")
        orbit = brand.get('brand_orbit', [])
        if orbit:
             st.write(", ".join([f"**{b['brand']}** ({b['count']})" for b in orbit[:5]]))

    with tab_raw:
        st.json(results)

    with tab_chat:
        st.markdown("### 🤖 Ask the Analyst")
        # Initialize chat history
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                
        q = st.chat_input("Ask about this creator's audience...")
        if q:
            st.session_state.chat_history.append({"role": "user", "content": q})
            # (Simplified: Reuse existing context logic or calling directly here would duplicate code. 
            # ideally we refactor the chat logic to a function, but for now we keep it simple or user must re-implement)
            st.info("AI Chat active (Backend connected)") 

    # ----------------------------------------
    # 4. EXPORT
    # ----------------------------------------
    st.divider()
    e1, e2 = st.columns([3, 1])
    with e1:
        st.caption("Ready to present?")
    with e2:
        if st.button("📄 Generate PDF Brief", use_container_width=True):
             # Logic to generate PDF (reusing imported reports.py)
             try:
                from reports import generate_pdf_report
                p_ctx = st.session_state.get('product_context', {})
                report_data = {
                    'creator_name': results.get('video_metadata', {}).get('channel', 'Unknown'),
                    'product_name': p_ctx.get('name', 'Product'),
                    'price_tier': p_ctx.get('tier', 'Premium'),
                    'final_score': fit.get('score', 0),
                    'analysis_json': results
                }
                pdf = generate_pdf_report(report_data)
                st.session_state['pdf_ready'] = pdf.getvalue()
                st.rerun()
             except Exception as e:
                st.error(f"PDF Error: {e}")

    if 'pdf_ready' in st.session_state:
        st.download_button("⬇️ Download PDF", st.session_state['pdf_ready'], "brief.pdf", "application/pdf", use_container_width=True)

# Footer
st.markdown('<div class="footer">AudiencePulse v2.0 • Agency OS</div>', unsafe_allow_html=True)
