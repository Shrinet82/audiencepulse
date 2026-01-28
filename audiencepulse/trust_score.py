"""
Trust Score - Shill Detector

Determines if audience trusts the creator:
- HIGH TRUST: "Honest review" → Safe to sponsor
- LOW TRUST: "Paid shill" → DANGER: Don't sponsor
"""

import re
from typing import List, Dict, Any
from collections import Counter


# ============================================
# TRUST KEYWORDS
# ============================================

SKEPTICISM_KEYWORDS = [
    'paid review', 'paid promotion', 'sponsored', 'sponsorship',
    'scripted', 'bias', 'biased', 'sellout', 'sell out', 'sold out',
    'shill', 'shilling', 'ad', 'advertisement', 'promotion',
    'paid to say', 'paid partnership', 'undisclosed', 'fake',
    'bought', 'bribed', 'money grab', 'cash grab',
    "can't trust", 'lost trust', 'unsubscribed', 'clickbait'
]

LOYALTY_KEYWORDS = [
    'honest', 'honest review', 'trust', 'trusted', 'trustworthy',
    'real', 'genuine', 'authentic', 'unbiased', 'no bs',
    'always trust', 'best reviewer', 'reliable', 'credible',
    'love this channel', 'subscriber for years', 'never disappoints',
    'tells it like it is', 'no sugar coating', 'refreshing honesty'
]

TOXICITY_KEYWORDS = [
    'hate', 'stupid', 'idiot', 'moron', 'dumb', 'pathetic',
    'trash', 'garbage', 'worst', 'terrible', 'awful',
    'die', 'kys', 'racist', 'sexist', 'discrimination'
]


# ============================================
# ANALYSIS FUNCTIONS
# ============================================

def analyze_trust(comments: List[Dict]) -> Dict[str, Any]:
    """
    Calculate trust score for creator.
    
    Returns:
        {
            'score': 'A+' | 'A' | 'B' | 'C' | 'D' | 'F',
            'score_numeric': -100 to 100,
            'verdict': str,
            'skepticism_count': int,
            'loyalty_count': int,
            'skepticism_examples': [...],
            'loyalty_examples': [...]
        }
    """
    skepticism_count = 0
    loyalty_count = 0
    skepticism_examples = []
    loyalty_examples = []
    
    for comment in comments:
        text = comment.get('text', '').lower() if isinstance(comment, dict) else str(comment).lower()
        
        # Check skepticism
        for keyword in SKEPTICISM_KEYWORDS:
            if keyword in text:
                skepticism_count += 1
                if len(skepticism_examples) < 3:
                    skepticism_examples.append(text[:100])
                break
        
        # Check loyalty
        for keyword in LOYALTY_KEYWORDS:
            if keyword in text:
                loyalty_count += 1
                if len(loyalty_examples) < 3:
                    loyalty_examples.append(text[:100])
                break
    
    # Calculate score
    total = len(comments) or 1
    skepticism_pct = (skepticism_count / total) * 100
    loyalty_pct = (loyalty_count / total) * 100
    
    # Numeric score: -100 (all skepticism) to +100 (all loyalty)
    score_numeric = int(loyalty_pct - skepticism_pct)
    
    # Letter grade
    if score_numeric >= 20:
        score = 'A+'
        verdict = 'Highly Trusted - Audience is loyal and believes the creator'
    elif score_numeric >= 10:
        score = 'A'
        verdict = 'Trusted - Positive audience sentiment'
    elif score_numeric >= 0:
        score = 'B'
        verdict = 'Neutral - Balanced trust levels'
    elif score_numeric >= -10:
        score = 'C'
        verdict = 'Skeptical - Some audience members question authenticity'
    elif score_numeric >= -20:
        score = 'D'
        verdict = 'Low Trust - Significant skepticism detected'
    else:
        score = 'F'
        verdict = '⚠️ DANGER: Audience views creator as a sellout'
    
    return {
        'score': score,
        'score_numeric': score_numeric,
        'verdict': verdict,
        'skepticism_count': skepticism_count,
        'loyalty_count': loyalty_count,
        'skepticism_pct': round(skepticism_pct, 1),
        'loyalty_pct': round(loyalty_pct, 1),
        'skepticism_examples': skepticism_examples,
        'loyalty_examples': loyalty_examples
    }


def analyze_toxicity(comments: List[Dict]) -> Dict[str, Any]:
    """
    Analyze comment section toxicity for brand safety.
    
    Returns:
        {
            'toxicity_level': 'LOW' | 'MEDIUM' | 'HIGH',
            'toxic_count': int,
            'toxic_pct': float,
            'is_safe': bool
        }
    """
    toxic_count = 0
    
    for comment in comments:
        text = comment.get('text', '').lower() if isinstance(comment, dict) else str(comment).lower()
        
        for keyword in TOXICITY_KEYWORDS:
            if keyword in text:
                toxic_count += 1
                break
    
    total = len(comments) or 1
    toxic_pct = (toxic_count / total) * 100
    
    if toxic_pct < 5:
        toxicity_level = 'LOW'
        is_safe = True
    elif toxic_pct < 15:
        toxicity_level = 'MEDIUM'
        is_safe = True
    else:
        toxicity_level = 'HIGH'
        is_safe = False
    
    return {
        'toxicity_level': toxicity_level,
        'toxic_count': toxic_count,
        'toxic_pct': round(toxic_pct, 1),
        'is_safe': is_safe
    }


def get_community_health(comments: List[Dict]) -> Dict[str, Any]:
    """
    Full community health check.
    
    Returns:
        {
            'trust': {...},
            'toxicity': {...},
            'overall_health': 'HEALTHY' | 'CONCERNING' | 'UNHEALTHY',
            'sponsor_recommendation': str
        }
    """
    trust = analyze_trust(comments)
    toxicity = analyze_toxicity(comments)
    
    # Determine overall health
    if trust['score'] in ['A+', 'A'] and toxicity['is_safe']:
        overall_health = 'HEALTHY'
        sponsor_recommendation = '✅ Safe to sponsor - Loyal, clean community'
    elif trust['score'] in ['B', 'C'] and toxicity['is_safe']:
        overall_health = 'NEUTRAL'
        sponsor_recommendation = '📊 Proceed with caution - Monitor audience reaction'
    elif trust['score'] in ['D', 'F'] or not toxicity['is_safe']:
        overall_health = 'UNHEALTHY'
        sponsor_recommendation = '⚠️ HIGH RISK - Audience may reject sponsored content'
    else:
        overall_health = 'CONCERNING'
        sponsor_recommendation = '🤔 Mixed signals - Deeper analysis recommended'
    
    return {
        'trust': trust,
        'toxicity': toxicity,
        'overall_health': overall_health,
        'sponsor_recommendation': sponsor_recommendation
    }


if __name__ == "__main__":
    # Test
    test_comments = [
        {"text": "This guy is so honest, trust his reviews completely"},
        {"text": "Another paid promotion, lost all respect"},
        {"text": "Best reviewer on YouTube, never disappoints"},
        {"text": "Obviously scripted, can't trust anything"},
        {"text": "Great video, love the content!"},
        {"text": "Unbiased as always, thanks!"},
        {"text": "You're a sellout now"},
    ]
    
    result = get_community_health(test_comments)
    print(f"Trust Score: {result['trust']['score']} ({result['trust']['score_numeric']})")
    print(f"Toxicity: {result['toxicity']['toxicity_level']}")
    print(f"Health: {result['overall_health']}")
    print(f"Recommendation: {result['sponsor_recommendation']}")
