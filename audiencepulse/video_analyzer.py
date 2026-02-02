# Video Analyzer Module for AudiencePulse
"""
Analyzes YouTube video content beyond comments:
1. Video Metadata (title, description, views, etc.)
2. Transcript/Captions
3. Comment-to-Content Correlation
4. Thumbnail Analysis
"""

import re
import os
import logging
import json
import subprocess
from typing import Dict, List, Optional, Tuple
from collections import Counter
from urllib.request import urlretrieve
from PIL import Image

logger = logging.getLogger("audiencepulse")

# ============================================
# 1. VIDEO METADATA EXTRACTION
# ============================================

def extract_video_id(url: str) -> Optional[str]:
    """Extract video ID from various YouTube URL formats."""
    patterns = [
        r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'(?:embed/)([a-zA-Z0-9_-]{11})',
        r'(?:shorts/)([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_video_metadata(url: str) -> Dict:
    """Extract video metadata using yt-dlp (no API key needed)."""
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError(f"Could not extract video ID from: {url}")
    
    try:
        # Use yt-dlp to get metadata as JSON
        result = subprocess.run(
            ['yt-dlp', '--dump-json', '--no-download', url],
            capture_output=True, text=True, timeout=60
        )
        
        if result.returncode != 0:
            logger.error(f"yt-dlp error: {result.stderr}")
            return {"error": result.stderr, "video_id": video_id}
        
        data = json.loads(result.stdout)
        
        # Extract relevant fields
        metadata = {
            "video_id": video_id,
            "title": data.get("title", ""),
            "description": data.get("description", ""),
            "channel": data.get("channel", ""),
            "channel_id": data.get("channel_id", ""),
            "upload_date": data.get("upload_date", ""),
            "duration": data.get("duration", 0),
            "view_count": data.get("view_count", 0),
            "like_count": data.get("like_count", 0),
            "comment_count": data.get("comment_count", 0),
            "tags": data.get("tags", []),
            "categories": data.get("categories", []),
            "thumbnail_url": data.get("thumbnail", ""),
            "age_limit": data.get("age_limit", 0),
            "is_live": data.get("is_live", False),
            "was_live": data.get("was_live", False),
        }
        
        # Calculate derived metrics
        if metadata["view_count"] > 0 and metadata["like_count"] > 0:
            metadata["like_ratio"] = round(
                metadata["like_count"] / metadata["view_count"] * 100, 4
            )
        else:
            metadata["like_ratio"] = 0.0
        
        # Engagement score
        if metadata["view_count"] > 0:
            engagement = (metadata["like_count"] + metadata["comment_count"]) / metadata["view_count"]
            metadata["engagement_rate"] = round(engagement * 100, 4)
        else:
            metadata["engagement_rate"] = 0.0
        
        logger.info(f"Extracted metadata for: {metadata['title'][:50]}...")
        return metadata
        
    except subprocess.TimeoutExpired:
        logger.error("yt-dlp timed out")
        return {"error": "Timeout", "video_id": video_id}
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        return {"error": str(e), "video_id": video_id}
    except Exception as e:
        logger.error(f"Metadata extraction failed: {e}")
        return {"error": str(e), "video_id": video_id}


# ============================================
# 2. TRANSCRIPT EXTRACTION
# ============================================

def get_transcript(url: str, languages: list = None) -> Dict:
    """Extract video transcript/captions."""
    if languages is None:
        languages = ['en', 'hi', 'es', 'fr', 'de']  # Common languages to try
    
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        logger.error("youtube-transcript-api not installed")
        return {"error": "youtube-transcript-api not installed", "segments": []}
    
    video_id = extract_video_id(url)
    if not video_id:
        return {"error": "Invalid URL", "segments": []}
    
    # COOKIE SUPPORT
    cookies = None
    if os.path.exists('cookies.txt'):
        cookies = 'cookies.txt'
    
    try:
        # Create API instance and fetch transcript
        # Note: API accepts cookies file path string directly in newer versions or via other methods.
        # Ideally: api = YouTubeTranscriptApi() 
        # But transcript fetching is static method.
        # Actually proper way:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=languages, cookies=cookies)
        
        # Convert to list of dicts
        segments = []
        for snippet in transcript:
            segments.append({
                "text": snippet.text,
                "start": snippet.start,
                "duration": snippet.duration
            })
        
        # Process transcript
        full_text = " ".join([s['text'] for s in segments])
        
        result = {
            "video_id": video_id,
            "language": transcript.language if hasattr(transcript, 'language') else "unknown",
            "is_generated": transcript.is_generated if hasattr(transcript, 'is_generated') else False,
            "segments": segments,
            "full_text": full_text,
            "word_count": len(full_text.split()),
            "duration_covered": sum(s.get('duration', 0) for s in segments),
        }
        
        logger.info(f"Extracted transcript: {result['word_count']} words")
        return result
        
    except Exception as e:
        logger.error(f"Transcript extraction failed: {e}")
        return {"error": str(e), "segments": [], "video_id": video_id}



# ============================================
# 3. COMMENT-TO-CONTENT CORRELATION
# ============================================

def extract_timestamp_mentions(comments: List[Dict]) -> Dict:
    """Extract timestamp mentions from comments and map to video segments."""
    timestamp_pattern = r'(\d{1,2}):(\d{2})(?::(\d{2}))?'
    
    mentions = []
    for comment in comments:
        text = comment.get('text', '')
        matches = re.findall(timestamp_pattern, text)
        for match in matches:
            hours = int(match[2]) if match[2] else 0
            minutes = int(match[0])
            seconds = int(match[1])
            total_seconds = hours * 3600 + minutes * 60 + seconds
            mentions.append({
                "timestamp": f"{match[0]}:{match[1]}" + (f":{match[2]}" if match[2] else ""),
                "seconds": total_seconds,
                "comment": text[:100],
                "votes": comment.get('votes', 0)
            })
    
    # Group by minute buckets
    minute_buckets = Counter()
    for m in mentions:
        bucket = m['seconds'] // 60
        minute_buckets[bucket] += 1
    
    return {
        "total_timestamp_mentions": len(mentions),
        "mentions": mentions[:50],  # Top 50
        "hotspot_minutes": dict(minute_buckets.most_common(10)),  # Top 10 hotspots
    }

def correlate_topics(transcript_text: str, comment_topics: List[str]) -> Dict:
    """Check which comment topics appear in the transcript."""
    if not transcript_text:
        return {"error": "No transcript available", "correlations": []}
    
    transcript_lower = transcript_text.lower()
    correlations = []
    
    for topic in comment_topics:
        topic_lower = topic.lower()
        # Simple word matching
        words = topic_lower.split()
        matches = sum(1 for word in words if word in transcript_lower)
        match_ratio = matches / len(words) if words else 0
        
        correlations.append({
            "topic": topic,
            "mentioned_in_video": match_ratio > 0.5,
            "match_score": round(match_ratio, 2)
        })
    
    return {
        "correlations": correlations,
        "topics_in_video": sum(1 for c in correlations if c['mentioned_in_video']),
        "topics_not_in_video": sum(1 for c in correlations if not c['mentioned_in_video']),
    }


# ============================================
# 4. THUMBNAIL ANALYSIS
# ============================================

def download_thumbnail(url: str, save_path: str = "thumbnail.jpg") -> Optional[str]:
    """Download video thumbnail."""
    try:
        urlretrieve(url, save_path)
        logger.info(f"Thumbnail saved to: {save_path}")
        return save_path
    except Exception as e:
        logger.error(f"Thumbnail download failed: {e}")
        return None

def analyze_thumbnail(image_path: str) -> Dict:
    """Analyze thumbnail image properties."""
    try:
        img = Image.open(image_path)
        
        # Basic properties
        width, height = img.size
        aspect_ratio = round(width / height, 2)
        
        # Color analysis
        img_rgb = img.convert('RGB')
        pixels = list(img_rgb.getdata())
        
        # Calculate average color
        r_avg = sum(p[0] for p in pixels) / len(pixels)
        g_avg = sum(p[1] for p in pixels) / len(pixels)
        b_avg = sum(p[2] for p in pixels) / len(pixels)
        
        # Brightness (0-255)
        brightness = (r_avg + g_avg + b_avg) / 3
        
        # Dominant colors (simplified - just get color buckets)
        color_buckets = Counter()
        for p in pixels[::100]:  # Sample every 100th pixel
            # Bucket into 6 categories
            r, g, b = p
            if r > 200 and g > 200 and b > 200:
                color_buckets['white'] += 1
            elif r < 50 and g < 50 and b < 50:
                color_buckets['black'] += 1
            elif r > g and r > b:
                color_buckets['red'] += 1
            elif g > r and g > b:
                color_buckets['green'] += 1
            elif b > r and b > g:
                color_buckets['blue'] += 1
            else:
                color_buckets['other'] += 1
        
        # Check for text (simple heuristic: high contrast areas)
        # This is a simplified approach; real OCR would use pytesseract
        has_high_contrast = brightness < 80 or brightness > 200
        
        result = {
            "width": width,
            "height": height,
            "aspect_ratio": aspect_ratio,
            "is_standard_ratio": aspect_ratio in [1.78, 1.77, 1.33],  # 16:9 or 4:3
            "brightness": round(brightness, 1),
            "brightness_category": "dark" if brightness < 100 else ("bright" if brightness > 180 else "medium"),
            "dominant_colors": dict(color_buckets.most_common(3)),
            "avg_color_rgb": (int(r_avg), int(g_avg), int(b_avg)),
            "likely_has_text": has_high_contrast,
            "file_size_kb": round(os.path.getsize(image_path) / 1024, 1),
        }
        
        logger.info(f"Thumbnail analyzed: {width}x{height}, brightness={brightness:.0f}")
        return result
        
    except Exception as e:
        logger.error(f"Thumbnail analysis failed: {e}")
        return {"error": str(e)}


# ============================================
# COMBINED ANALYSIS
# ============================================

def analyze_video_full(url: str, comments: List[Dict] = None) -> Dict:
    """Run all video analysis and return combined results."""
    logger.info(f"Starting full video analysis for: {url}")
    
    results = {
        "url": url,
        "metadata": {},
        "transcript": {},
        "timestamp_mentions": {},
        "topic_correlation": {},
        "thumbnail": {},
    }
    
    # 1. Metadata
    results["metadata"] = get_video_metadata(url)
    
    # 2. Transcript
    results["transcript"] = get_transcript(url)
    
    # 3. Timestamp mentions (if comments provided)
    if comments:
        results["timestamp_mentions"] = extract_timestamp_mentions(comments)
    
    # 4. Topic correlation (if both transcript and comment topics available)
    # This would need comment topics from the analyzer
    
    # 5. Thumbnail
    thumbnail_url = results["metadata"].get("thumbnail_url")
    if thumbnail_url:
        thumb_path = download_thumbnail(thumbnail_url, "thumbnail_temp.jpg")
        if thumb_path:
            results["thumbnail"] = analyze_thumbnail(thumb_path)
            # Clean up
            try:
                os.remove(thumb_path)
            except:
                pass
    
    logger.info("Full video analysis complete")
    return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python video_analyzer.py <YOUTUBE_URL>")
        sys.exit(1)
    
    url = sys.argv[1]
    result = analyze_video_full(url)
    print(json.dumps(result, indent=2, default=str))
