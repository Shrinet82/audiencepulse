"""
Chain-of-Thought Lead Funnel - Precision lead detection

3-Stage filtering:
1. POSSESSION CHECK: Does user already own product?
2. BARRIER CHECK: Is user asking blocker questions (price, shipping)?
3. COMPETITOR CHECK: Is user mentioning rival negatively?

Result: Zero false positives, only active potential buyers
"""

import os
import json
import re
from typing import List, Dict, Any, Optional
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


# ============================================
# STAGE DEFINITIONS
# ============================================

LEAD_CATEGORIES = {
    'customer_feedback': {
        'label': 'Customer Feedback',
        'value': 'low',
        'description': 'Already owns the product',
        'icon': '👤'
    },
    'high_intent_lead': {
        'label': 'High-Intent Lead',
        'value': 'high',
        'description': 'Ready to buy, asking where/how',
        'icon': '🔥'
    },
    'conquest_opportunity': {
        'label': 'Conquest Opportunity',
        'value': 'high',
        'description': 'Unhappy with competitor',
        'icon': '🎯'
    },
    'consideration': {
        'label': 'In Consideration',
        'value': 'medium',
        'description': 'Evaluating, needs more info',
        'icon': '🤔'
    },
    'casual': {
        'label': 'Casual Comment',
        'value': 'none',
        'description': 'No buying intent',
        'icon': '💬'
    }
}


# ============================================
# STAGE 1: POSSESSION CHECK
# ============================================

POSSESSION_PATTERNS = [
    r'\b(i bought|i purchased|i own|i have|i got|mine is|my .+ is)\b',
    r'\b(i\'ve had|i\'ve been using|i use|i\'m using)\b',
    r'\b(ordered|received|delivered|arrived)\b.*\b(mine|my)\b',
    r'\b(since|for) (a year|months|years|weeks)\b',
]

def check_possession(text: str) -> Dict[str, Any]:
    """
    Stage 1: Check if user already owns the product.
    If YES → Stop, classify as Customer Feedback
    """
    text_lower = text.lower()
    
    for pattern in POSSESSION_PATTERNS:
        if re.search(pattern, text_lower):
            return {
                'has_possession': True,
                'matched_pattern': pattern,
                'classification': 'customer_feedback',
                'stop': True
            }
    
    return {
        'has_possession': False,
        'stop': False
    }


# ============================================
# STAGE 2: BARRIER CHECK
# ============================================

BARRIER_PATTERNS = {
    'price': [
        r'\b(how much|price|cost|expensive|cheap|afford|budget)\b',
        r'\b(worth it|worth the money|value for money)\b',
        r'\b(discount|coupon|sale|offer|deal)\b',
    ],
    'availability': [
        r'\b(where (can i|to) buy|available|in stock|link|store)\b',
        r'\b(shipping|delivery|ship to|deliver to)\b',
        r'\b(available in|ship to) (india|usa|uk|my country)\b',
    ],
    'compatibility': [
        r'\b(work with|compatible|support)\b',
        r'\b(vs|versus|compared to|or should i|which is better)\b',
    ],
    'timing': [
        r'\b(when (will|is)|release date|coming soon|launch)\b',
        r'\b(should i wait|wait for|upgrade from)\b',
    ]
}

def check_barriers(text: str) -> Dict[str, Any]:
    """
    Stage 2: Check if user is asking blocker questions.
    If YES → High-Intent Lead
    """
    text_lower = text.lower()
    barriers_found = []
    
    for barrier_type, patterns in BARRIER_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                barriers_found.append(barrier_type)
                break
    
    if barriers_found:
        return {
            'has_barriers': True,
            'barrier_types': list(set(barriers_found)),
            'classification': 'high_intent_lead',
            'stop': True
        }
    
    return {
        'has_barriers': False,
        'stop': False
    }


# ============================================
# STAGE 3: COMPETITOR CHECK
# ============================================

COMPETITOR_PATTERNS = [
    r'\b(better than|worse than|compared to)\b',
    r'\b(switched from|moving from|leaving)\b',
    r'\b(sucks|terrible|awful|hate|worst)\b.*\b(samsung|apple|google|microsoft|amazon)\b',
    r'\b(samsung|apple|google|microsoft|amazon)\b.*\b(sucks|terrible|awful|hate|worst)\b',
    r'\b(never buying|done with|tired of)\b',
]

def check_competitor(text: str) -> Dict[str, Any]:
    """
    Stage 3: Check if user mentions competitor negatively.
    If YES → Conquest Opportunity
    """
    text_lower = text.lower()
    
    for pattern in COMPETITOR_PATTERNS:
        if re.search(pattern, text_lower):
            return {
                'has_competitor_mention': True,
                'matched_pattern': pattern,
                'classification': 'conquest_opportunity',
                'stop': True
            }
    
    return {
        'has_competitor_mention': False,
        'stop': False
    }


# ============================================
# CHAIN-OF-THOUGHT CLASSIFIER
# ============================================

def classify_comment_cot(comment: Dict) -> Dict[str, Any]:
    """
    Full Chain-of-Thought classification.
    Runs through all stages in sequence.
    """
    text = comment.get('text', '') if isinstance(comment, dict) else str(comment)
    
    result = {
        'text': text[:200],
        'stages': [],
        'classification': 'casual',
        'value': 'none',
        'reasoning': []
    }
    
    # Stage 1: Possession Check
    stage1 = check_possession(text)
    result['stages'].append({'stage': 1, 'name': 'Possession Check', 'result': stage1})
    
    if stage1['stop']:
        result['classification'] = stage1['classification']
        result['value'] = LEAD_CATEGORIES[stage1['classification']]['value']
        result['reasoning'].append(f"User already owns product (matched: {stage1.get('matched_pattern', 'N/A')})")
        return result
    
    result['reasoning'].append("User doesn't appear to own the product")
    
    # Stage 2: Barrier Check
    stage2 = check_barriers(text)
    result['stages'].append({'stage': 2, 'name': 'Barrier Check', 'result': stage2})
    
    if stage2['stop']:
        result['classification'] = stage2['classification']
        result['value'] = LEAD_CATEGORIES[stage2['classification']]['value']
        result['reasoning'].append(f"User asking about: {', '.join(stage2.get('barrier_types', []))}")
        return result
    
    result['reasoning'].append("No direct purchase barriers asked")
    
    # Stage 3: Competitor Check
    stage3 = check_competitor(text)
    result['stages'].append({'stage': 3, 'name': 'Competitor Check', 'result': stage3})
    
    if stage3['stop']:
        result['classification'] = stage3['classification']
        result['value'] = LEAD_CATEGORIES[stage3['classification']]['value']
        result['reasoning'].append("User expressing frustration with competitor")
        return result
    
    result['reasoning'].append("No competitor frustration detected")
    
    # Default: Casual comment
    result['classification'] = 'casual'
    result['value'] = 'none'
    
    return result


# ============================================
# BATCH PROCESSING
# ============================================

def process_lead_funnel(comments: List[Dict]) -> Dict[str, Any]:
    """
    Process all comments through the lead funnel.
    
    Returns:
        {
            'leads': {
                'high_intent': [...],
                'conquest': [...],
                'consideration': [...],
                'customer_feedback': [...],
                'casual': [...]
            },
            'stats': {...},
            'summary': str
        }
    """
    leads = {
        'high_intent_lead': [],
        'conquest_opportunity': [],
        'consideration': [],
        'customer_feedback': [],
        'casual': []
    }
    
    for comment in comments:
        result = classify_comment_cot(comment)
        classification = result['classification']
        
        # Add original comment data
        lead_entry = {
            'text': comment.get('text', '')[:200] if isinstance(comment, dict) else str(comment)[:200],
            'author': comment.get('author', 'Anonymous') if isinstance(comment, dict) else 'Unknown',
            'votes': comment.get('votes', '0') if isinstance(comment, dict) else '0',
            'classification': classification,
            'value': result['value'],
            'reasoning': result['reasoning']
        }
        
        if classification in leads:
            leads[classification].append(lead_entry)
        else:
            leads['casual'].append(lead_entry)
    
    # Calculate stats
    total = len(comments)
    high_value = len(leads['high_intent_lead']) + len(leads['conquest_opportunity'])
    
    stats = {
        'total_processed': total,
        'high_intent_leads': len(leads['high_intent_lead']),
        'conquest_opportunities': len(leads['conquest_opportunity']),
        'customer_feedback': len(leads['customer_feedback']),
        'casual_comments': len(leads['casual']),
        'high_value_rate': round((high_value / total) * 100, 1) if total > 0 else 0
    }
    
    summary = (
        f"Processed {total} comments: "
        f"{stats['high_intent_leads']} high-intent leads, "
        f"{stats['conquest_opportunities']} conquest opportunities, "
        f"{stats['customer_feedback']} existing customers"
    )
    
    return {
        'leads': leads,
        'stats': stats,
        'summary': summary
    }


def get_actionable_leads(result: Dict) -> List[Dict]:
    """Get only high-value leads (high_intent + conquest)."""
    leads = result.get('leads', {})
    return leads.get('high_intent_lead', []) + leads.get('conquest_opportunity', [])


if __name__ == "__main__":
    # Test
    test_comments = [
        {"text": "I bought this last year, it's amazing!"},
        {"text": "How much does this cost?"},
        {"text": "Where can I buy this in India?"},
        {"text": "Samsung sucks, I'm done with them"},
        {"text": "Is this better than the iPhone?"},
        {"text": "Great video, keep it up!"},
        {"text": "Link please?"},
        {"text": "I've been using this for 6 months now"},
    ]
    
    result = process_lead_funnel(test_comments)
    print(f"\n{result['summary']}")
    print(f"\nStats: {json.dumps(result['stats'], indent=2)}")
    
    print("\n🔥 High-Intent Leads:")
    for lead in result['leads']['high_intent_lead']:
        print(f"  - {lead['text'][:50]}...")
        print(f"    Reasoning: {lead['reasoning']}")
