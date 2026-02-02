# 🧠 AudiencePulse: AI-Powered Creator Vetting

![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Python](https://img.shields.io/badge/python-3.10+-yellow.svg) ![Status](https://img.shields.io/badge/status-production-green.svg)

> **AudiencePulse** is an enterprise-grade SaaS platform for auditing, scoring, and comparing YouTube creators using advanced AI. It transforms raw comment data into actionable intelligence for influencer marketing campaigns.

---

## 🚀 Key Features

### 1. 🛡️ Creator Intelligence Profile

- **Trust Score**: 0-100 rating based on sentiment, spam analysis, and audience alignment.
- **Audience DNA**: Radar charts visualizing "Spending Power", "Tech Affinity", and "Trust".
- **Brand Safety**: Automatic detection of toxic content or controversy risk.

### 2. 📂 Campaign Command Center

- **Mission Workspaces**: Organize creators into campaigns (e.g., "Summer Tech Launch").
- **Battle Mode**: Head-to-head comparison of candidates with visual overlays.

### 3. 🤖 AI Pipeline

- **Smart Scraper**: Extracts comments and transcripts (headless browser).
- **Groq (LLaMA-3)**: High-speed semantic analysis of thousands of comments.
- **Vector Search**: Semantic similarity matching using local embeddings.

---

## 🛠️ Architecture

The project follows a strict **Domain-Driven Design (DDD)** pattern:

| Domain                  | Description                             |
| :---------------------- | :-------------------------------------- |
| **`modules/campaigns`** | Manages workspaces and rosters.         |
| **`modules/creators`**  | Core entity logic (profiles, scoring).  |
| **`modules/compare`**   | Comparison engine logic.                |
| **`modules/reports`**   | PDF generation and export logic.        |
| **`modules/core`**      | Shared utilities (Config, Session, DB). |

---

## ⚙️ Setup & Installation

### Prerequisites

- Python 3.10+
- [Supabase Account](https://supabase.com)
- [Groq API Key](https://groq.com)

### 1. Clone & Install

```bash
git clone https://github.com/Shrinet82/audiencepulse.git
cd audiencepulse
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure Secrets

Create `.streamlit/secrets.toml`:

```toml
[supabase]
url = "YOUR_SUPABASE_URL"
key = "YOUR_SUPABASE_ANON_KEY"

[youtube]
api_key = "YOUR_YOUTUBE_API_KEY"
```

Create `.env`:

```bash
GROQ_API_KEY=your_groq_key_here
```

### 3. Run Application

```bash
streamlit run app.py
```

Login with default credentials (if seeded) or sign up via the UI.

---

## 📸 Screenshots

|                            Dashboard                             |                      Intelligence Profile                      |
| :--------------------------------------------------------------: | :------------------------------------------------------------: |
| ![Dashboard](https://via.placeholder.com/400x200?text=Dashboard) | ![Radar](https://via.placeholder.com/400x200?text=Radar+Chart) |

---

## 🔮 Future Roadmap

- [ ] Stripe Integration for "Pro" tiers.
- [ ] Instagram/TikTok support.
- [ ] AI Agent for automated outreach.

---

## 🤝 Contributing

1. Fork the repo
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'feat: Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
