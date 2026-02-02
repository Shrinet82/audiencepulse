import sys
import os
import streamlit as st
from audiencepulse.creator_audit import calculate_creator_fit
from app import fetch_all_data

# 1. DEFINE CAMPAIGN CONTEXT (The Agency Brief)
CAMPAIGN_CONTEXT = {
    'name': "iPhone 15 Pro Max",
    'price': 159900,  # ~$1,900 USD
    'category': "Tech & Electronics",
    'tier': "Premium",
    'description': "Flagship smartphone targeting tech enthusiasts, creators, and professionals who value ecosystem integration and premium build quality."
}

# 2. THE VIDEO ASSET
VIDEO_URL = "https://youtu.be/rng_yUSwrgU?si=uy6Qmw3_lAw5Vebu"

def run_agency_audit():
    print(f"📋 AGENCY BRIEF: {CAMPAIGN_CONTEXT['name']}")
    print(f"💰 Budget Tier: {CAMPAIGN_CONTEXT['tier']} (₹{CAMPAIGN_CONTEXT['price']})")
    print(f"🎯 Target Description: {CAMPAIGN_CONTEXT['description']}")
    print("-" * 50)
    print(f"📺 ANALYZING CREATOR ASSET: {VIDEO_URL}")
    
    # A. FETCH DATA (Transcript + Comments + Metadata)
    print("   > Fetching Intelligence (API + Scraper)...")
    raw_data = fetch_all_data(VIDEO_URL)
    
    if not raw_data['comments']:
        print("❌ CRITICAL: No comments found. Analysis aborted.")
        return

    print(f"   > Metadata: {raw_data['metadata'].get('title')[:50]}...")
    print(f"   > Sample Size: {len(raw_data['comments'])} Comments")

    # B. RUN AUDIT ALGORITHM
    print("   > Running Audience DNA Logic...")
    # Note: passing None for embedding_model for now as we might not have it loaded in this lightweight script, 
    # relying on keyword/heuristic fallbacks in the audit logic if model is missing.
    # actually app.py loads it. Let's see if we can do without or if we need to mock it.
    # Ideally we load it, but it takes time. Let's try to run without first, usually there's a fallback.
    
    results = calculate_creator_fit(
        creator_data=raw_data['comments'],
        video_metadata=raw_data['metadata'],
        product_context=CAMPAIGN_CONTEXT,
        product_type=CAMPAIGN_CONTEXT['tier']
        # embedding_model=None (Implies keyword fallback)
    )

    # C. PRESENT FINDINGS
    fit = results['creator_fit']
    print("\n📊 AUDIT RESULTS")
    print("-" * 50)
    print(f"✅ FIT SCORE:  {fit['score']}/100")
    print(f"🏆 GRADE:      {fit['grade']}")
    print(f"📝 VERDICT:    {fit['verdict']}")
    print("-" * 50)
    
    print("🧠 AUDIENCE PSYCHOLOGY (The 'Why')")
    dna = results['audience_dna']
    print(f"   • Dominant Persona: {dna.get('dominant_persona', 'N/A')}")
    print(f"   • Sentiment: {dna.get('sentiment', {}).get('positive', 0)}% Positive")
    print(f"   • Pain Points detected: {len(dna.get('pain_clusters', []))}")
    
    print("\n💡 STRATEGIC ALIGNMENT")
    if fit['score'] > 75:
        print("   ✅ APPROVED: This creator is a Match.")
    else:
        print("   ⚠️ REVIEW NEEDED: Risks detected.")

if __name__ == "__main__":
    run_agency_audit()
