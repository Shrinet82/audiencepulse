# Time parsing utilities for AudiencePulse
"""
Parses relative time strings like "2 hours ago", "3 days ago" into actual datetimes.
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple

def parse_relative_time(time_str: str, reference_time: datetime = None) -> Optional[datetime]:
    """
    Convert relative time string to actual datetime.
    
    Args:
        time_str: e.g., "2 hours ago", "3 days ago", "1 month ago"
        reference_time: The time to subtract from (defaults to now)
    
    Returns:
        Actual datetime when the comment was posted
    """
    if reference_time is None:
        reference_time = datetime.now()
    
    time_str = time_str.lower().strip()
    
    # Patterns for different time units
    patterns = [
        (r'(\d+)\s*second', 'seconds'),
        (r'(\d+)\s*minute', 'minutes'),
        (r'(\d+)\s*hour', 'hours'),
        (r'(\d+)\s*day', 'days'),
        (r'(\d+)\s*week', 'weeks'),
        (r'(\d+)\s*month', 'months'),
        (r'(\d+)\s*year', 'years'),
    ]
    
    for pattern, unit in patterns:
        match = re.search(pattern, time_str)
        if match:
            value = int(match.group(1))
            
            if unit == 'seconds':
                delta = timedelta(seconds=value)
            elif unit == 'minutes':
                delta = timedelta(minutes=value)
            elif unit == 'hours':
                delta = timedelta(hours=value)
            elif unit == 'days':
                delta = timedelta(days=value)
            elif unit == 'weeks':
                delta = timedelta(weeks=value)
            elif unit == 'months':
                delta = timedelta(days=value * 30)  # Approximate
            elif unit == 'years':
                delta = timedelta(days=value * 365)
            else:
                continue
            
            return reference_time - delta
    
    # Handle "just now" or similar
    if 'just now' in time_str or 'now' in time_str:
        return reference_time
    
    return None


def parse_upload_date(upload_date_str: str) -> Optional[datetime]:
    """
    Parse YouTube upload date format (YYYYMMDD).
    
    Args:
        upload_date_str: e.g., "20260121"
    
    Returns:
        datetime object
    """
    try:
        return datetime.strptime(upload_date_str, "%Y%m%d")
    except:
        return None


def calculate_time_since_upload(comment_time_str: str, upload_date: datetime, now: datetime = None) -> Tuple[Optional[timedelta], str]:
    """
    Calculate how long after video upload a comment was posted.
    
    Args:
        comment_time_str: e.g., "2 hours ago"
        upload_date: When the video was uploaded
        now: Current time (defaults to datetime.now())
    
    Returns:
        (timedelta since upload, human readable string)
    """
    if now is None:
        now = datetime.now()
    
    comment_posted = parse_relative_time(comment_time_str, now)
    
    if comment_posted is None:
        return None, "Unknown"
    
    time_since_upload = comment_posted - upload_date
    
    if time_since_upload.total_seconds() < 0:
        # Comment claims to be from before video upload - data error
        return None, "Data error"
    
    # Convert to human readable
    total_hours = time_since_upload.total_seconds() / 3600
    
    if total_hours < 1:
        return time_since_upload, "Within first hour"
    elif total_hours < 6:
        return time_since_upload, "Hours 1-6"
    elif total_hours < 12:
        return time_since_upload, "Hours 6-12"
    elif total_hours < 24:
        return time_since_upload, "Hours 12-24"
    elif total_hours < 48:
        return time_since_upload, "Day 1-2"
    elif total_hours < 168:  # 7 days
        return time_since_upload, f"Day {int(total_hours // 24)}"
    elif total_hours < 720:  # 30 days
        return time_since_upload, f"Week {int(total_hours // 168)}"
    else:
        return time_since_upload, "After 30 days"


def analyze_comment_timing(comments: list, upload_date_str: str) -> dict:
    """
    Analyze when comments were posted relative to video upload.
    
    Args:
        comments: List of comment dicts with 'time' field
        upload_date_str: Video upload date (YYYYMMDD format)
    
    Returns:
        Analysis dict with timing breakdown
    """
    upload_date = parse_upload_date(upload_date_str)
    if upload_date is None:
        return {"error": "Could not parse upload date"}
    
    now = datetime.now()
    video_age_hours = (now - upload_date).total_seconds() / 3600
    
    buckets = {
        "Within first hour": 0,
        "Hours 1-6": 0,
        "Hours 6-12": 0,
        "Hours 12-24": 0,
        "Day 1-2": 0,
        "Day 2-7": 0,
        "Week 1-4": 0,
        "After 30 days": 0,
        "Unknown": 0,
    }
    
    for comment in comments:
        time_str = comment.get('time', '') if isinstance(comment, dict) else ''
        if not time_str:
            buckets["Unknown"] += 1
            continue
        
        _, bucket = calculate_time_since_upload(time_str, upload_date, now)
        
        # Map to simpler buckets
        if bucket in buckets:
            buckets[bucket] += 1
        elif bucket.startswith("Day"):
            buckets["Day 2-7"] += 1
        elif bucket.startswith("Week"):
            buckets["Week 1-4"] += 1
        else:
            buckets["Unknown"] += 1
    
    # Remove empty buckets
    buckets = {k: v for k, v in buckets.items() if v > 0}
    
    # Calculate video age
    if video_age_hours < 24:
        video_age_str = f"{video_age_hours:.0f} hours"
    else:
        video_age_str = f"{video_age_hours / 24:.1f} days"
    
    return {
        "video_age": video_age_str,
        "video_age_hours": video_age_hours,
        "upload_date": upload_date.strftime("%Y-%m-%d"),
        "total_comments": sum(buckets.values()),
        "buckets": buckets,
    }


if __name__ == "__main__":
    # Test
    test_comments = [
        {"time": "3 minutes ago"},
        {"time": "2 hours ago"},
        {"time": "1 day ago"},
        {"time": "3 days ago"},
    ]
    
    result = analyze_comment_timing(test_comments, "20260127")
    import json
    print(json.dumps(result, indent=2))
