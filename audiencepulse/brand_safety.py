"""
Brand Safety - Ad suitability scoring for marketing agencies.

Determines if a video is safe for brand sponsorship by analyzing:
1. Transcript content for unsafe topics
2. Comment section toxicity
"""

import re
from typing import Dict, List, Any, Optional


# Unsafe topics that make a video risky for brand sponsorship
UNSAFE_TOPICS = {
    'politics': [
        'election', 'politician', 'democrat', 'republican', 'liberal', 'conservative',
        'trump', 'biden', 'modi', 'bjp', 'congress', 'aap', 'vote', 'voting',
        'government', 'policy', 'political'
    ],
    'religion': [
        'muslim', 'christian', 'hindu', 'jewish', 'atheist', 'islam', 'church',
        'temple', 'mosque', 'god', 'jesus', 'allah', 'religious', 'faith'
    ],
    'violence': [
        'kill', 'murder', 'assault', 'attack', 'bomb', 'gun', 'weapon', 'war',
        'death', 'dead', 'shooting', 'violence', 'fight', 'blood'
    ],
    'adult_content': [
        'sex', 'porn', 'nude', 'xxx', 'adult', 'explicit', 'nsfw', 'onlyfans'
    ],
    'drugs_alcohol': [
        'drug', 'weed', 'marijuana', 'cocaine', 'heroin', 'alcohol', 'drunk',
        'high', 'stoned', 'beer', 'vodka', 'whiskey'
    ],
    'gambling': [
        'casino', 'bet', 'betting', 'gamble', 'gambling', 'poker', 'lottery'
    ],
    'hate_speech': [
        'hate', 'racist', 'discrimination', 'bigot', 'slur', 'offensive'
    ],
    'controversy': [
        'scam', 'fraud', 'lawsuit', 'scandal', 'controversy', 'exposed'
    ]
}

# Hostile patterns in comments
HOSTILE_PATTERNS = [
    r'\b(hate|stupid|idiot|moron|dumb|pathetic|trash|garbage|worst)\b',
    r'\b(f+u+c+k|sh+i+t|a+ss|damn|hell|crap)\b',
    r'\b(die|kill|hurt|destroy|attack)\b',
    r'!{3,}',  # Multiple exclamation marks = emotional
    r'[A-Z]{5,}',  # ALL CAPS = shouting
]


def check_unsafe_topics(text: str) -> Dict[str, List[str]]:
    """
    Scan text for unsafe topics.
    
    Returns:
        Dict of category -> matched keywords
    """
    text_lower = text.lower()
    found = {}
    
    for category, keywords in UNSAFE_TOPICS.items():
        matches = []
        for keyword in keywords:
            if keyword in text_lower:
                matches.append(keyword)
        if matches:
            found[category] = matches[:5]  # Limit to 5 examples
    
    return found


def calculate_toxicity_score(comments: List[Dict], sample_size: int = 100) -> Dict[str, Any]:
    """
    Calculate toxicity score from comment sample.
    
    Returns:
        {
            'hostile_count': int,
            'total_sampled': int,
            'toxicity_pct': float,
            'is_toxic': bool (>20% threshold),
            'examples': List[str]
        }
    """
    if not comments:
        return {
            'hostile_count': 0,
            'total_sampled': 0,
            'toxicity_pct': 0.0,
            'is_toxic': False,
            'examples': []
        }
    
    # Sample comments
    sample = comments[:sample_size]
    
    hostile_count = 0
    hostile_examples = []
    
    for comment in sample:
        text = comment.get('text', '') if isinstance(comment, dict) else str(comment)
        
        # Check against hostile patterns
        is_hostile = False
        for pattern in HOSTILE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                is_hostile = True
                break
        
        if is_hostile:
            hostile_count += 1
            if len(hostile_examples) < 5:
                hostile_examples.append(text[:100] + '...' if len(text) > 100 else text)
    
    toxicity_pct = (hostile_count / len(sample)) * 100 if sample else 0
    
    return {
        'hostile_count': hostile_count,
        'total_sampled': len(sample),
        'toxicity_pct': round(toxicity_pct, 1),
        'is_toxic': toxicity_pct > 20,  # >20% threshold
        'examples': hostile_examples
    }


def assess_brand_safety(
    transcript: str = "",
    comments: List[Dict] = None,
    title: str = "",
    description: str = ""
) -> Dict[str, Any]:
    """
    Full brand safety assessment.
    
    Returns:
        {
            'verdict': 'BRAND_SAFE' | 'CAUTION' | 'DO_NOT_SPONSOR',
            'score': 0-100 (100 = safest),
            'ad_suitability_flag': bool,
            'community_flag': bool,
            'unsafe_topics': {...},
            'toxicity': {...},
            'recommendations': [...]
        }
    """
    comments = comments or []
    
    # Check transcript + metadata for unsafe topics
    full_text = f"{title} {description} {transcript}"
    unsafe_topics = check_unsafe_topics(full_text)
    ad_suitability_flag = len(unsafe_topics) > 0
    
    # Check comment toxicity
    toxicity = calculate_toxicity_score(comments)
    community_flag = toxicity['is_toxic']
    
    # Calculate overall score
    # Start at 100, deduct for issues
    score = 100
    
    # Deduct for unsafe topics
    if 'violence' in unsafe_topics or 'hate_speech' in unsafe_topics:
        score -= 40
    if 'politics' in unsafe_topics:
        score -= 25
    if 'religion' in unsafe_topics:
        score -= 20
    if 'adult_content' in unsafe_topics:
        score -= 50
    if 'drugs_alcohol' in unsafe_topics:
        score -= 15
    if 'gambling' in unsafe_topics:
        score -= 15
    if 'controversy' in unsafe_topics:
        score -= 10
    
    # Deduct for toxicity
    score -= min(30, toxicity['toxicity_pct'])
    
    score = max(0, score)
    
    # Determine verdict
    if score >= 70 and not ad_suitability_flag and not community_flag:
        verdict = 'BRAND_SAFE'
    elif score >= 40:
        verdict = 'CAUTION'
    else:
        verdict = 'DO_NOT_SPONSOR'
    
    # Generate recommendations
    recommendations = []
    if ad_suitability_flag:
        topics = ', '.join(unsafe_topics.keys())
        recommendations.append(f"Content touches on sensitive topics: {topics}")
    if community_flag:
        recommendations.append(f"High comment toxicity ({toxicity['toxicity_pct']}%) - audience may be hostile")
    if not recommendations:
        recommendations.append("No major risks detected")
    
    return {
        'verdict': verdict,
        'score': round(score),
        'ad_suitability_flag': ad_suitability_flag,
        'community_flag': community_flag,
        'unsafe_topics': unsafe_topics,
        'toxicity': toxicity,
        'recommendations': recommendations
    }


def get_safety_badge(verdict: str) -> str:
    """Get emoji badge for verdict."""
    badges = {
        'BRAND_SAFE': '✅ Brand Safe',
        'CAUTION': '⚠️ Caution',
        'DO_NOT_SPONSOR': '🚫 Do Not Sponsor'
    }
    return badges.get(verdict, '❓ Unknown')


if __name__ == "__main__":
    # Test
    test_transcript = """
    This video discusses the recent government policy changes and their impact.
    Some politicians have been criticized for their stance on this issue.
    """
    
    test_comments = [
        {"text": "This is so stupid! The government is trash!"},
        {"text": "Great video, very informative"},
        {"text": "I hate these politicians"},
        {"text": "Thanks for explaining"},
        {"text": "What an idiot presenter"},
    ]
    
    result = assess_brand_safety(
        transcript=test_transcript,
        comments=test_comments,
        title="Political Analysis 2024"
    )
    
    import json
    print(json.dumps(result, indent=2))
    print(f"\nBadge: {get_safety_badge(result['verdict'])}")
