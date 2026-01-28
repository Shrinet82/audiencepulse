"""
Creator Profile - Multi-Video Aggregate Analysis

Surveys multiple videos from a creator to build a comprehensive
audience DNA profile. More accurate than single-video analysis.
"""

import os
import subprocess
import json
from typing import List, Dict, Any
from datetime import datetime

from .creator_audit import run_creator_audit


def scrape_video_comments(url: str) -> List[Dict]:
    """Scrape comments from a single video."""
    temp_file = f"temp_comments_{hash(url) % 10000}.jsonl"
    
    result = subprocess.run(
        ["python3", "scraper.py", url, "-o", temp_file],
        capture_output=True, text=True, cwd=os.getcwd()
    )
    
    comments = []
    if os.path.exists(temp_file):
        with open(temp_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    comments.append(json.loads(line))
                except:
                    pass
        os.remove(temp_file)  # Clean up
    
    return comments


def get_video_info(url: str) -> Dict:
    """Get basic video info."""
    try:
        from .video_analyzer import get_video_metadata
        return get_video_metadata(url)
    except:
        return {'title': 'Unknown', 'channel': 'Unknown'}


def build_creator_profile(
    video_urls: List[str],
    creator_name: str = "Unknown Creator",
    product_category: str = "premium",
    embedding_model: Any = None,
    progress_callback: callable = None
) -> Dict[str, Any]:
    """
    Build comprehensive creator profile from multiple videos.
    
    Args:
        video_urls: List of YouTube video URLs (3-5 recommended)
        creator_name: Name of the creator
        product_category: Target product category
        embedding_model: Pre-loaded SentenceTransformer
        progress_callback: Optional callback for progress updates
    
    Returns:
        Creator profile with aggregate analysis
    """
    start_time = datetime.now()
    
    profile = {
        'creator_name': creator_name,
        'videos_analyzed': [],
        'total_comments': 0,
        'merged_audit': {},
        'per_video_stats': [],
        'aggregate_scores': {},
        'timing': {}
    }
    
    all_comments = []
    
    # 1. Scrape all videos
    for i, url in enumerate(video_urls[:5]):  # Max 5 videos
        if progress_callback:
            progress_callback(f"Scraping video {i+1}/{len(video_urls[:5])}...")
        
        # Get video info
        video_info = get_video_info(url)
        
        # Scrape comments
        comments = scrape_video_comments(url)
        
        profile['videos_analyzed'].append({
            'url': url,
            'title': video_info.get('title', 'Unknown')[:50],
            'comment_count': len(comments)
        })
        
        profile['per_video_stats'].append({
            'title': video_info.get('title', 'Unknown')[:50],
            'comments': len(comments)
        })
        
        all_comments.extend(comments)
    
    profile['total_comments'] = len(all_comments)
    
    # 2. Run merged analysis
    if progress_callback:
        progress_callback(f"Analyzing {len(all_comments)} merged comments...")
    
    if len(all_comments) > 0:
        profile['merged_audit'] = run_creator_audit(
            comments=all_comments,
            video_metadata={'channel': creator_name},
            product_category=product_category,
            embedding_model=embedding_model
        )
        
        # Extract key scores for comparison
        audit = profile['merged_audit']
        fit = audit.get('creator_fit', {})
        dna = audit.get('audience_dna', {})
        health = audit.get('community_health', {})
        brand = audit.get('brand_affinity', {})
        
        profile['aggregate_scores'] = {
            'fit_score': fit.get('score', 0),
            'grade': fit.get('grade', 'N/A'),
            'verdict': fit.get('verdict', ''),
            'wallet_depth': {
                'score': dna.get('spending_power', {}).get('premium_score', 0),
                'verdict': dna.get('spending_power', {}).get('verdict', 'N/A')
            },
            'tech_level': {
                'score': dna.get('tech_literacy', {}).get('expert_score', 0),
                'verdict': dna.get('tech_literacy', {}).get('verdict', 'N/A')
            },
            'trust': {
                'score': health.get('trust', {}).get('score', 'N/A'),
                'numeric': health.get('trust', {}).get('score_numeric', 0)
            },
            'brand_tier': brand.get('dominant_tier', 'unknown')
        }
    
    # Timing
    end_time = datetime.now()
    profile['timing'] = {
        'duration_seconds': (end_time - start_time).total_seconds()
    }
    
    return profile


def compare_creators(
    profile_a: Dict,
    profile_b: Dict,
    product_category: str = "premium"
) -> Dict[str, Any]:
    """
    Compare two creator profiles.
    
    Returns:
        Comparison with winner and reasoning
    """
    scores_a = profile_a.get('aggregate_scores', {})
    scores_b = profile_b.get('aggregate_scores', {})
    
    comparison = {
        'creator_a': {
            'name': profile_a.get('creator_name', 'Creator A'),
            'videos': len(profile_a.get('videos_analyzed', [])),
            'comments': profile_a.get('total_comments', 0),
            'fit_score': scores_a.get('fit_score', 0),
            'grade': scores_a.get('grade', 'N/A'),
            'wallet': scores_a.get('wallet_depth', {}).get('verdict', 'N/A'),
            'tech': scores_a.get('tech_level', {}).get('verdict', 'N/A'),
            'trust': scores_a.get('trust', {}).get('score', 'N/A'),
            'brand_tier': scores_a.get('brand_tier', 'unknown')
        },
        'creator_b': {
            'name': profile_b.get('creator_name', 'Creator B'),
            'videos': len(profile_b.get('videos_analyzed', [])),
            'comments': profile_b.get('total_comments', 0),
            'fit_score': scores_b.get('fit_score', 0),
            'grade': scores_b.get('grade', 'N/A'),
            'wallet': scores_b.get('wallet_depth', {}).get('verdict', 'N/A'),
            'tech': scores_b.get('tech_level', {}).get('verdict', 'N/A'),
            'trust': scores_b.get('trust', {}).get('score', 'N/A'),
            'brand_tier': scores_b.get('brand_tier', 'unknown')
        },
        'winner': '',
        'reasoning': []
    }
    
    # Determine winner
    score_a = scores_a.get('fit_score', 0)
    score_b = scores_b.get('fit_score', 0)
    
    if score_a > score_b:
        comparison['winner'] = profile_a.get('creator_name', 'Creator A')
        comparison['reasoning'].append(f"Higher fit score ({score_a}% vs {score_b}%)")
    elif score_b > score_a:
        comparison['winner'] = profile_b.get('creator_name', 'Creator B')
        comparison['reasoning'].append(f"Higher fit score ({score_b}% vs {score_a}%)")
    else:
        comparison['winner'] = "TIE"
        comparison['reasoning'].append("Equal fit scores")
    
    # Add specific insights
    wallet_a = scores_a.get('wallet_depth', {}).get('score', 0)
    wallet_b = scores_b.get('wallet_depth', {}).get('score', 0)
    
    if wallet_a > wallet_b + 10:
        comparison['reasoning'].append(f"{profile_a.get('creator_name', 'A')} has higher-spending audience")
    elif wallet_b > wallet_a + 10:
        comparison['reasoning'].append(f"{profile_b.get('creator_name', 'B')} has higher-spending audience")
    
    return comparison


if __name__ == "__main__":
    # Test
    print("Creator Profile module loaded")
    print("Use build_creator_profile() to analyze multiple videos")
    print("Use compare_creators() to compare two profiles")
