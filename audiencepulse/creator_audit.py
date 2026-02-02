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
    product_context: Dict = None,
    product_type: str = 'premium', # Deprecated, used if context missing
    embedding_model: Any = None
) -> Dict[str, Any]:
    """
    Calculate RELATIVE creator-product fit score.
    Scores are based on how well the audience matches THIS specific product.
    
    Weights:
    - Price Compatibility: 30%
    - Brand Compatibility: 30%
    - Category Relevance: 20%
    - Trust & Safety: 20%
    """
    if not product_context:
        # Fallback to legacy logic for backward compatibility
        return _calculate_legacy_fit(dna, brand_affinity, community_health, product_type)

    score_components = {
        'price_fit': 0,
        'brand_fit': 0,
        'category_fit': 0,
        'trust_score': 0
    }
    
    # 1. PRICE COMPATIBILITY (30%)
    price = product_context.get('price', 0)
    spending = dna.get('spending_power', {})
    premium_pct = spending.get('premium_score', 50)
    budget_pct = spending.get('budget_score', 50)
    
    if price > 50000: # High Ticket (₹50k+)
        # Strict requirement for premium audience
        price_fit = premium_pct
    elif price < 15000: # Budget (Under ₹15k)
        # Strict requirement for budget audience
        price_fit = budget_pct
    else: # Mid-Range
        # Best fit is balanced audience (e.g. 50% premium). 
        # Penalize if too skewed to budget OR too skewed to luxury (they might ignore mid-range)
        dist_from_center = abs(premium_pct - 50)
        price_fit = 100 - (dist_from_center * 1.5) # Map 50->100, 0/100 -> 25
    
    score_components['price_fit'] = max(0, min(100, price_fit))

    # 2. BRAND COMPATIBILITY (30%)
    target_brand = product_context.get('name', '').lower()
    brand_orbit = brand_affinity.get('brand_orbit', [])
    brand_mentions = [b for b in brand_orbit if b.get('brand', '').lower() in target_brand or target_brand in b.get('brand', '').lower()]
    
    if brand_mentions:
        # Brand exists in orbit! Use the sentiment.
        sentiment = brand_mentions[0].get('positive_pct', 50)
        if sentiment < 40:
            # VETO: They hate this brand.
            brand_fit = 0 
        else:
            brand_fit = sentiment
    else:
        # Fallback: Brand not found. Default to Neutral (50).
        # We cannot safely infer brand affinity from tier alone (False Positive Risk).
        # User Feedback: "Uncertainty should not result in a high score."
        brand_fit = 50
             
    score_components['brand_fit'] = brand_fit

    # 3. CATEGORY RELEVANCE (20%)
    target_cat = product_context.get('category', 'Tech').lower()
    # Simple heuristic checks
    if target_cat in ['tech', 'gaming', 'electronics']:
        # Use Tech Literacy as proxy for relevance
        cat_fit = dna.get('tech_literacy', {}).get('expert_score', 50)
    elif target_cat in ['fashion', 'beauty', 'lifestyle']:
        # Use simple "Casual" score as proxy for "Visual/Vibe" focus
        # In current DNA, 'casual' keywords include 'aesthetic', 'design'
        cat_fit = dna.get('tech_literacy', {}).get('casual_score', 50)
    else:
        # Generic category - assume neutral relevance
        cat_fit = 60
        
    score_components['category_fit'] = cat_fit
    
    # 3.5 DESCRIPTION PERSONA MATCHING (Boost)
    # Check if description semantically matches any detected personas (Vector Search)
    description = product_context.get('description', '').lower()
    personas = dna.get('personas', {}).get('personas', [])
    
    persona_boost = 0
    matched_personas = []
    
    if description and personas and embedding_model:
        try:
            # Encode description
            desc_embedding = embedding_model.encode(description, convert_to_tensor=True)
            
            from sentence_transformers import util
            
            for persona in personas:
                # Encode persona description + name for richer context
                p_text = f"{persona.get('name', '')}: {persona.get('description', '')}"
                p_embedding = embedding_model.encode(p_text, convert_to_tensor=True)
                
                # Calculate Cosine Similarity
                similarity = util.cos_sim(desc_embedding, p_embedding).item()
                
                # Semantic Match Threshold (0.4 is a strong signal for short text)
                if similarity > 0.4:  
                    # Boost based on how dominant this persona is
                    # Example: If 'Gamer' is 40% of audience, add 20 points
                    boost_val = min(20, int(persona.get('percentage', 0) / 2))
                    persona_boost += boost_val
                    matched_personas.append(f"{persona.get('name')} ({similarity:.2f})")
                    
        except Exception as e:
            print(f"Embedding error: {e}")
            pass
            
    elif description and personas and not embedding_model:
        # Fallback to string match if model missing (for tests/legacy)
        for persona in personas:
             p_name = persona.get('name', '').lower()
             if p_name in description:
                 boost_val = min(20, int(persona.get('percentage', 0) / 2))
                 persona_boost += boost_val
                 matched_personas.append(p_name)
    
    if persona_boost > 0:
        # Boost Category Fit but cap at 100
        score_components['category_fit'] = min(100, score_components['category_fit'] + persona_boost)
        # We'll note this in the breakdown for transparency
        score_components['persona_boost'] = persona_boost
        score_components['matched_personas'] = matched_personas

    # 4. TRUST & SAFETY (20%)
    trust = max(0, min(100, community_health.get('trust', {}).get('score_numeric', 0) + 50))
    
    # Safety Check
    toxicity_pct = community_health.get('toxicity', {}).get('toxicity_pct', 0)
    if toxicity_pct > 20:
        trust = max(0, trust - (toxicity_pct * 2)) # Heavy penalty for toxicity
        
    score_components['trust_score'] = trust

    # FINAL WEIGHTED SCORE
    final_score = (
        (score_components['price_fit'] * 0.30) +
        (score_components['brand_fit'] * 0.30) +
        (score_components['category_fit'] * 0.20) +
        (score_components['trust_score'] * 0.20)
    )
    
    final_score = int(max(0, min(100, final_score)))
    
    # Generate specific feedback
    failure_reasons = []

    # CRITICAL VETO: If Brand Fit is 0 (Hostile), you cannot pass.
    if score_components['brand_fit'] == 0:
        final_score = min(final_score, 35) # Force F grade
        failure_reasons.insert(0, f"⛔ CRITICAL: Audience is hostile towards {target_brand}")

    # Verdict Generation with Context
    if final_score >= 85:
        grade = 'A'
        verdict = f"🚀 Perfect Match for {target_brand}"
    elif final_score >= 70:
        grade = 'B'
        verdict = f"✅ Good Fit for {target_brand}"
    elif final_score >= 50:
        grade = 'C'
        verdict = "⚠️ Marginal Fit - Proceed with Caution"
    else:
        grade = 'F'
        verdict = f"❌ Incompatible with {target_brand}"

    # Generate specific feedback (Appended to Veto if exists)
    # failure_reasons initialized above
    if score_components['price_fit'] < 40:
        failure_reasons.append(f"Price Mismatch (Product too {'expensive' if price > 20000 else 'cheap'} for audience)")
    if score_components['brand_fit'] < 40:
        failure_reasons.append(f"Brand Incompatibility (Audience dislike or tier mismatch)")
    
    return {
        'score': final_score,
        'grade': grade,
        'verdict': verdict,
        'failure_reason': "; ".join(failure_reasons),
        'breakdown': score_components
    }

def _calculate_legacy_fit(dna, brand_affinity, community_health, product_type):
    """Legacy grading for backward compatibility."""
    # ... (Keep original logic minimal or just simple avg)
    return {'score': 50, 'grade': 'C', 'verdict': 'Legacy Mode', 'breakdown': {}}


# ============================================
# MAIN CREATOR AUDIT
# ============================================

def run_creator_audit(
    comments: List[Dict],
    video_metadata: Dict = None,
    product_context: Dict = None, # New
    product_category: str = 'premium', # Deprecated
    embedding_model: Any = None
) -> Dict[str, Any]:
    """
    Full Creator Audit for agency sponsorship decisions.
    
    Args:
        comments: List of comment dicts
        video_metadata: Video title, channel, etc.
        product_context: Full context (price, name, category)
        product_category: Fallback legacy category
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
        product_context=product_context,
        product_type=product_category,
        embedding_model=embedding_model
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
