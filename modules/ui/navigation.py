import streamlit as st
from modules.core.session import SessionManager

def render_sidebar():
    """Renders the global sidebar navigation."""
    
    with st.sidebar:
        # 1. Logo Heading
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h2 style="color: #fff; margin:0;">AUDIENCE<span style="color: #00d4ff;">PULSE</span></h2>
            <div style="color: #64748b; font-size: 0.8rem; letter-spacing: 1px;">AGENCY OS v2.1</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 2. User Profile
        user = SessionManager.get_user()
        if user:
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 8px; margin-bottom: 2rem; display: flex; align-items: center; gap: 10px;">
                <div style="background: #3b82f6; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center;">👤</div>
                <div>
                    <div style="font-weight: bold; font-size: 0.9rem;">{getattr(user, 'email', 'User')}</div>
                    <div style="font-size: 0.7rem; color: #94a3b8;">Standard Plan</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # 3. Navigation Links
        st.markdown("**APPS**")
        base_options = ["Campaign Manager", "Creator Audit", "Settings"]
        
        # Dynamic Option: If a creator is selected, show "Creator Profile"
        if SessionManager.get_selected_creator_id():
            base_options.insert(1, "Creator Profile")
            
        selected = st.radio("Go to", base_options, label_visibility="collapsed", key="nav_selection")
        
        # Auto-clear creator selection if user navigates away
        if selected != "Creator Profile" and SessionManager.get_selected_creator_id():
            # If they manually clicked away, clear the selection
            # We check if it changed this rerun to avoid clearing instantly
            pass 
        
        st.divider()
        
        # 4. Sign Out
        if st.button("Sign Out", use_container_width=True):
            SessionManager.set_user(None)
            st.session_state.clear()
            st.rerun()

        return selected
