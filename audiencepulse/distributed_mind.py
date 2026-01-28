"""
Distributed Mind - Map-Reduce Architecture for 10K+ Comments

Solves the "Lost in the Middle" problem with:
1. SHARD: Split comments into chunks (100 each)
2. MAP: Parallel workers analyze each chunk
3. REDUCE: Master AI synthesizes all mini-reports
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


# ============================================
# CONFIGURATION
# ============================================

DEFAULT_CHUNK_SIZE = 100  # Comments per chunk (optimal for context window)
MAX_PARALLEL_WORKERS = 20  # Rate limit safe
ANALYSIS_MODEL = "llama-3.3-70b-versatile"
SYNTHESIS_MODEL = "llama-3.3-70b-versatile"


# ============================================
# SHARD: Split into chunks
# ============================================

def shard_comments(comments: List[Dict], chunk_size: int = DEFAULT_CHUNK_SIZE) -> List[List[Dict]]:
    """
    Split comments into equal-sized chunks for parallel processing.
    
    Args:
        comments: Full list of comments
        chunk_size: Max comments per chunk
    
    Returns:
        List of comment chunks
    """
    chunks = []
    for i in range(0, len(comments), chunk_size):
        chunks.append(comments[i:i + chunk_size])
    return chunks


# ============================================
# MAP: Analyze each chunk
# ============================================

def analyze_chunk(
    client: Groq,
    chunk: List[Dict],
    chunk_id: int,
    model: str = ANALYSIS_MODEL
) -> Dict[str, Any]:
    """
    Analyze a single chunk of comments.
    Each worker is independent - no knowledge of other chunks.
    
    Returns:
        Mini-report with key insights and stats
    """
    # Extract just the text for analysis
    texts = [c.get('text', '')[:200] for c in chunk]  # Truncate for efficiency
    batch_text = "\n".join([f"{i+1}. {t}" for i, t in enumerate(texts)])
    
    prompt = """Analyze these YouTube comments and extract:
1. Key themes/topics (max 5)
2. Sentiment distribution (positive/negative/neutral %)
3. Notable quotes (max 3 representative comments)
4. Pain points mentioned
5. Questions asked
6. Product/brand mentions

Return JSON:
{
    "chunk_id": N,
    "themes": ["theme1", "theme2"],
    "sentiment": {"positive": %, "negative": %, "neutral": %},
    "notable_quotes": ["quote1", "quote2"],
    "pain_points": ["issue1", "issue2"],
    "questions": ["q1", "q2"],
    "mentions": ["brand1", "product1"],
    "comment_count": N
}"""
    
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": batch_text}
            ],
            model=model,
            temperature=0.2,
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        result['chunk_id'] = chunk_id
        result['comment_count'] = len(chunk)
        result['status'] = 'success'
        return result
        
    except Exception as e:
        return {
            'chunk_id': chunk_id,
            'comment_count': len(chunk),
            'status': 'error',
            'error': str(e)
        }


def map_parallel(
    client: Groq,
    chunks: List[List[Dict]],
    max_workers: int = MAX_PARALLEL_WORKERS,
    model: str = ANALYSIS_MODEL
) -> List[Dict[str, Any]]:
    """
    Process all chunks in parallel using thread pool.
    
    Returns:
        List of mini-reports from all workers
    """
    mini_reports = []
    
    # Limit workers to avoid rate limits
    actual_workers = min(max_workers, len(chunks))
    
    with ThreadPoolExecutor(max_workers=actual_workers) as executor:
        # Submit all chunks
        future_to_chunk = {
            executor.submit(analyze_chunk, client, chunk, i, model): i
            for i, chunk in enumerate(chunks)
        }
        
        # Collect results
        for future in as_completed(future_to_chunk):
            chunk_id = future_to_chunk[future]
            try:
                result = future.result()
                mini_reports.append(result)
            except Exception as e:
                mini_reports.append({
                    'chunk_id': chunk_id,
                    'status': 'error',
                    'error': str(e)
                })
    
    # Sort by chunk_id for consistent ordering
    mini_reports.sort(key=lambda x: x.get('chunk_id', 0))
    
    return mini_reports


# ============================================
# REDUCE: Synthesize all mini-reports
# ============================================

def reduce_reports(
    client: Groq,
    mini_reports: List[Dict[str, Any]],
    model: str = SYNTHESIS_MODEL
) -> Dict[str, Any]:
    """
    Master AI synthesizes all mini-reports into unified analysis.
    Finds cross-chunk patterns.
    
    Returns:
        Final comprehensive report
    """
    # Filter successful reports
    successful = [r for r in mini_reports if r.get('status') == 'success']
    failed = [r for r in mini_reports if r.get('status') == 'error']
    
    if not successful:
        return {
            'status': 'error',
            'error': 'All chunks failed',
            'failed_chunks': len(failed)
        }
    
    # Compile reports for synthesis
    reports_text = json.dumps(successful, indent=2)
    
    synthesis_prompt = """You are the Master Synthesizer AI. 
You received analysis from multiple worker AIs, each analyzing a different chunk of YouTube comments.

Your job:
1. Find patterns that appear across MULTIPLE chunks (e.g., "Chunks 1, 5, 18 all mention audio issues")
2. Calculate aggregate sentiment from all chunks
3. Identify the TOP 5 themes across ALL chunks (ranked by frequency)
4. Extract the most impactful quotes
5. List ALL pain points mentioned (with chunk count)
6. Identify cross-cutting questions

Return JSON:
{
    "total_comments_analyzed": N,
    "chunks_processed": N,
    "aggregate_sentiment": {"positive": %, "negative": %, "neutral": %},
    "top_themes": [
        {"theme": "name", "chunks_mentioned": [1,5,18], "estimated_volume": N}
    ],
    "cross_chunk_patterns": ["Pattern across chunks X, Y, Z"],
    "top_pain_points": [{"issue": "name", "chunk_count": N}],
    "key_questions": ["question1", "question2"],
    "notable_quotes": ["quote1", "quote2"],
    "brand_mentions": [{"brand": "name", "sentiment": "pos/neg/neutral"}],
    "executive_summary": "2-3 sentence synthesis"
}"""
    
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": synthesis_prompt},
                {"role": "user", "content": f"Synthesize these {len(successful)} chunk reports:\n\n{reports_text}"}
            ],
            model=model,
            temperature=0.2,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        result['status'] = 'success'
        result['chunks_successful'] = len(successful)
        result['chunks_failed'] = len(failed)
        
        return result
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'chunks_successful': len(successful),
            'chunks_failed': len(failed)
        }


# ============================================
# ORCHESTRATOR: Full Map-Reduce Pipeline
# ============================================

def distributed_analysis(
    comments: List[Dict],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    max_workers: int = MAX_PARALLEL_WORKERS
) -> Dict[str, Any]:
    """
    Full Map-Reduce pipeline for analyzing any number of comments.
    
    Args:
        comments: List of comment dicts
        chunk_size: Comments per chunk
        max_workers: Max parallel workers
    
    Returns:
        Comprehensive synthesized report
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {"status": "error", "error": "GROQ_API_KEY not found"}
    
    client = Groq(api_key=api_key)
    
    # Step 1: SHARD
    chunks = shard_comments(comments, chunk_size)
    
    print(f"📊 Distributed Mind: {len(comments)} comments → {len(chunks)} chunks")
    
    # Step 2: MAP (parallel analysis)
    print(f"🔄 MAP: Processing {len(chunks)} chunks with {min(max_workers, len(chunks))} workers...")
    mini_reports = map_parallel(client, chunks, max_workers)
    
    successful = sum(1 for r in mini_reports if r.get('status') == 'success')
    print(f"✓ MAP complete: {successful}/{len(chunks)} chunks successful")
    
    # Step 3: REDUCE (synthesis)
    print("🧠 REDUCE: Synthesizing all reports...")
    final_report = reduce_reports(client, mini_reports)
    
    if final_report.get('status') == 'success':
        print("✅ Distributed analysis complete!")
    else:
        print(f"⚠️ Synthesis failed: {final_report.get('error')}")
    
    # Add metadata
    final_report['pipeline'] = 'distributed_mind'
    final_report['config'] = {
        'chunk_size': chunk_size,
        'max_workers': max_workers,
        'total_chunks': len(chunks)
    }
    
    return final_report


if __name__ == "__main__":
    # Test with sample data
    test_comments = [
        {"text": f"Comment number {i} about the product"} 
        for i in range(250)
    ]
    
    result = distributed_analysis(test_comments, chunk_size=50)
    print(json.dumps(result, indent=2))
