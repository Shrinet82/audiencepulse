"""
Marketing Intelligence Engine - Orchestrates all analysis components.

Unified pipeline:
1. Fetch video data + comments (parallel)
2. Smart sample comments
3. Create context from transcript
4. Run context-aware analysis
5. Filter buying intent leads
6. Assess brand safety
7. Generate comprehensive report
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from .smart_sampler import smart_sample, get_sample_summary
from .context_engine import create_context_object, enhance_analysis_prompt, get_context_aware_prompt
from .brand_safety import assess_brand_safety, get_safety_badge
from .intent_filter import generate_lead_list, format_lead_for_export
from .video_analyzer import get_video_metadata, get_video_transcript


def run_full_analysis(
    url: str,
    comments: List[Dict],
    model: str = "llama-3.3-70b-versatile",
    sampling_config: Dict = None
) -> Dict[str, Any]:
    """
    Run the complete Marketing Intelligence Engine analysis.
    
    Args:
        url: YouTube video URL
        comments: List of scraped comments (full objects with time, votes, etc.)
        model: LLM model for analysis
        sampling_config: Override default sampling (top_by_likes, top_by_date, etc.)
    
    Returns:
        Comprehensive analysis report
    """
    start_time = datetime.now()
    
    # Default sampling config
    sampling_config = sampling_config or {
        'top_by_likes': 50,
        'top_by_date': 50,
        'top_by_replies': 20
    }
    
    report = {
        'metadata': {},
        'context': {},
        'sampling': {},
        'leads': {},
        'brand_safety': {},
        'analysis': {},
        'timing': {}
    }
    
    # ========================================
    # 1. VIDEO METADATA
    # ========================================
    try:
        metadata = get_video_metadata(url)
        report['metadata'] = metadata
    except Exception as e:
        report['metadata'] = {'error': str(e)}
    
    # ========================================
    # 2. SMART SAMPLING
    # ========================================
    sample_result = smart_sample(
        comments,
        top_by_likes=sampling_config['top_by_likes'],
        top_by_date=sampling_config['top_by_date'],
        top_by_replies=sampling_config['top_by_replies']
    )
    
    sampled_comments = sample_result['sampled']
    report['sampling'] = {
        'stats': sample_result['stats'],
        'summary': get_sample_summary(sample_result['stats']),
        'sample_buckets': sample_result['buckets']
    }
    
    # ========================================
    # 3. CONTEXT EXTRACTION
    # ========================================
    try:
        transcript = get_video_transcript(url)
        context = create_context_object(
            transcript=transcript,
            title=report['metadata'].get('title', ''),
            description=report['metadata'].get('description', '')
        )
        report['context'] = context
    except Exception as e:
        report['context'] = {'error': str(e), 'context_source': 'none'}
    
    # ========================================
    # 4. BUYING INTENT LEADS
    # ========================================
    leads_result = generate_lead_list(sampled_comments)
    report['leads'] = {
        'high_value': len(leads_result['leads'].get('high', [])),
        'medium_value': len(leads_result['leads'].get('medium', [])),
        'low_value': len(leads_result['leads'].get('low', [])),
        'summary': leads_result['summary'],
        'stats': leads_result['stats'],
        # Include actual leads for export
        'high_value_leads': [
            format_lead_for_export(l) 
            for l in leads_result['leads'].get('high', [])[:10]
        ]
    }
    
    # ========================================
    # 5. BRAND SAFETY
    # ========================================
    safety = assess_brand_safety(
        transcript=report['context'].get('summary', ''),
        comments=sampled_comments,
        title=report['metadata'].get('title', ''),
        description=report['metadata'].get('description', '')
    )
    report['brand_safety'] = {
        'verdict': safety['verdict'],
        'badge': get_safety_badge(safety['verdict']),
        'score': safety['score'],
        'flags': {
            'content_flag': safety['ad_suitability_flag'],
            'community_flag': safety['community_flag']
        },
        'unsafe_topics': list(safety['unsafe_topics'].keys()),
        'toxicity_pct': safety['toxicity']['toxicity_pct'],
        'recommendations': safety['recommendations']
    }
    
    # ========================================
    # 6. TIMING
    # ========================================
    end_time = datetime.now()
    report['timing'] = {
        'total_seconds': (end_time - start_time).total_seconds(),
        'timestamp': end_time.isoformat()
    }
    
    return report


def generate_executive_summary(report: Dict) -> str:
    """Generate a text summary for non-technical stakeholders."""
    metadata = report.get('metadata', {})
    safety = report.get('brand_safety', {})
    leads = report.get('leads', {})
    sampling = report.get('sampling', {})
    
    summary = f"""
MARKETING INTELLIGENCE REPORT
{'=' * 40}

VIDEO: {metadata.get('title', 'Unknown')[:50]}...
CHANNEL: {metadata.get('channel', 'Unknown')}
VIEWS: {metadata.get('view_count', 0):,}

BRAND SAFETY: {safety.get('badge', 'Unknown')}
Score: {safety.get('score', 0)}/100
{chr(10).join(['• ' + r for r in safety.get('recommendations', [])])}

LEADS DETECTED:
• High-Value: {leads.get('high_value', 0)}
• Medium-Value: {leads.get('medium_value', 0)}
• Low-Value: {leads.get('low_value', 0)}

SAMPLING: {sampling.get('summary', 'N/A')}

ANALYSIS TIME: {report.get('timing', {}).get('total_seconds', 0):.1f}s
"""
    return summary.strip()


def export_leads_csv(report: Dict, filename: str = 'leads.csv'):
    """Export high-value leads to CSV."""
    import csv
    
    leads = report.get('leads', {}).get('high_value_leads', [])
    
    if not leads:
        return False
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=leads[0].keys())
        writer.writeheader()
        writer.writerows(leads)
    
    return True


if __name__ == "__main__":
    # Test with mock data
    test_comments = [
        {"text": "How much does this cost?", "votes": "100", "time": "2 hours ago"},
        {"text": "Is this better than Samsung?", "votes": "50", "time": "1 day ago"},
        {"text": "Great video!", "votes": "200", "time": "1 hour ago"},
        {"text": "Link please?", "votes": "30", "time": "3 hours ago"},
        {"text": "I wish I could afford this", "votes": "10", "time": "4 hours ago"},
    ]
    
    # Just test sampling and leads (no API calls)
    sample_result = smart_sample(test_comments)
    leads_result = generate_lead_list(test_comments)
    
    print(f"Sampled: {len(sample_result['sampled'])} comments")
    print(f"Leads found: {leads_result['summary']}")
