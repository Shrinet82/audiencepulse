"""
Brand Affinity Mapping - Who does this audience trust?

Clusters brand mentions to understand:
- Premium Tech Cluster (Sony, Apple, Bose) → Good for luxury
- Budget Accessories Cluster (Boat, Noise) → Wrong for premium
"""

import re
from typing import List, Dict, Any
from collections import Counter


# ============================================
# BRAND TIERS
# ============================================

BRAND_DATABASE = {
    # Premium Tier
    'apple': {'tier': 'premium', 'category': 'tech'},
    'sony': {'tier': 'premium', 'category': 'audio'},
    'bose': {'tier': 'premium', 'category': 'audio'},
    'sennheiser': {'tier': 'premium', 'category': 'audio'},
    'samsung': {'tier': 'premium', 'category': 'tech'},
    'bang & olufsen': {'tier': 'premium', 'category': 'audio'},
    'b&o': {'tier': 'premium', 'category': 'audio'},
    'leica': {'tier': 'premium', 'category': 'camera'},
    'hasselblad': {'tier': 'premium', 'category': 'camera'},
    'marshall': {'tier': 'premium', 'category': 'audio'},
    'dyson': {'tier': 'premium', 'category': 'appliance'},
    'tesla': {'tier': 'premium', 'category': 'auto'},
    'rolex': {'tier': 'premium', 'category': 'watch'},
    'omega': {'tier': 'premium', 'category': 'watch'},
    
    # Mid Tier
    'jbl': {'tier': 'mid', 'category': 'audio'},
    'anker': {'tier': 'mid', 'category': 'accessories'},
    'oneplus': {'tier': 'mid', 'category': 'phone'},
    'nothing': {'tier': 'mid', 'category': 'phone'},
    'pixel': {'tier': 'mid', 'category': 'phone'},
    'google': {'tier': 'mid', 'category': 'tech'},
    'logitech': {'tier': 'mid', 'category': 'peripherals'},
    'razer': {'tier': 'mid', 'category': 'gaming'},
    'corsair': {'tier': 'mid', 'category': 'gaming'},
    'skullcandy': {'tier': 'mid', 'category': 'audio'},
    'fossil': {'tier': 'mid', 'category': 'watch'},
    'garmin': {'tier': 'mid', 'category': 'wearable'},
    
    # Budget Tier
    'boat': {'tier': 'budget', 'category': 'audio'},
    'noise': {'tier': 'budget', 'category': 'wearable'},
    'fireboltt': {'tier': 'budget', 'category': 'wearable'},
    'ptron': {'tier': 'budget', 'category': 'audio'},
    'redmi': {'tier': 'budget', 'category': 'phone'},
    'poco': {'tier': 'budget', 'category': 'phone'},
    'realme': {'tier': 'budget', 'category': 'phone'},
    'mivi': {'tier': 'budget', 'category': 'audio'},
    'boult': {'tier': 'budget', 'category': 'audio'},
    'zebronics': {'tier': 'budget', 'category': 'electronics'},
    'amazfit': {'tier': 'budget', 'category': 'wearable'},
}


# ============================================
# SENTIMENT KEYWORDS
# ============================================

POSITIVE_CONTEXT = [
    'love', 'best', 'amazing', 'great', 'excellent', 'perfect',
    'better than', 'switched to', 'recommend', 'fan of', 'trust'
]

NEGATIVE_CONTEXT = [
    'hate', 'worst', 'terrible', 'sucks', 'trash', 'garbage',
    'overrated', 'never buy', 'avoid', 'disappointed', 'regret'
]


# ============================================
# BRAND EXTRACTION
# ============================================

def extract_brand_mentions(comments: List[Dict]) -> List[Dict[str, Any]]:
    """
    Extract brand mentions with sentiment context.
    
    Returns:
        List of {brand, tier, category, sentiment, text}
    """
    mentions = []
    
    for comment in comments:
        text = comment.get('text', '').lower() if isinstance(comment, dict) else str(comment).lower()
        
        for brand, info in BRAND_DATABASE.items():
            if brand in text:
                # Determine sentiment
                sentiment = 'neutral'
                for pos_word in POSITIVE_CONTEXT:
                    if pos_word in text:
                        sentiment = 'positive'
                        break
                if sentiment == 'neutral':
                    for neg_word in NEGATIVE_CONTEXT:
                        if neg_word in text:
                            sentiment = 'negative'
                            break
                
                mentions.append({
                    'brand': brand,
                    'tier': info['tier'],
                    'category': info['category'],
                    'sentiment': sentiment,
                    'text': text[:100]
                })
    
    return mentions


def analyze_brand_affinity(comments: List[Dict]) -> Dict[str, Any]:
    """
    Full brand affinity analysis.
    
    Returns:
        {
            'brand_orbit': [{brand, count, sentiment_pct, tier}],
            'tier_distribution': {premium: %, mid: %, budget: %},
            'dominant_tier': str,
            'category_focus': str,
            'recommendation': str
        }
    """
    mentions = extract_brand_mentions(comments)
    
    if not mentions:
        return {
            'brand_orbit': [],
            'tier_distribution': {'premium': 33, 'mid': 34, 'budget': 33},
            'dominant_tier': 'unknown',
            'category_focus': 'general',
            'recommendation': 'Not enough brand mentions to analyze',
            'total_mentions': 0
        }
    
    # Count brands
    brand_counts = Counter()
    brand_sentiment = {}
    tier_counts = Counter()
    category_counts = Counter()
    
    for mention in mentions:
        brand = mention['brand']
        brand_counts[brand] += 1
        tier_counts[mention['tier']] += 1
        category_counts[mention['category']] += 1
        
        if brand not in brand_sentiment:
            brand_sentiment[brand] = {'positive': 0, 'negative': 0, 'neutral': 0}
        brand_sentiment[brand][mention['sentiment']] += 1
    
    # Build brand orbit
    brand_orbit = []
    for brand, count in brand_counts.most_common(10):
        sentiment = brand_sentiment[brand]
        total = sum(sentiment.values())
        positive_pct = int((sentiment['positive'] / total) * 100) if total > 0 else 50
        
        brand_orbit.append({
            'brand': brand.title(),
            'count': count,
            'positive_pct': positive_pct,
            'tier': BRAND_DATABASE.get(brand, {}).get('tier', 'unknown')
        })
    
    # Tier distribution
    total_tiers = sum(tier_counts.values()) or 1
    tier_distribution = {
        'premium': int((tier_counts.get('premium', 0) / total_tiers) * 100),
        'mid': int((tier_counts.get('mid', 0) / total_tiers) * 100),
        'budget': int((tier_counts.get('budget', 0) / total_tiers) * 100)
    }
    
    # Dominant tier
    dominant_tier = max(tier_counts.items(), key=lambda x: x[1])[0] if tier_counts else 'unknown'
    
    # Category focus
    category_focus = max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else 'general'
    
    # Generate recommendation
    if dominant_tier == 'premium':
        recommendation = "✅ Premium audience - ideal for luxury/flagship products"
    elif dominant_tier == 'budget':
        recommendation = "⚠️ Budget-conscious audience - may resist premium pricing"
    else:
        recommendation = "📊 Mixed audience - mid-tier products may perform best"
    
    return {
        'brand_orbit': brand_orbit,
        'tier_distribution': tier_distribution,
        'dominant_tier': dominant_tier,
        'category_focus': category_focus,
        'recommendation': recommendation,
        'total_mentions': len(mentions)
    }


def get_competitor_insights(brand_affinity: Dict, your_brand: str) -> Dict[str, Any]:
    """
    Get competitive insights for a specific brand.
    """
    orbit = brand_affinity.get('brand_orbit', [])
    competitors = [b for b in orbit if b['brand'].lower() != your_brand.lower()]
    
    return {
        'top_competitors': competitors[:5],
        'your_brand_mentions': next(
            (b for b in orbit if b['brand'].lower() == your_brand.lower()), 
            {'count': 0, 'positive_pct': 0}
        )
    }


if __name__ == "__main__":
    # Test
    test_comments = [
        {"text": "This is way better than my old Sony headphones!"},
        {"text": "Apple ecosystem is unmatched"},
        {"text": "Boat is trash, should've bought JBL"},
        {"text": "Love my Sennheiser, best audio quality"},
        {"text": "Comparing this to Bose QC45"},
        {"text": "Redmi vs Realme which is better?"},
        {"text": "Samsung just copied Apple again"},
    ]
    
    result = analyze_brand_affinity(test_comments)
    print(f"Dominant Tier: {result['dominant_tier']}")
    print(f"Distribution: {result['tier_distribution']}")
    print(f"Recommendation: {result['recommendation']}")
    print("\nBrand Orbit:")
    for brand in result['brand_orbit'][:5]:
        print(f"  - {brand['brand']}: {brand['count']} mentions ({brand['positive_pct']}% positive)")
