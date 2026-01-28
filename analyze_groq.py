import os
import argparse
import json
import re
import sys
from groq import Groq
from tqdm import tqdm
from dotenv import load_dotenv
from collections import Counter
from difflib import SequenceMatcher

load_dotenv()

# Emoji patterns
POSITIVE_EMOJIS = set(['😀', '😃', '😄', '😁', '😆', '🥹', '😅', '🤣', '😂', '🙂', '😊', '😇', '🥰', '😍', '🤩', '😘', '😗', '☺', '😚', '😙', '🥲', '😋', '😛', '😜', '🤪', '😝', '👍', '👏', '🙌', '🎉', '❤️', '💕', '💖', '💗', '💓', '💞', '💘', '🔥', '✨', '⭐', '🌟', '💯', '✅', '👌', '🤝', '💪'])
NEGATIVE_EMOJIS = set(['😞', '😔', '😟', '😕', '🙁', '☹', '😣', '😖', '😫', '😩', '🥺', '😢', '😭', '😤', '😠', '😡', '🤬', '👎', '💔', '😒', '😑', '😐', '🙄', '😬', '😮‍💨', '😵', '🤢', '🤮', '💩', '🖕', '❌', '⛔'])

# ============================================
# TOKEN OPTIMIZATION UTILITIES
# ============================================

def truncate_comment(text, max_chars=200):
    """Truncate long comments while preserving meaning."""
    if len(text) <= max_chars:
        return text
    # Try to cut at sentence/word boundary
    truncated = text[:max_chars]
    last_space = truncated.rfind(' ')
    if last_space > max_chars * 0.7:
        truncated = truncated[:last_space]
    return truncated + "..."

def is_similar(text1, text2, threshold=0.85):
    """Check if two texts are similar (for deduplication)."""
    if len(text1) < 20 or len(text2) < 20:
        return text1.lower() == text2.lower()
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio() > threshold

def deduplicate_comments(comments, similarity_threshold=0.85):
    """Remove duplicate/very similar comments, keeping the one with most votes."""
    if not comments:
        return comments
    
    # Sort by votes (descending) to keep high-engagement versions
    def get_votes(c):
        v = c.get('votes', '0')
        try:
            if 'k' in str(v).lower():
                return int(float(str(v).lower().replace('k', '')) * 1000)
            return int(v) if v else 0
        except:
            return 0
    
    sorted_comments = sorted(comments, key=get_votes, reverse=True)
    unique = []
    seen_texts = []
    
    for comment in sorted_comments:
        text = comment.get('text', '')
        is_dup = False
        for seen in seen_texts:
            if is_similar(text, seen, similarity_threshold):
                is_dup = True
                break
        if not is_dup:
            unique.append(comment)
            seen_texts.append(text)
    
    return unique

def compress_for_llm(comments, max_chars=200):
    """Prepare comments for LLM: truncate and format efficiently."""
    compressed = []
    for c in comments:
        text = truncate_comment(c.get('text', ''), max_chars)
        # Use compact format: just numbered text
        compressed.append(text)
    return compressed


# ============================================
# LOCAL METRICS (No LLM needed)
# ============================================

def extract_local_metrics(comments_batch):
    """Extract metrics that don't need LLM (faster, cheaper)."""
    metrics = {
        'total_comments': len(comments_batch),
        'avg_length': 0,
        'short_comments': 0,
        'long_comments': 0,
        'questions': 0,
        'positive_emojis': 0,
        'negative_emojis': 0,
        'total_votes': 0,
        'total_replies': 0,
        'potential_spam': 0,
    }

    lengths = []
    for c in comments_batch:
        text = c.get('text', '')
        length = len(text)
        lengths.append(length)

        if length < 20:
            metrics['short_comments'] += 1
        elif length > 100:
            metrics['long_comments'] += 1

        if '?' in text:
            metrics['questions'] += 1

        for char in text:
            if char in POSITIVE_EMOJIS:
                metrics['positive_emojis'] += 1
            elif char in NEGATIVE_EMOJIS:
                metrics['negative_emojis'] += 1

        votes_str = c.get('votes', '0')
        try:
            if 'k' in str(votes_str).lower():
                votes = int(float(votes_str.lower().replace('k', '')) * 1000)
            elif 'm' in str(votes_str).lower():
                votes = int(float(votes_str.lower().replace('m', '')) * 1000000)
            else:
                votes = int(votes_str) if votes_str else 0
        except:
            votes = 0
        metrics['total_votes'] += votes

        replies_str = c.get('replies', '0')
        try:
            if 'k' in str(replies_str).lower():
                replies = int(float(replies_str.lower().replace('k', '')) * 1000)
            else:
                replies = int(replies_str) if replies_str else 0
        except:
            replies = 0
        metrics['total_replies'] += replies

        if length < 10 and votes == 0:
            metrics['potential_spam'] += 1

    metrics['avg_length'] = sum(lengths) / len(lengths) if lengths else 0
    metrics['question_rate'] = round(metrics['questions'] / len(comments_batch) * 100, 1) if comments_batch else 0

    return metrics


# ============================================
# MAIN ANALYSIS
# ============================================

def analyze_comments(input_file, model="llama-3.3-70b-versatile"):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY not found.")
        sys.exit(1)

    client = Groq(api_key=api_key)

    # Load comments
    comments_data = []
    print(f"Reading comments from {input_file}...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get('text', '').strip():
                        comments_data.append(data)
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        print(f"File {input_file} not found.")
        sys.exit(1)

    if not comments_data:
        print("No comments found.")
        sys.exit(0)

    original_count = len(comments_data)
    print(f"Loaded {original_count} comments.")

    # OPTIMIZATION 1: Deduplicate similar comments
    comments_data = deduplicate_comments(comments_data, similarity_threshold=0.80)
    deduped_count = len(comments_data)
    print(f"After deduplication: {deduped_count} unique comments ({original_count - deduped_count} duplicates removed)")

    # OPTIMIZATION 2: Larger batches (75 instead of 50)
    batch_size = 75
    
    # OPTIMIZATION 3: Compact prompt (same structure, fewer tokens)
    system_prompt = """Analyze YouTube comments. Return ONLY JSON:
{"sentiment_breakdown":{"positive":%,"negative":%,"neutral":%},"top_topics":["t1","t2","t3"],"controversy_score":0-100,"feature_requests":["r1"],"influencer_mentions":["@m1"],"overall_summary":"1-2 sentences"}"""

    all_results = []
    all_local_metrics = []

    num_batches = (len(comments_data) + batch_size - 1) // batch_size
    print(f"Analyzing {num_batches} batches (batch_size={batch_size})...")

    for i in tqdm(range(0, len(comments_data), batch_size)):
        batch = comments_data[i:i + batch_size]
        
        # OPTIMIZATION 4: Truncate long comments
        batch_texts = compress_for_llm(batch, max_chars=200)
        # Use compact separator
        batch_text = "\n".join([f"{j+1}:{t}" for j, t in enumerate(batch_texts)])

        # Local metrics (fast, no API)
        local_metrics = extract_local_metrics(batch)
        local_metrics['batch_id'] = (i // batch_size) + 1
        all_local_metrics.append(local_metrics)

        # LLM analysis
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": batch_text}
                ],
                model=model,
                temperature=0.3,
                max_tokens=512,  # Reduced from 1024
                response_format={"type": "json_object"}
            )
            result = json.loads(chat_completion.choices[0].message.content)
            result['batch_id'] = (i // batch_size) + 1
            all_results.append(result)
        except Exception as e:
            print(f"Error batch {(i // batch_size) + 1}: {e}")

    # Save results
    with open('analysis_full.json', 'w', encoding='utf-8') as f:
        json.dump({'llm_analysis': all_results, 'local_metrics': all_local_metrics}, f, indent=2)

    print(f"\nSaved full analysis to analysis_full.json")
    print(f"Token efficiency: {original_count} -> {deduped_count} comments, {num_batches} batches")

    # Quick summary
    if all_results:
        print("\n--- Sample Analysis (Batch 1) ---")
        print(json.dumps(all_results[0], indent=2))

    # Store raw comments for chat
    with open('comments_for_chat.json', 'w', encoding='utf-8') as f:
        json.dump([c.get('text', '') for c in comments_data], f, ensure_ascii=False)
    print(f"Saved {len(comments_data)} comments for chat context.")


def main():
    parser = argparse.ArgumentParser(description="Enhanced YouTube comment analysis.")
    parser.add_argument("input_file", help="Input JSONL file")
    args = parser.parse_args()
    analyze_comments(args.input_file)


if __name__ == "__main__":
    main()
