def get_custom_css():
    return """
    <style>
        /* =========================================
           AUDIENCEPULSE PREMIUM UI THEME
           ========================================= */
        
        /* 1. GLOBAL RESET & TYPOGRAPHY */
        .stApp {
            background: linear-gradient(135deg, #0b0f1a 0%, #141a2f 100%);
            background-attachment: fixed;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            color: #e0e0e0;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: #ffffff !important;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        
        p, .stMarkdown, .stText {
            color: #cbd5e1 !important;
        }

        /* 2. SIDEBAR - DARK GLASS */
        section[data-testid="stSidebar"] {
            background-color: rgba(11, 15, 26, 0.95);
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        /* Sidebar Text */
        section[data-testid="stSidebar"] .stMarkdown h1, h2, h3 {
             color: #94a3b8 !important;
        }

        /* 3. INPUTS - GLASS STYLE */
        .stTextInput input, 
        .stSelectbox div[data-baseweb="select"] > div, 
        .stTextArea textarea {
            background-color: rgba(255, 255, 255, 0.04) !important;
            color: white !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 8px !important;
        }
        
        .stTextInput input:focus, 
        .stTextArea textarea:focus {
            border-color: #00d4ff !important;
            background-color: rgba(255, 255, 255, 0.08) !important;
            box-shadow: 0 0 0 1px #00d4ff !important;
        }

        /* 4. BUTTONS - PREMIUM GRADIENT */
        div.stButton > button {
            background: linear-gradient(135deg, #00d4ff 0%, #3b82f6 100%);
            color: white !important;
            border: none;
            border-radius: 8px;
            padding: 0.6rem 1.2rem;
            font-weight: 600;
            letter-spacing: 0.5px;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
            transition: all 0.3s ease;
        }

        div.stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
        }
        
        div.stButton > button:active {
            transform: translateY(0px);
        }
        
        /* Secondary Buttons (Ghost) */
        div[data-testid="stForm"] div.stButton > button[kind="secondary"] {
             background: transparent;
             border: 1px solid rgba(255,255,255,0.1);
        }

        /* 5. GLASS CARDS & CONTAINERS */
        .glass-card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            transition: border-color 0.3s ease;
        }
        
        .glass-card:hover {
            border-color: rgba(0, 212, 255, 0.3);
        }

        /* 6. HERO METRICS */
        .big-score {
            font-size: 3.5rem;
            font-weight: 800;
            background: linear-gradient(to right, #00d4ff, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }

        /* 7. HIDE STREAMLIT CHROME */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* 8. TABS */
        .stTabs [data-baseweb="tab-list"] {
            gap: 20px;
            background-color: transparent;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 44px;
            border-radius: 6px;
            color: #64748b;
            font-weight: 600;
            background-color: transparent;
        }
        
        .stTabs [aria-selected="true"] {
            color: #38bdf8 !important;
            background: rgba(56, 189, 248, 0.1) !important;
        }
    </style>
    """
