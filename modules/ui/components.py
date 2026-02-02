import streamlit as st

# ==========================================
# GLASSMORPHISM COMPONENT LIBRARY
# ==========================================

def render_glass_card(content: str, vibe: str = "neutral"):
    """
    Renders a glassmorphism card container.
    vibe: "neutral", "success", "warning", "danger" controls border color.
    """
    colors = {
        "neutral": "rgba(255, 255, 255, 0.1)",
        "success": "#10b981",
        "warning": "#f59e0b",
        "danger": "#ef4444",
        "neon": "#00d4ff"
    }
    border_color = colors.get(vibe, colors["neutral"])
    
    st.markdown(f"""
    <div class="glass-card" style="border-color: {border_color};">
        {content}
    </div>
    """, unsafe_allow_html=True)

def render_metric_card(label: str, value: str, subtext: str = "", vibe: str = "neutral"):
    """
    Renders a standard metric card.
    """
    colors = {
        "neutral": "#e2e8f0",
        "success": "#10b981",
        "warning": "#f59e0b",
        "danger": "#ef4444",
        "neon": "#00d4ff"
    }
    val_color = colors.get(vibe, colors["neutral"])
    
    html = f"""
    <div class="glass-card" style="padding: 1.5rem; text-align: center; margin-bottom: 1rem;">
        <div style="font-size: 2rem; font-weight: 700; color: {val_color}; margin-bottom: 0.5rem;">{value}</div>
        <div style="color: #94a3b8; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px;">{label}</div>
        {'<div style="color: #64748b; font-size: 0.8rem; margin-top: 0.5rem;">' + subtext + '</div>' if subtext else ''}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_hero_score(score: int, grade: str, verdict: str):
    """
    Renders the big hero score card.
    """
    # Color Logic
    if score >= 75: color = "#10b981"
    elif score >= 50: color = "#f59e0b"
    else: color = "#ef4444"
    
    html = f"""
    <div class="glass-card" style="text-align: center; padding: 3rem; border-image: linear-gradient(45deg, {color}, #3b82f6) 1;">
        <h4 style="color: #94a3b8; text-transform: uppercase; letter-spacing: 3px; margin-bottom: 1rem;">Strategic Fit Verdict</h4>
        <div class="big-score">{score}</div>
        <div style="font-size: 2rem; font-weight: 700; margin-top: 1rem; color: {color};">
            Grade {grade} • {verdict}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_progress_bar(label: str, percentage: int, left_label: str, right_label: str, color_gradient: str = "linear-gradient(90deg, #10b981, #3b82f6)"):
    """
    Renders a custom styled progress bar.
    """
    html = f"""
    <div style="margin-bottom: 1.5rem;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <strong style="color: #e2e8f0;">{label}</strong>
            <span style="color: #00d4ff;">{percentage}%</span>
        </div>
        <div class="progress-container">
            <div class="progress-fill" style="width: {percentage}%; background: {color_gradient};"></div>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #64748b;">
            <span>{left_label}</span>
            <span>{right_label}</span>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
