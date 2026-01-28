"""
Buying Intent Filter - Detect high-value leads from comments.

Two-stage funnel:
1. Regex Gate (zero cost) - fast keyword filter
2. LLM Classification - categorize intent type
"""

import os
import re
from typing import Dict, List, Any, Optional
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


# High-intent keywords for Stage 1 filtering
INTENT_KEYWORDS = {
    'transactional': [
        'price', 'buy', 'purchase', 'cost', 'how much', 'where can i',
        'link', 'shipping', 'available', 'in stock', 'order', 'discount',
        'coupon', 'promo', 'deal', 'sale', 'offer'
    ],
    'comparison': [
        'vs', 'versus', 'better than', 'compared to', 'or should i',
        'difference between', 'which is better', 'alternative'
    ],
    'consideration': [
        'worth it', 'should i get', 'should i buy', 'recommend',
        'thinking about', 'considering', 'is it good', 'any good'
    ],
    'support': [
        'how do i', 'how to', 'help', 'issue', 'problem', 'not working',
        'broken', 'fix', 'support', 'customer service'
    ]
}


def has_buying_intent(text: str) -> Dict[str, Any]:
    """
    Stage 1: Fast keyword check (zero API cost).
    
    Returns:
        {
            'has_intent': bool,
            'matched_categories': List[str],
            'matched_keywords': List[str]
        }
    """
    text_lower = text.lower()
    
    matched_categories = []
    matched_keywords = []
    
    for category, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                if category not in matched_categories:
                    matched_categories.append(category)
                matched_keywords.append(keyword)
    
    return {
        'has_intent': len(matched_categories) > 0,
        'matched_categories': matched_categories,
        'matched_keywords': list(set(matched_keywords))[:5]
    }


def filter_high_intent_comments(comments: List[Dict]) -> Dict[str, Any]:
    """
    Stage 1: Filter comments for buying intent keywords.
    
    Returns:
        {
            'high_intent': List of comments with intent,
            'low_intent': List of comments without intent,
            'stats': {
                'total': int,
                'high_intent_count': int,
                'filter_rate': float
            }
        }
    """
    high_intent = []
    low_intent = []
    
    for comment in comments:
        text = comment.get('text', '') if isinstance(comment, dict) else str(comment)
        intent_check = has_buying_intent(text)
        
        if intent_check['has_intent']:
            high_intent.append({
                **comment,
                '_intent_categories': intent_check['matched_categories'],
                '_intent_keywords': intent_check['matched_keywords']
            })
        else:
            low_intent.append(comment)
    
    total = len(comments)
    high_count = len(high_intent)
    
    return {
        'high_intent': high_intent,
        'low_intent': low_intent,
        'stats': {
            'total': total,
            'high_intent_count': high_count,
            'filter_rate': round((high_count / total) * 100, 1) if total > 0 else 0
        }
    }


def classify_intent_llm(
    comments: List[Dict],
    model: str = "llama-3.1-8b-instant"
) -> List[Dict]:
    """
    Stage 2: LLM classification of intent type.
    
    Categories:
    - transactional_query: Ready to buy
    - comparison_query: Evaluating options
    - past_purchase: Already bought (low value)
    - hypothetical: Wishful thinking
    - support_request: Needs help
    """
    if not comments:
        return []
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        # Fallback: use keyword-based classification
        return [
            {
                **c,
                '_intent_type': c.get('_intent_categories', ['unknown'])[0],
                '_lead_score': 'medium'
            }
            for c in comments
        ]
    
    client = Groq(api_key=api_key)
    
    # Batch classify for efficiency
    comments_text = "\n".join([
        f"{i+1}. {c.get('text', '')[:150]}"
        for i, c in enumerate(comments[:20])  # Limit to 20 for token efficiency
    ])
    
    try:
        response = client.chat.completions.create(
            messages=[{
                "role": "system",
                "content": """Classify each comment's buying intent. Return JSON:
{"results": [
    {"id": 1, "type": "transactional_query|comparison_query|past_purchase|hypothetical|support_request", "score": "high|medium|low"},
    ...
]}

Types:
- transactional_query: Ready to buy, asking where/how (HIGH value)
- comparison_query: Comparing products (HIGH value - competitive intel)
- past_purchase: Already bought (LOW value)
- hypothetical: Wishing/dreaming (MEDIUM value - pricing feedback)
- support_request: Needs help (MEDIUM value - loyalty opportunity)"""
            }, {
                "role": "user",
                "content": comments_text
            }],
            model=model,
            temperature=0.2,
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        classifications = result.get('results', [])
        
        # Merge classifications back to comments
        classified = []
        for i, comment in enumerate(comments[:20]):
            cls = next((c for c in classifications if c.get('id') == i + 1), {})
            classified.append({
                **comment,
                '_intent_type': cls.get('type', 'unknown'),
                '_lead_score': cls.get('score', 'medium')
            })
        
        # Add remaining comments with default classification
        for comment in comments[20:]:
            classified.append({
                **comment,
                '_intent_type': comment.get('_intent_categories', ['unknown'])[0],
                '_lead_score': 'medium'
            })
        
        return classified
        
    except Exception as e:
        # Fallback on error
        return [
            {
                **c,
                '_intent_type': c.get('_intent_categories', ['unknown'])[0],
                '_lead_score': 'medium',
                '_error': str(e)
            }
            for c in comments
        ]


def generate_lead_list(comments: List[Dict]) -> Dict[str, Any]:
    """
    Full pipeline: Filter -> Classify -> Generate lead list.
    """
    # Stage 1: Keyword filter
    filtered = filter_high_intent_comments(comments)
    
    if not filtered['high_intent']:
        return {
            'leads': [],
            'stats': filtered['stats'],
            'summary': 'No high-intent comments found'
        }
    
    # Stage 2: LLM classification
    classified = classify_intent_llm(filtered['high_intent'])
    
    # Organize by lead score
    high_value = [c for c in classified if c.get('_lead_score') == 'high']
    medium_value = [c for c in classified if c.get('_lead_score') == 'medium']
    low_value = [c for c in classified if c.get('_lead_score') == 'low']
    
    # Generate summary
    summary = (
        f"Found {len(high_value)} high-value leads, "
        f"{len(medium_value)} medium-value, "
        f"{len(low_value)} low-value from {filtered['stats']['total']} comments"
    )
    
    return {
        'leads': {
            'high': high_value,
            'medium': medium_value,
            'low': low_value
        },
        'stats': {
            **filtered['stats'],
            'high_value_count': len(high_value),
            'medium_value_count': len(medium_value),
            'low_value_count': len(low_value)
        },
        'summary': summary
    }


def format_lead_for_export(lead: Dict) -> Dict:
    """Format lead for CSV export."""
    return {
        'text': lead.get('text', '')[:200],
        'author': lead.get('author', 'Anonymous'),
        'intent_type': lead.get('_intent_type', 'unknown'),
        'lead_score': lead.get('_lead_score', 'medium'),
        'keywords': ', '.join(lead.get('_intent_keywords', [])),
        'votes': lead.get('votes', '0'),
        'time': lead.get('time', '')
    }


if __name__ == "__main__":
    # Test
    test_comments = [
        {"text": "How much does this cost?", "author": "buyer1"},
        {"text": "Is this better than Samsung?", "author": "comparison1"},
        {"text": "I bought this last year, it's great", "author": "past_buyer"},
        {"text": "Nice video!", "author": "casual"},
        {"text": "Where can I buy this in India?", "author": "buyer2"},
        {"text": "I wish I could afford this", "author": "wishful"},
        {"text": "Great content, keep it up!", "author": "fan"},
        {"text": "Link please?", "author": "buyer3"},
    ]
    
    result = generate_lead_list(test_comments)
    
    import json
    print(json.dumps(result['stats'], indent=2))
    print(f"\nSummary: {result['summary']}")
    print(f"\nHigh-value leads: {len(result['leads']['high'])}")
