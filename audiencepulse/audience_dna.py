"""
Audience DNA Profiler - Spending Power & Technical Literacy Analysis

For agencies deciding where to spend sponsorship budget:
- Is this audience rich or budget-conscious?
- Are they technical experts or casual consumers?
- What buyer personas dominate?
"""

import re
from typing import List, Dict, Any
from collections import Counter


# ============================================
# SPENDING POWER KEYWORDS
# ============================================

SPENDING_KEYWORDS = {
    'premium': [
        'worth it', 'worth every', 'take my money', 'shut up and take',
        'ordered', 'just bought', 'buying this', 'purchased',
        'quality over', 'invest in', 'premium', 'flagship',
        'no regrets', 'love it', 'best purchase', 'amazing quality'
    ],
    'budget': [
        'too expensive', 'overpriced', 'not worth',
        'cheaper', 'budget', 'affordable', 'value for money',
        'sale', 'discount', 'deal', 'coupon', 'promo',
        'alternative', 'vs', 'compared to', "can't afford",
        'wait for price drop', 'redmi', 'poco', 'realme'
    ]
}


# ============================================
# TECHNICAL LITERACY KEYWORDS
# ============================================

LITERACY_KEYWORDS = {
    'expert': [
        'bitrate', 'frequency response', 'codec', 'latency',
        'sensor size', 'aperture', 'iso', 'dynamic range',
        'refresh rate', 'response time', 'polling rate',
        'driver', 'dac', 'amp', 'ohm', 'impedance',
        'specs', 'benchmark', 'teardown', 'calibration',
        'soundstage', 'imaging', 'separation', 'distortion',
        'sample rate', 'bit depth', 'lossless', 'flac'
    ],
    'casual': [
        'looks cool', 'looks nice', 'pretty', 'beautiful',
        'color', 'design', 'aesthetic', 'vibe', 'fire',
        'goat', 'sick', 'dope', 'lit', 'clean',
        'love it', 'hate it', 'nice', 'good',
        'first', 'lol', 'lmao', 'haha'
    ]
}


# ============================================
# BUYER PERSONAS
# ============================================

PERSONA_PATTERNS = {
    'spec_nerd': {
        'keywords': ['specs', 'benchmark', 'vs', 'compared', 'which is better', 'technical'],
        'description': 'Deep research before buying, compares everything'
    },
    'premium_buyer': {
        'keywords': ['worth it', 'quality', 'best', 'flagship', 'premium', 'pro'],
        'description': 'Values quality over price, buys top-tier'
    },
    'apple_loyalist': {
        'keywords': ['apple', 'iphone', 'macbook', 'airpods', 'ecosystem'],
        'description': 'Prefers Apple ecosystem'
    },
    'budget_hunter': {
        'keywords': ['cheap', 'budget', 'value', 'deal', 'discount', 'alternative'],
        'description': 'Price-conscious, always looking for deals'
    },
    'early_adopter': {
        'keywords': ['new', 'latest', 'launch', 'first', 'pre-order', 'day one'],
        'description': 'Wants newest tech immediately'
    },
    'skeptic': {
        'keywords': ['overhyped', 'not worth', 'sponsored', 'paid', 'marketing'],
        'description': 'Distrusts marketing, needs convincing'
    }
}


# ============================================
# ANALYSIS FUNCTIONS
# ============================================

def analyze_spending_power(comments: List[Dict]) -> Dict[str, Any]:
    """
    Analyze audience spending power.
    
    Returns:
        {
            'premium_score': 0-100,
            'budget_score': 0-100,
            'verdict': 'HIGH' | 'MEDIUM' | 'LOW',
            'premium_signals': [...],
            'budget_signals': [...]
        }
    """
    premium_count = 0
    budget_count = 0
    premium_examples = []
    budget_examples = []
    
    for comment in comments:
        text = comment.get('text', '').lower() if isinstance(comment, dict) else str(comment).lower()
        
        # Check premium signals
        for keyword in SPENDING_KEYWORDS['premium']:
            if keyword in text:
                premium_count += 1
                if len(premium_examples) < 3:
                    premium_examples.append(text[:100])
                break
        
        # Check budget signals
        for keyword in SPENDING_KEYWORDS['budget']:
            if keyword in text:
                budget_count += 1
                if len(budget_examples) < 3:
                    budget_examples.append(text[:100])
                break
    
    total = premium_count + budget_count
    if total == 0:
        total = 1  # Avoid division by zero
    
    premium_score = int((premium_count / total) * 100) if total > 0 else 50
    budget_score = int((budget_count / total) * 100) if total > 0 else 50
    
    # Determine verdict
    if premium_score > 60:
        verdict = 'HIGH'
    elif premium_score > 40:
        verdict = 'MEDIUM'
    else:
        verdict = 'LOW'
    
    return {
        'premium_score': premium_score,
        'budget_score': budget_score,
        'verdict': verdict,
        'premium_signals': premium_count,
        'budget_signals': budget_count,
        'premium_examples': premium_examples,
        'budget_examples': budget_examples
    }


def analyze_tech_literacy(comments: List[Dict]) -> Dict[str, Any]:
    """
    Analyze audience technical literacy.
    
    Returns:
        {
            'expert_score': 0-100,
            'casual_score': 0-100,
            'verdict': 'EXPERT' | 'ENTHUSIAST' | 'CASUAL',
            'technical_terms': [...]
        }
    """
    expert_count = 0
    casual_count = 0
    technical_terms_found = []
    
    for comment in comments:
        text = comment.get('text', '').lower() if isinstance(comment, dict) else str(comment).lower()
        
        # Check expert signals
        for keyword in LITERACY_KEYWORDS['expert']:
            if keyword in text:
                expert_count += 1
                if keyword not in technical_terms_found:
                    technical_terms_found.append(keyword)
                break
        
        # Check casual signals
        for keyword in LITERACY_KEYWORDS['casual']:
            if keyword in text:
                casual_count += 1
                break
    
    total = expert_count + casual_count
    if total == 0:
        total = 1
    
    expert_score = int((expert_count / total) * 100)
    casual_score = int((casual_count / total) * 100)
    
    # Determine verdict
    if expert_score > 60:
        verdict = 'EXPERT'
    elif expert_score > 30:
        verdict = 'ENTHUSIAST'
    else:
        verdict = 'CASUAL'
    
    return {
        'expert_score': expert_score,
        'casual_score': casual_score,
        'verdict': verdict,
        'expert_signals': expert_count,
        'casual_signals': casual_count,
        'technical_terms': technical_terms_found[:10]
    }


def detect_personas(comments: List[Dict]) -> Dict[str, Any]:
    """
    Detect dominant buyer personas.
    
    Returns:
        {
            'personas': [{'name': str, 'percentage': int, 'description': str}],
            'dominant': str
        }
    """
    persona_counts = Counter()
    
    for comment in comments:
        text = comment.get('text', '').lower() if isinstance(comment, dict) else str(comment).lower()
        
        for persona, config in PERSONA_PATTERNS.items():
            for keyword in config['keywords']:
                if keyword in text:
                    persona_counts[persona] += 1
                    break
    
    total = sum(persona_counts.values()) or 1
    
    personas = []
    for persona, count in persona_counts.most_common(5):
        personas.append({
            'name': persona.replace('_', ' ').title(),
            'percentage': int((count / total) * 100),
            'count': count,
            'description': PERSONA_PATTERNS[persona]['description']
        })
    
    dominant = personas[0]['name'] if personas else 'General Consumer'
    
    return {
        'personas': personas,
        'dominant': dominant
    }


# ============================================
# FULL AUDIENCE DNA ANALYSIS
# ============================================

def analyze_audience_dna(comments: List[Dict]) -> Dict[str, Any]:
    """
    Complete Audience DNA analysis.
    
    Returns:
        {
            'spending_power': {...},
            'tech_literacy': {...},
            'personas': {...},
            'summary': str
        }
    """
    spending = analyze_spending_power(comments)
    literacy = analyze_tech_literacy(comments)
    personas = detect_personas(comments)
    
    # FIX: Bind personas to spending power to avoid conflicting percentages
    # Recalculate persona percentages based on actual spending signals
    premium_ratio = spending['premium_score'] / 100
    budget_ratio = spending['budget_score'] / 100
    
    # Adjust persona percentages to align with spending power
    for persona in personas.get('personas', []):
        name_lower = persona['name'].lower()
        if 'premium' in name_lower or 'early adopter' in name_lower:
            # Premium-related personas capped by actual premium signals
            persona['percentage'] = min(persona['percentage'], spending['premium_score'] + 10)
        elif 'budget' in name_lower or 'hunter' in name_lower:
            # Budget-related personas capped by actual budget signals
            persona['percentage'] = min(persona['percentage'], spending['budget_score'] + 10)
    
    # Renormalize percentages to sum to ~100
    total_pct = sum(p['percentage'] for p in personas.get('personas', []))
    if total_pct > 0:
        for persona in personas.get('personas', []):
            persona['percentage'] = int((persona['percentage'] / total_pct) * 100)
    
    # Generate summary
    summary = (
        f"Wallet: {spending['verdict']} | "
        f"Tech: {literacy['verdict']} | "
        f"Dominant: {personas['dominant']}"
    )
    
    return {
        'spending_power': spending,
        'tech_literacy': literacy,
        'personas': personas,
        'summary': summary,
        'total_comments': len(comments)
    }


def get_audience_fit_score(dna: Dict, product_type: str = 'premium') -> int:
    """
    Calculate fit score based on audience DNA and product type.
    
    Args:
        dna: Audience DNA analysis result
        product_type: 'premium', 'mid_tier', or 'budget'
    
    Returns:
        Fit score 0-100
    """
    spending = dna.get('spending_power', {})
    literacy = dna.get('tech_literacy', {})
    
    if product_type == 'premium':
        # Premium products need high spending power + expert/enthusiast
        spending_weight = spending.get('premium_score', 50)
        literacy_weight = literacy.get('expert_score', 50)
        return int((spending_weight * 0.6) + (literacy_weight * 0.4))
    
    elif product_type == 'mid_tier':
        # Mid-tier needs balanced audience
        return int(50 + (spending.get('premium_score', 50) - 50) * 0.3)
    
    else:  # budget
        # Budget products need price-conscious audience
        return int(spending.get('budget_score', 50))


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
    ]
    
    result = analyze_audience_dna(test_comments)
    print(f"Summary: {result['summary']}")
    print(f"Spending Power: {result['spending_power']['verdict']} ({result['spending_power']['premium_score']}% premium)")
    print(f"Tech Literacy: {result['tech_literacy']['verdict']} ({result['tech_literacy']['expert_score']}% expert)")
    print(f"Top Personas: {[p['name'] for p in result['personas']['personas'][:3]]}")
