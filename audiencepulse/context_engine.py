"""
Context Engine - Creates video context for transcript-aware comment analysis.

Flow:
1. Get transcript from video_analyzer
2. Chunk into manageable segments
3. Summarize to create "Context Object" (~300 tokens)
4. Use Context Object to enhance comment analysis
"""

import os
import re
from typing import Dict, List, Optional, Any
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


def chunk_transcript(transcript: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
    """
    Split transcript into overlapping chunks.
    
    Args:
        transcript: Full transcript text
        chunk_size: Target characters per chunk (~500 tokens)
        overlap: Overlap between chunks for context continuity
    
    Returns:
        List of transcript chunks
    """
    if not transcript:
        return []
    
    # Clean transcript
    transcript = re.sub(r'\s+', ' ', transcript).strip()
    
    if len(transcript) <= chunk_size:
        return [transcript]
    
    chunks = []
    start = 0
    
    while start < len(transcript):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(transcript):
            # Look for sentence end within last 20% of chunk
            search_start = end - int(chunk_size * 0.2)
            sentence_end = transcript.rfind('. ', search_start, end)
            if sentence_end > search_start:
                end = sentence_end + 1
        
        chunks.append(transcript[start:end].strip())
        start = end - overlap
    
    return chunks


def summarize_chunk(client: Groq, chunk: str, model: str = "llama-3.1-8b-instant") -> str:
    """Summarize a single transcript chunk."""
    try:
        response = client.chat.completions.create(
            messages=[{
                "role": "system",
                "content": "Summarize this video transcript segment in 2-3 sentences. Focus on: main topics, products/brands mentioned, any controversial claims."
            }, {
                "role": "user",
                "content": chunk
            }],
            model=model,
            temperature=0.3,
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"


def create_context_object(
    transcript: str,
    title: str = "",
    description: str = "",
    model: str = "llama-3.1-8b-instant"
) -> Dict[str, Any]:
    """
    Create a Context Object from video transcript and metadata.
    
    Args:
        transcript: Video transcript text
        title: Video title
        description: Video description
        model: LLM model for summarization
    
    Returns:
        Context Object with summary, topics, and claims
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {"error": "GROQ_API_KEY not found"}
    
    client = Groq(api_key=api_key)
    
    # Handle missing transcript
    if not transcript or len(transcript.strip()) < 100:
        # Fallback: use title + description
        fallback_context = f"Video: {title}\n{description}"
        return {
            "summary": f"Video titled '{title}'. No transcript available.",
            "core_topics": [title] if title else [],
            "products_mentioned": [],
            "controversial_claims": [],
            "context_source": "metadata_only",
            "token_estimate": len(fallback_context.split())
        }
    
    # Chunk and summarize transcript
    chunks = chunk_transcript(transcript, chunk_size=3000)
    
    if len(chunks) == 1:
        # Short video - single summarization
        summaries = [summarize_chunk(client, chunks[0], model)]
    else:
        # Long video - summarize each chunk
        summaries = []
        for i, chunk in enumerate(chunks[:5]):  # Max 5 chunks to limit tokens
            summary = summarize_chunk(client, chunk, model)
            summaries.append(summary)
    
    combined_summary = " ".join(summaries)
    
    # Final synthesis to create structured Context Object
    try:
        response = client.chat.completions.create(
            messages=[{
                "role": "system",
                "content": """Analyze this video summary and return JSON:
{
    "summary": "2-3 sentence overview",
    "core_topics": ["topic1", "topic2", "topic3"],
    "products_mentioned": ["product1", "brand1"],
    "controversial_claims": ["claim1", "claim2"],
    "creator_stance": "positive/negative/neutral on main topic"
}"""
            }, {
                "role": "user",
                "content": f"Title: {title}\n\nSummary: {combined_summary}"
            }],
            model=model,
            temperature=0.3,
            max_tokens=300,
            response_format={"type": "json_object"}
        )
        
        import json
        context = json.loads(response.choices[0].message.content)
        context["context_source"] = "transcript"
        context["chunks_processed"] = len(chunks)
        context["token_estimate"] = len(combined_summary.split())
        
        return context
        
    except Exception as e:
        return {
            "error": str(e),
            "summary": combined_summary[:500],
            "context_source": "partial"
        }


def enhance_analysis_prompt(context_object: Dict, base_prompt: str) -> str:
    """
    Enhance analysis prompt with video context.
    
    Instead of "Is this positive?", we ask "Does this agree with the creator?"
    """
    if not context_object or "error" in context_object:
        return base_prompt
    
    context_section = f"""
VIDEO CONTEXT:
- Summary: {context_object.get('summary', 'N/A')}
- Topics: {', '.join(context_object.get('core_topics', []))}
- Products: {', '.join(context_object.get('products_mentioned', []))}
- Controversial Claims: {', '.join(context_object.get('controversial_claims', []))}
- Creator Stance: {context_object.get('creator_stance', 'N/A')}

ANALYSIS INSTRUCTIONS:
When analyzing comments, consider:
1. Does the comment AGREE or DISAGREE with the creator's claims?
2. Does it validate or challenge the controversial points?
3. Is it asking about mentioned products/topics?
"""
    
    return context_section + "\n\n" + base_prompt


def get_context_aware_prompt() -> str:
    """Get the context-aware analysis prompt."""
    return """Analyze YouTube comments WITH video context. Return JSON:
{
    "sentiment_breakdown": {"positive": %, "negative": %, "neutral": %},
    "agreement_with_creator": {"agree": %, "disagree": %, "unrelated": %},
    "top_topics": ["t1", "t2", "t3"],
    "validated_claims": ["claim that comments support"],
    "challenged_claims": ["claim that comments dispute"],
    "product_interest": ["product people ask about"],
    "controversy_score": 0-100,
    "overall_summary": "1-2 sentences"
}"""


if __name__ == "__main__":
    # Test
    test_transcript = """
    Today we're reviewing the new iPhone 16 Pro. The camera is amazing but I noticed 
    it overheats during long video recordings. Apple claims 4-hour battery life but 
    in my tests it lasted only 3 hours. The price at $1199 is steep compared to 
    Samsung Galaxy which offers similar features for $999.
    """
    
    context = create_context_object(
        transcript=test_transcript,
        title="iPhone 16 Pro Honest Review"
    )
    
    import json
    print(json.dumps(context, indent=2))
