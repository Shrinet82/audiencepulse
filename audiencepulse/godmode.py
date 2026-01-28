"""
God Mode - Unified Marketing Intelligence Engine

Combines all advanced systems:
1. Distributed Mind (Map-Reduce for 10K+ comments)
2. Semantic Clustering (Vector-based noise reduction)
3. Lead Funnel (Chain-of-Thought precision detection)
4. Context Mapper (Timestamp-aware analysis)
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from .distributed_mind import distributed_analysis, shard_comments
from .semantic_cluster import semantic_cluster_analysis, get_top_clusters
from .lead_funnel import process_lead_funnel, get_actionable_leads
from .context_mapper import map_comments_to_context


# ============================================
# CONFIGURATION
# ============================================

GODMODE_CONFIG = {
    'chunk_size': 100,
    'max_workers': 20,
    'cluster_eps': 0.35,
    'cluster_min_samples': 3,
    'enable_context_mapping': True,
    'enable_clustering': True,
    'enable_leads': True,
    'enable_distributed': True
}


# ============================================
# GOD MODE ORCHESTRATOR
# ============================================

def run_godmode_analysis(
    comments: List[Dict],
    transcript_data: Any = None,
    video_metadata: Dict = None,
    config: Dict = None,
    embedding_model: Any = None
) -> Dict[str, Any]:
    """
    Full God Mode analysis pipeline.
    
    Args:
        comments: List of comment dicts
        transcript_data: Video transcript for context mapping
        video_metadata: Video title, description, etc.
        config: Override default config
    
    Returns:
        Comprehensive God Mode report
    """
    config = {**GODMODE_CONFIG, **(config or {})}
    start_time = datetime.now()
    
    report = {
        'metadata': video_metadata or {},
        'config': config,
        'total_comments': len(comments),
        'distributed_analysis': {},
        'semantic_clusters': {},
        'leads': {},
        'context_mapping': {},
        'executive_summary': {},
        'timing': {}
    }
    
    print(f"\n🚀 GOD MODE ANALYSIS: {len(comments)} comments")
    print("=" * 50)
    
    # ========================================
    # 1. DISTRIBUTED MIND (Map-Reduce)
    # ========================================
    if config['enable_distributed'] and len(comments) > 100:
        print("\n📊 [1/4] DISTRIBUTED MIND")
        distributed_result = distributed_analysis(
            comments,
            chunk_size=config['chunk_size'],
            max_workers=config['max_workers']
        )
        report['distributed_analysis'] = distributed_result
    else:
        print("\n📊 [1/4] DISTRIBUTED MIND (skipped - not enough comments)")
        report['distributed_analysis'] = {'status': 'skipped', 'reason': 'Less than 100 comments'}
    
    # ========================================
    # 2. SEMANTIC CLUSTERING
    # ========================================
    if config['enable_clustering']:
        print("\n🔮 [2/4] SEMANTIC CLUSTERING")
        cluster_result = semantic_cluster_analysis(
            comments,
            eps=config['cluster_eps'],
            min_samples=config['cluster_min_samples'],
            model=embedding_model
        )
        report['semantic_clusters'] = {
            'summary': cluster_result.get('summary', ''),
            'cluster_count': cluster_result.get('cluster_count', 0),
            'top_clusters': get_top_clusters(cluster_result, n=10),
            'noise': cluster_result.get('noise', {})
        }
    else:
        print("\n🔮 [2/4] SEMANTIC CLUSTERING (disabled)")
        report['semantic_clusters'] = {'status': 'disabled'}
    
    # ========================================
    # 3. LEAD FUNNEL (Chain-of-Thought)
    # ========================================
    if config['enable_leads']:
        print("\n🎯 [3/4] LEAD FUNNEL")
        lead_result = process_lead_funnel(comments)
        report['leads'] = {
            'summary': lead_result.get('summary', ''),
            'stats': lead_result.get('stats', {}),
            'high_intent': lead_result['leads'].get('high_intent_lead', [])[:10],
            'conquest': lead_result['leads'].get('conquest_opportunity', [])[:10],
            'customer_feedback': lead_result['leads'].get('customer_feedback', [])[:5]
        }
        print(f"   {lead_result.get('summary', '')}")
    else:
        print("\n🎯 [3/4] LEAD FUNNEL (disabled)")
        report['leads'] = {'status': 'disabled'}
    
    # ========================================
    # 4. CONTEXT MAPPING
    # ========================================
    if config['enable_context_mapping'] and transcript_data:
        print("\n🎬 [4/4] CONTEXT MAPPING")
        context_result = map_comments_to_context(comments, transcript_data)
        report['context_mapping'] = {
            'summary': context_result.get('summary', ''),
            'stats': context_result.get('stats', {}),
            'reclassified_examples': [
                c for c in context_result.get('mapped_comments', [])
                if c.get('_has_timestamp') and 
                c.get('_classification', {}).get('contextualized_sentiment') != 
                c.get('_classification', {}).get('original_sentiment')
            ][:5]
        }
        print(f"   {context_result.get('summary', '')}")
    else:
        print("\n🎬 [4/4] CONTEXT MAPPING (skipped - no transcript)")
        report['context_mapping'] = {'status': 'skipped', 'reason': 'No transcript provided'}
    
    # ========================================
    # EXECUTIVE SUMMARY
    # ========================================
    print("\n📝 Generating Executive Summary...")
    report['executive_summary'] = generate_executive_summary(report)
    
    # Timing
    end_time = datetime.now()
    report['timing'] = {
        'start': start_time.isoformat(),
        'end': end_time.isoformat(),
        'duration_seconds': (end_time - start_time).total_seconds()
    }
    
    print(f"\n✅ GOD MODE COMPLETE in {report['timing']['duration_seconds']:.1f}s")
    print("=" * 50)
    
    return report


def generate_executive_summary(report: Dict) -> Dict[str, Any]:
    """Generate executive summary from all analyses."""
    
    # Aggregate sentiment from distributed analysis
    dist = report.get('distributed_analysis', {})
    sentiment = dist.get('aggregate_sentiment', {})
    
    # Get top clusters
    clusters = report.get('semantic_clusters', {})
    top_themes = [c['representative'][:50] for c in clusters.get('top_clusters', [])[:3]]
    
    # Get lead stats
    leads = report.get('leads', {})
    lead_stats = leads.get('stats', {})
    
    # Build summary
    total = report.get('total_comments', 0)
    
    summary = {
        'total_analyzed': total,
        'sentiment': sentiment,
        'top_themes': top_themes,
        'cluster_count': clusters.get('cluster_count', 0),
        'high_intent_leads': lead_stats.get('high_intent_leads', 0),
        'conquest_opportunities': lead_stats.get('conquest_opportunities', 0),
        'key_findings': []
    }
    
    # Generate key findings
    if sentiment.get('positive', 0) > 60:
        summary['key_findings'].append("Predominantly positive audience sentiment")
    elif sentiment.get('negative', 0) > 40:
        summary['key_findings'].append("Significant negative sentiment detected")
    
    if lead_stats.get('high_intent_leads', 0) > 5:
        summary['key_findings'].append(f"Strong buying intent: {lead_stats['high_intent_leads']} potential leads")
    
    if clusters.get('cluster_count', 0) > 0:
        summary['key_findings'].append(f"Comments organized into {clusters['cluster_count']} distinct themes")
    
    return summary


def save_godmode_report(report: Dict, filename: str = 'godmode_report.json'):
    """Save full report to file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    print(f"Report saved to {filename}")


if __name__ == "__main__":
    # Test with sample data
    test_comments = [
        {"text": f"Test comment {i}", "votes": str(i * 10)}
        for i in range(50)
    ]
    
    # Add some realistic comments
    test_comments.extend([
        {"text": "Where can I buy this?", "votes": "100"},
        {"text": "I bought this last year, love it!", "votes": "50"},
        {"text": "Samsung sucks, switching to this", "votes": "30"},
        {"text": "The battery drains so fast", "votes": "200"},
        {"text": "Battery life is terrible", "votes": "150"},
    ])
    
    result = run_godmode_analysis(
        comments=test_comments,
        config={'enable_distributed': False}  # Skip for small test
    )
    
    print("\nExecutive Summary:")
    print(json.dumps(result['executive_summary'], indent=2))
