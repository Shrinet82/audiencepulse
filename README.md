# AudiencePulse - Creator Vetting Platform

AI-powered YouTube audience analysis for agencies making sponsorship decisions.

## Features

- 🎯 **Creator Fit Score** - Instant match percentage for your product
- 💰 **Wallet Depth Analysis** - Budget-conscious vs premium buyers
- 🧠 **Tech Literacy Detection** - Casual vs expert audience
- 🏷️ **Brand Affinity Mapping** - What brands they trust
- 🛡️ **Trust Score** - Shill detector for safe sponsorships
- 📄 **PDF Strategy Deck** - Agency-ready deliverables
- 👤 **Multi-Video Profiles** - Aggregate audience DNA

## Quick Start (Docker)

```bash
# Pull from GitHub Container Registry
docker pull ghcr.io/YOUR_USERNAME/comment-analysis:latest

# Run with environment variable
docker run -d \
  -p 8501:8501 \
  -e GROQ_API_KEY=your_key_here \
  ghcr.io/YOUR_USERNAME/comment-analysis:latest
```

Open: http://localhost:8501

## Environment Variables

| Variable       | Required | Description                                               |
| -------------- | -------- | --------------------------------------------------------- |
| `GROQ_API_KEY` | Yes      | API key from [console.groq.com](https://console.groq.com) |

## Local Development

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/comment-analysis.git
cd comment-analysis

# Install dependencies
pip install -r requirements.txt

# Create .env
echo "GROQ_API_KEY=your_key" > .env

# Run
streamlit run app.py
```

## Deploy to Cloud

### Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template)

### Render

1. Connect GitHub repo
2. Set `GROQ_API_KEY` env var
3. Deploy

### Docker Compose

```yaml
version: "3.8"
services:
  audiencepulse:
    image: ghcr.io/YOUR_USERNAME/comment-analysis:latest
    ports:
      - "8501:8501"
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
```

## License

MIT
