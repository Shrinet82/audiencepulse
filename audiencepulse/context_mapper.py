"""
Context Mapper - Timestamp-aware comment analysis

Maps comments to the exact video moment they reference:
1. INDEX: Parse transcript with timestamps
2. LOOK-BACK: When analyzing comment, fetch surrounding context
3. CONTEXTUALIZE: Combine comment + transcript for accurate classification
"""

import os
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import timedelta


# ============================================
# TRANSCRIPT PARSING
# ============================================

def parse_timestamp(ts_str: str) -> Optional[float]:
    """
    Parse timestamp string to seconds.
    Handles: "1:23", "01:23", "1:23:45", "04:20"
    """
    try:
        parts = ts_str.strip().split(':')
        if len(parts) == 2:
            minutes, seconds = map(float, parts)
            return minutes * 60 + seconds
        elif len(parts) == 3:
            hours, minutes, seconds = map(float, parts)
            return hours * 3600 + minutes * 60 + seconds
        else:
            return float(ts_str)
    except:
        return None


def extract_comment_timestamp(text: str) -> Optional[float]:
    """
    Extract timestamp reference from comment.
    Looks for patterns like "at 4:20" or "04:20"
    """
    patterns = [
        r'(?:at|@|around)\s*(\d{1,2}:\d{2}(?::\d{2})?)',
        r'\b(\d{1,2}:\d{2}(?::\d{2})?)\b',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return parse_timestamp(match.group(1))
    
    return None


def parse_transcript_with_timestamps(transcript_data: Any) -> List[Dict[str, Any]]:
    """
    Parse transcript into indexed segments.
    
    Handles different transcript formats:
    - List of {"text": ..., "start": ..., "duration": ...}
    - Plain text with embedded timestamps
    - VTT/SRT format
    
    Returns:
        List of {"start": float, "end": float, "text": str}
    """
    segments = []
    
    if isinstance(transcript_data, list):
        # YouTube auto-generated format
        for item in transcript_data:
            if isinstance(item, dict):
                start = item.get('start', 0)
                duration = item.get('duration', 5)
                text = item.get('text', '')
                segments.append({
                    'start': float(start),
                    'end': float(start) + float(duration),
                    'text': text
                })
    
    elif isinstance(transcript_data, str):
        # Try to parse VTT/SRT or plain text
        lines = transcript_data.split('\n')
        current_start = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for timestamp line (VTT format: 00:00:00.000 --> 00:00:05.000)
            ts_match = re.match(r'(\d{2}:\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[.,]\d{3})', line)
            if ts_match:
                start_str = ts_match.group(1).replace(',', '.')
                end_str = ts_match.group(2).replace(',', '.')
                current_start = parse_vtt_timestamp(start_str)
                continue
            
            # Skip numeric lines (SRT indices)
            if line.isdigit():
                continue
            
            # Add as segment
            if line and not line.startswith('WEBVTT'):
                segments.append({
                    'start': current_start,
                    'end': current_start + 5,  # Default 5 second window
                    'text': line
                })
                current_start += 5
    
    return segments


def parse_vtt_timestamp(ts_str: str) -> float:
    """Parse VTT timestamp (00:00:00.000) to seconds."""
    try:
        parts = ts_str.replace(',', '.').split(':')
        hours = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    except:
        return 0


# ============================================
# CONTEXT LOOKUP
# ============================================

def get_context_window(
    segments: List[Dict],
    timestamp: float,
    window_before: float = 15,
    window_after: float = 10
) -> Dict[str, Any]:
    """
    Get transcript context around a specific timestamp.
    
    Args:
        segments: Indexed transcript segments
        timestamp: Target timestamp in seconds
        window_before: Seconds to look back
        window_after: Seconds to look forward
    
    Returns:
        {
            'timestamp': float,
            'window': [start, end],
            'context_text': str,
            'segments': List[Dict]
        }
    """
    start_time = max(0, timestamp - window_before)
    end_time = timestamp + window_after
    
    relevant_segments = [
        seg for seg in segments
        if (seg['start'] >= start_time and seg['start'] <= end_time) or
           (seg['end'] >= start_time and seg['end'] <= end_time)
    ]
    
    context_text = ' '.join([seg['text'] for seg in relevant_segments])
    
    return {
        'timestamp': timestamp,
        'window': [start_time, end_time],
        'context_text': context_text.strip(),
        'segments': relevant_segments
    }


# ============================================
# CONTEXTUAL CLASSIFICATION
# ============================================

def classify_with_context(
    comment_text: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Re-classify comment based on video context.
    
    Example:
    - Video: "Competitor claims to be faster..."
    - Comment: "This is a lie!"
    - Old classification: Negative/Hate
    - New classification: Agreement with Creator
    
    Returns:
        {
            'original_sentiment': str,
            'contextualized_sentiment': str,
            'context_type': str,
            'reasoning': str
        }
    """
    context_text = context.get('context_text', '').lower()
    comment_lower = comment_text.lower()
    
    # Detect what video is talking about
    video_topics = []
    if any(word in context_text for word in ['competitor', 'rival', 'vs', 'compared']):
        video_topics.append('competitor_discussion')
    if any(word in context_text for word in ['claim', 'claims', 'says', 'according']):
        video_topics.append('claims_discussion')
    if any(word in context_text for word in ['problem', 'issue', 'bug', 'flaw']):
        video_topics.append('problem_discussion')
    
    # Detect comment sentiment
    negative_words = ['lie', 'wrong', 'false', 'bad', 'terrible', 'sucks', 'hate', 'awful']
    positive_words = ['true', 'right', 'agree', 'exactly', 'yes', 'correct', 'love', 'great']
    
    has_negative = any(word in comment_lower for word in negative_words)
    has_positive = any(word in comment_lower for word in positive_words)
    
    # Contextualize
    result = {
        'video_context': context_text[:200] if context_text else 'N/A',
        'video_topics': video_topics,
        'original_sentiment': 'negative' if has_negative else 'positive' if has_positive else 'neutral'
    }
    
    # Re-classify based on context
    if 'competitor_discussion' in video_topics:
        if has_negative:
            # Negative about competitor = Agreement with creator
            result['contextualized_sentiment'] = 'agreement_with_creator'
            result['context_type'] = 'competitor_criticism'
            result['reasoning'] = 'User criticizing competitor discussed in video = supports creator'
        elif has_positive:
            # Positive about competitor = Disagreement
            result['contextualized_sentiment'] = 'disagreement_with_creator'
            result['context_type'] = 'competitor_support'
            result['reasoning'] = 'User praising competitor = challenges creator'
        else:
            result['contextualized_sentiment'] = 'neutral'
            result['context_type'] = 'observation'
            result['reasoning'] = 'Neutral comment during competitor discussion'
    
    elif 'claims_discussion' in video_topics:
        if has_negative:
            # Could be validating or challenging
            result['contextualized_sentiment'] = 'claim_validation'
            result['context_type'] = 'validates_claim'
            result['reasoning'] = 'Negative reaction to third-party claims discussed in video'
        else:
            result['contextualized_sentiment'] = result['original_sentiment']
            result['context_type'] = 'direct_response'
            result['reasoning'] = 'Direct response to claims in video'
    
    else:
        # No special context
        result['contextualized_sentiment'] = result['original_sentiment']
        result['context_type'] = 'direct'
        result['reasoning'] = 'No special context detected'
    
    return result


# ============================================
# FULL CONTEXT MAPPING PIPELINE
# ============================================

def map_comments_to_context(
    comments: List[Dict],
    transcript_data: Any
) -> Dict[str, Any]:
    """
    Full context mapping pipeline.
    
    Args:
        comments: List of comment dicts
        transcript_data: Raw transcript (list or string)
    
    Returns:
        {
            'mapped_comments': List of comments with context,
            'stats': {...},
            'summary': str
        }
    """
    # Parse transcript
    segments = parse_transcript_with_timestamps(transcript_data)
    
    if not segments:
        return {
            'status': 'skipped',
            'reason': 'No transcript segments found',
            'mapped_comments': comments
        }
    
    mapped = []
    comments_with_timestamp = 0
    reclassified = 0
    
    for comment in comments:
        text = comment.get('text', '') if isinstance(comment, dict) else str(comment)
        
        # Try to extract timestamp from comment
        timestamp = extract_comment_timestamp(text)
        
        if timestamp is not None:
            comments_with_timestamp += 1
            
            # Get context window
            context = get_context_window(segments, timestamp)
            
            # Classify with context
            classification = classify_with_context(text, context)
            
            # Check if reclassified
            if classification['contextualized_sentiment'] != classification['original_sentiment']:
                reclassified += 1
            
            mapped.append({
                **comment,
                '_has_timestamp': True,
                '_timestamp': timestamp,
                '_context': context['context_text'][:100],
                '_classification': classification
            })
        else:
            mapped.append({
                **comment,
                '_has_timestamp': False,
                '_classification': {'contextualized_sentiment': 'unknown', 'context_type': 'no_timestamp'}
            })
    
    stats = {
        'total_comments': len(comments),
        'transcript_segments': len(segments),
        'comments_with_timestamp': comments_with_timestamp,
        'reclassified_count': reclassified
    }
    
    summary = (
        f"Mapped {len(comments)} comments. "
        f"{comments_with_timestamp} had timestamps, "
        f"{reclassified} were reclassified with context."
    )
    
    return {
        'status': 'success',
        'mapped_comments': mapped,
        'stats': stats,
        'summary': summary
    }


if __name__ == "__main__":
    # Test
    test_transcript = [
        {"start": 250, "duration": 5, "text": "Now let's talk about competitor claims"},
        {"start": 255, "duration": 5, "text": "Samsung says their battery lasts longer"},
        {"start": 260, "duration": 5, "text": "But that's completely false"},
    ]
    
    test_comments = [
        {"text": "At 4:20 this is such a lie!"},
        {"text": "Great video!"},
        {"text": "4:22 exactly, Samsung always lies"},
    ]
    
    result = map_comments_to_context(test_comments, test_transcript)
    print(result['summary'])
    
    for c in result['mapped_comments']:
        if c.get('_has_timestamp'):
            print(f"\n{c['text'][:50]}...")
            print(f"  Context: {c.get('_context', 'N/A')}")
            print(f"  Classification: {c['_classification']}")
