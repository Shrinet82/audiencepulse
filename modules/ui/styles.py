def get_custom_css():
    return """
    <style>
        /* =========================================
           GLASSMORPHISM THEME - AUDIENCEPULSE 2.0
           ========================================= */
        
        /* 1. BACKGROUND & TYPOGRAPHY */
        .stApp {
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            background-attachment: fixed;
            font-family: 'Inter', sans-serif;
            color: #e0e0e0;
        }
        
        h1, h2, h3, h4 {
            color: #ffffff !important;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        
        .stMarkdown p {
            color: #cbd5e1 !important;
            line-height: 1.6;
        }
        
        /* 2. GLASS CARDS */
        .glass-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 24px;
            transition: transform 0.2s ease;
        }
        
        .glass-card:hover {
            border-color: rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
        }

        /* 3. HERO METRICS (Score Cards) */
        .metric-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
        }
        
        .big-score {
            font-size: 4.5rem;
            font-weight: 800;
            background: -webkit-linear-gradient(45deg, #00d4ff, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 30px rgba(0, 212, 255, 0.3);
            margin: 0;
            line-height: 1;
        }
        
        .score-label {
            text-transform: uppercase;
            letter-spacing: 2px;
            font-size: 0.8rem;
            color: #94a3b8;
            margin-top: 12px;
        }
        
        /* 4. TABS & NAVIGATION */
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
            background-color: transparent;
        }

        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: transparent;
            border-radius: 8px;
            color: #94a3b8;
            font-weight: 600;
            border: none;
            padding: 0 16px; 
            transition: all 0.2s;
        }

        .stTabs [data-baseweb="tab"]:hover {
            color: #ffffff;
            background: rgba(255, 255, 255, 0.05);
        }

        .stTabs [aria-selected="true"] {
            color: #00d4ff !important;
            background: rgba(0, 212, 255, 0.1) !important;
            border-bottom: 2px solid #00d4ff;
        }

        /* 5. COMPONENTS */
        /* Status Badges */
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .badge-premium { background: rgba(139, 92, 246, 0.2); color: #c4b5fd; border: 1px solid rgba(139, 92, 246, 0.4); }
        .badge-success { background: rgba(16, 185, 129, 0.2); color: #6ee7b7; border: 1px solid rgba(16, 185, 129, 0.4); }
        .badge-danger  { background: rgba(239, 68, 68, 0.2); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.4); }
        .badge-warning { background: rgba(245, 158, 11, 0.2); color: #fcd34d; border: 1px solid rgba(245, 158, 11, 0.4); }

        /* Hide Streamlit default elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Input Fields */
        .stTextInput > div > div > input {
            background-color: rgba(255, 255, 255, 0.05);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
        }
        
        .stTextArea > div > div > textarea {
            background-color: rgba(255, 255, 255, 0.05);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
        }
    </style>
    """
