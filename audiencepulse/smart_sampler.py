"""
Smart Sampler - Intelligent comment sampling for token optimization.

Implements stratified sampling to get 90% of insights from 1% of comments:
- Bucket A: Top by likes (consensus)
- Bucket B: Top by date (current pulse)
- Bucket C: Top by replies (discussion hubs)
"""

from typing import List, Dict, Any
from datetime import datetime
import re


def parse_votes(votes_str: str) -> int:
    """Parse vote string like '1.2k' or '500' to integer."""
    if not votes_str:
        return 0
    try:
        v = str(votes_str).lower().strip()
        if 'k' in v:
            return int(float(v.replace('k', '')) * 1000)
        if 'm' in v:
            return int(float(v.replace('m', '')) * 1000000)
        return int(v)
    except:
        return 0


def parse_replies(replies_str: str) -> int:
    """Parse reply count string to integer."""
    if not replies_str:
        return 0
    try:
        # Handle "X replies" format
        match = re.search(r'(\d+)', str(replies_str))
        if match:
            return int(match.group(1))
        return 0
    except:
        return 0


def parse_relative_time_to_minutes(time_str: str) -> int:
    """
    Convert relative time to minutes for sorting.
    Lower = more recent.
    """
    if not time_str:
        return 999999  # Unknown = very old
    
    time_str = time_str.lower()
    
    # Extract number
    match = re.search(r'(\d+)', time_str)
    if not match:
        return 999999
    
    num = int(match.group(1))
    
    if 'second' in time_str:
        return num // 60
    elif 'minute' in time_str:
        return num
    elif 'hour' in time_str:
        return num * 60
    elif 'day' in time_str:
        return num * 60 * 24
    elif 'week' in time_str:
        return num * 60 * 24 * 7
    elif 'month' in time_str:
        return num * 60 * 24 * 30
    elif 'year' in time_str:
        return num * 60 * 24 * 365
    
    return 999999


def smart_sample(
    comments: List[Dict[str, Any]],
    top_by_likes: int = 50,
    top_by_date: int = 50,
    top_by_replies: int = 20,
    min_reply_threshold: int = 3
) -> Dict[str, Any]:
    """
    Perform stratified sampling on comments.
    
    Args:
        comments: List of comment dicts with 'text', 'votes', 'replies', 'time'
        top_by_likes: How many from popularity bucket
        top_by_date: How many from recency bucket
        top_by_replies: How many from discussion hubs
        min_reply_threshold: Minimum replies to qualify for Bucket C
    
    Returns:
        {
            'sampled': List of sampled comments,
            'stats': Sampling statistics,
            'buckets': {'likes': [...], 'date': [...], 'replies': [...]}
        }
    """
    if not comments:
        return {'sampled': [], 'stats': {}, 'buckets': {}}
    
    # Enrich comments with parsed values for sorting
    enriched = []
    for c in comments:
        enriched.append({
            **c,
            '_votes': parse_votes(c.get('votes', '0')),
            '_replies': parse_replies(c.get('replies', '0')),
            '_time_minutes': parse_relative_time_to_minutes(c.get('time', ''))
        })
    
    # Bucket A: Top by likes (consensus)
    sorted_by_likes = sorted(enriched, key=lambda x: x['_votes'], reverse=True)
    bucket_likes = sorted_by_likes[:top_by_likes]
    
    # Bucket B: Top by date (newest first = pulse)
    sorted_by_date = sorted(enriched, key=lambda x: x['_time_minutes'])
    bucket_date = sorted_by_date[:top_by_date]
    
    # Bucket C: Discussion hubs (high reply count)
    discussion_hubs = [c for c in enriched if c['_replies'] >= min_reply_threshold]
    sorted_by_replies = sorted(discussion_hubs, key=lambda x: x['_replies'], reverse=True)
    bucket_replies = sorted_by_replies[:top_by_replies]
    
    # Deduplicate across buckets (by text)
    seen_texts = set()
    sampled = []
    
    def add_unique(bucket, source_name):
        added = 0
        for c in bucket:
            text = c.get('text', '').strip()[:100]  # First 100 chars as key
            if text and text not in seen_texts:
                seen_texts.add(text)
                # Remove internal fields before adding
                clean = {k: v for k, v in c.items() if not k.startswith('_')}
                clean['_sample_source'] = source_name
                sampled.append(clean)
                added += 1
        return added
    
    likes_added = add_unique(bucket_likes, 'likes')
    date_added = add_unique(bucket_date, 'date')
    replies_added = add_unique(bucket_replies, 'replies')
    
    stats = {
        'total_input': len(comments),
        'sampled_count': len(sampled),
        'reduction_pct': round((1 - len(sampled) / len(comments)) * 100, 1) if comments else 0,
        'bucket_likes': likes_added,
        'bucket_date': date_added,
        'bucket_replies': replies_added,
        'duplicates_removed': (top_by_likes + top_by_date + top_by_replies) - len(sampled)
    }
    
    return {
        'sampled': sampled,
        'stats': stats,
        'buckets': {
            'likes': [c.get('text', '')[:50] + '...' for c in bucket_likes[:5]],
            'date': [c.get('text', '')[:50] + '...' for c in bucket_date[:5]],
            'replies': [c.get('text', '')[:50] + '...' for c in bucket_replies[:5]]
        }
    }


def get_sample_summary(stats: Dict) -> str:
    """Generate human-readable summary of sampling."""
    return (
        f"Sampled {stats['sampled_count']} from {stats['total_input']} comments "
        f"({stats['reduction_pct']}% reduction). "
        f"Sources: {stats['bucket_likes']} popular, {stats['bucket_date']} recent, "
        f"{stats['bucket_replies']} discussions."
    )


if __name__ == "__main__":
    # Test with sample data
    test_comments = [
        {"text": "Great video!", "votes": "1.2k", "replies": "50 replies", "time": "2 hours ago"},
        {"text": "This is bad", "votes": "5", "replies": "0", "time": "1 day ago"},
        {"text": "Where can I buy?", "votes": "100", "replies": "10 replies", "time": "3 hours ago"},
        {"text": "First!", "votes": "2k", "replies": "5 replies", "time": "1 month ago"},
    ]
    
    result = smart_sample(test_comments, top_by_likes=2, top_by_date=2, top_by_replies=2)
    print(f"Sampled: {len(result['sampled'])} comments")
    print(f"Stats: {result['stats']}")
    print(f"Summary: {get_sample_summary(result['stats'])}")
