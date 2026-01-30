"""
Creator Audit - Agency Vetting Platform Orchestrator

Combines all analysis for sponsorship decisions:
1. Audience DNA (Spending + Literacy + Personas)
2. Brand Affinity (Which brands they trust)
3. Trust Score (Is creator seen as sellout?)
4. Semantic Clusters (Pain points - kept from before)
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from .audience_dna import analyze_audience_dna, get_audience_fit_score
from .brand_affinity import analyze_brand_affinity
from .trust_score import get_community_health
from .semantic_cluster import semantic_cluster_analysis, get_top_clusters
from .context_mapper import map_comments_to_context


# ============================================
# CREATOR FIT CALCULATION
# ============================================

def calculate_creator_fit(
    dna: Dict,
    brand_affinity: Dict,
    community_health: Dict,
    product_type: str = 'premium'
) -> Dict[str, Any]:
    """
    Calculate overall creator-product fit score.
    
    Args:
        dna: Audience DNA analysis
        brand_affinity: Brand affinity analysis
        community_health: Trust and toxicity analysis
        product_type: 'premium', 'mid_tier', or 'budget'
    
    Returns:
        {
            'score': 0-100,
            'grade': 'A+' to 'F',
            'verdict': str,
            'failure_reason': str,
            'breakdown': {...}
        }
    """
    # Component scores
    spending_score = dna.get('spending_power', {}).get('premium_score', 50)
    budget_score = dna.get('spending_power', {}).get('budget_score', 50)
    literacy_score = dna.get('tech_literacy', {}).get('expert_score', 50)
    
    # Trust score with brand sentiment cap
    raw_trust = max(0, community_health.get('trust', {}).get('score_numeric', 0) + 50)
    
    # FIX: Cap trust if brand sentiment is universally low (toxic audience)
    brand_orbit = brand_affinity.get('brand_orbit', [])
    if brand_orbit:
        avg_brand_sentiment = sum(b.get('positive_pct', 50) for b in brand_orbit) / len(brand_orbit)
        if avg_brand_sentiment < 30:
            # Toxic audience - cap trust score
            raw_trust = min(raw_trust, 40)  # Cap at C level
    else:
        avg_brand_sentiment = 50
    
    trust_score = raw_trust
    
    # Brand tier alignment
    tier_dist = brand_affinity.get('tier_distribution', {})
    if product_type == 'premium':
        brand_alignment = tier_dist.get('premium', 33)
    elif product_type == 'budget':
        brand_alignment = tier_dist.get('budget', 33)
    else:
        brand_alignment = tier_dist.get('mid', 34)
    
    # Weighted average
    if product_type == 'premium':
        score = int(
            (spending_score * 0.35) +
            (trust_score * 0.25) +
            (brand_alignment * 0.25) +
            (literacy_score * 0.15)
        )
    else:
        score = int(
            (budget_score * 0.30) +
            (trust_score * 0.30) +
            (brand_alignment * 0.25) +
            (50 * 0.15)
        )
    
    # Clamp to 0-100
    score = max(0, min(100, score))
    
    # Identify failure reasons
    failure_reasons = []
    
    if product_type == 'premium':
        if spending_score < 40:
            failure_reasons.append(f"Low spending power ({spending_score}% premium buyers vs required 40%+)")
        if trust_score < 50:
            failure_reasons.append(f"Trust issues (score {trust_score}, audience skeptical)")
        if brand_alignment < 30:
            failure_reasons.append(f"Wrong brand tier (only {brand_alignment}% premium brand mentions)")
        if avg_brand_sentiment < 30:
            failure_reasons.append(f"Toxic audience (avg brand sentiment {avg_brand_sentiment:.0f}%)")
    else:
        if budget_score < 40:
            failure_reasons.append(f"Audience not price-conscious enough ({budget_score}%)")
    
    # Grade
    if score >= 85:
        grade = 'A+'
        verdict = '🎯 Excellent Fit - Highly recommend sponsorship'
    elif score >= 75:
        grade = 'A'
        verdict = '✅ Strong Fit - Good sponsorship opportunity'
    elif score >= 65:
        grade = 'B+'
        verdict = '👍 Good Fit - Consider sponsoring'
    elif score >= 55:
        grade = 'B'
        verdict = '📊 Moderate Fit - Proceed with defined expectations'
    elif score >= 45:
        grade = 'C'
        verdict = '⚠️ Weak Fit - May not be ideal match'
    else:
        grade = 'D'
        verdict = '❌ Poor Fit - Not recommended for this product'
    
    # Dynamic failure reason for executives
    if failure_reasons:
        failure_reason = "Failure: " + "; ".join(failure_reasons[:2])
    else:
        failure_reason = ""
    
    return {
        'score': score,
        'grade': grade,
        'verdict': verdict,
        'failure_reason': failure_reason,
        'product_type': product_type,
        'avg_brand_sentiment': round(avg_brand_sentiment, 1),
        'breakdown': {
            'spending_power': spending_score,
            'tech_literacy': literacy_score,
            'trust': trust_score,
            'brand_alignment': brand_alignment
        }
    }


# ============================================
# MAIN CREATOR AUDIT
# ============================================

def run_creator_audit(
    comments: List[Dict],
    video_metadata: Dict = None,
    product_category: str = 'premium',
    embedding_model: Any = None
) -> Dict[str, Any]:
    """
    Full Creator Audit for agency sponsorship decisions.
    
    Args:
        comments: List of comment dicts
        video_metadata: Video title, channel, etc.
        product_category: 'premium', 'mid_tier', or 'budget'
        embedding_model: Pre-loaded SentenceTransformer
    
    Returns:
        Complete audit report
    """
    start_time = datetime.now()
    
    print(f"\n🎯 CREATOR AUDIT: {len(comments)} comments")
    print("=" * 50)
    
    report = {
        'metadata': video_metadata or {},
        'total_comments': len(comments),
        'product_category': product_category,
        'audience_dna': {},
        'brand_affinity': {},
        'community_health': {},
        'pain_clusters': {},
        'creator_fit': {},
        'timing': {}
    }
    
    # 0. CONTEXT MAPPING (New Feature)
    transcript = video_metadata.get('transcript') if video_metadata else None
    
    if transcript:
        print(f"\n🧠 [0/4] CONTEXT MAPPING")
        # Enhance comments with context
        context_result = map_comments_to_context(comments, transcript)
        # Use context-aware comments for subsequent analysis
        comments = context_result.get('mapped_comments', comments)
        print(f"   {context_result['summary']}")
        report['context_stats'] = context_result['stats']
    else:
        print("\nℹ️ [0/4] CONTEXT MAPPING: No transcript available (skipping)")

    # 1. AUDIENCE DNA
    print("\n💰 [1/4] AUDIENCE DNA")
    report['audience_dna'] = analyze_audience_dna(comments)
    print(f"   {report['audience_dna']['summary']}")
    
    # 2. BRAND AFFINITY
    print("\n🏷️ [2/4] BRAND AFFINITY")
    report['brand_affinity'] = analyze_brand_affinity(comments)
    print(f"   Dominant Tier: {report['brand_affinity']['dominant_tier']}")
    print(f"   {report['brand_affinity']['recommendation']}")
    
    # 3. COMMUNITY HEALTH
    print("\n🛡️ [3/4] COMMUNITY HEALTH")
    report['community_health'] = get_community_health(comments)
    print(f"   Trust: {report['community_health']['trust']['score']}")
    print(f"   {report['community_health']['sponsor_recommendation']}")
    
    # 4. PAIN CLUSTERS (Keep semantic clustering)
    print("\n🔮 [4/4] PAIN CLUSTERS")
    cluster_result = semantic_cluster_analysis(comments, model=embedding_model)
    report['pain_clusters'] = {
        'cluster_count': cluster_result.get('cluster_count', 0),
        'top_clusters': get_top_clusters(cluster_result, n=5),
        'summary': cluster_result.get('summary', '')
    }
    
    # 5. CALCULATE FIT SCORE
    print("\n📊 CALCULATING CREATOR FIT...")
    report['creator_fit'] = calculate_creator_fit(
        report['audience_dna'],
        report['brand_affinity'],
        report['community_health'],
        product_category
    )
    print(f"   Score: {report['creator_fit']['score']}% ({report['creator_fit']['grade']})")
    print(f"   {report['creator_fit']['verdict']}")
    
    # Timing
    end_time = datetime.now()
    report['timing'] = {
        'duration_seconds': (end_time - start_time).total_seconds()
    }
    
    print(f"\n✅ AUDIT COMPLETE in {report['timing']['duration_seconds']:.1f}s")
    print("=" * 50)
    
    return report


def generate_agency_summary(report: Dict) -> str:
    """Generate executive summary for agency decision makers."""
    fit = report.get('creator_fit', {})
    dna = report.get('audience_dna', {})
    trust = report.get('community_health', {}).get('trust', {})
    brand = report.get('brand_affinity', {})
    
    return f"""
CREATOR AUDIT SUMMARY
=====================
Fit Score: {fit.get('score', 0)}% ({fit.get('grade', 'N/A')})
{fit.get('verdict', '')}

AUDIENCE PROFILE
• Wallet: {dna.get('spending_power', {}).get('verdict', 'Unknown')} ({dna.get('spending_power', {}).get('premium_score', 0)}% premium)
• Tech Level: {dna.get('tech_literacy', {}).get('verdict', 'Unknown')}
• Top Persona: {dna.get('personas', {}).get('dominant', 'Unknown')}

BRAND AFFINITY
• Dominant Tier: {brand.get('dominant_tier', 'Unknown').title()}
• {brand.get('recommendation', '')}

TRUST CHECK
• Score: {trust.get('score', 'N/A')}
• {trust.get('verdict', '')}
"""


if __name__ == "__main__":
    # Test
    test_comments = [
        {"text": "This is worth every penny! Best purchase I made."},
        {"text": "Too expensive, waiting for a sale"},
        {"text": "What's the frequency response on these?"},
        {"text": "Looks so clean and fire 🔥"},
        {"text": "How does this compare to Sony in terms of bitrate?"},
        {"text": "Just ordered the flagship model!"},
        {"text": "Is there a budget alternative?"},
        {"text": "Honest review as always, trust this guy"},
        {"text": "Apple ecosystem is unmatched"},
        {"text": "Samsung just copied Apple again"},
    ]
    
    result = run_creator_audit(test_comments, product_category='premium')
    print("\n" + generate_agency_summary(result))
