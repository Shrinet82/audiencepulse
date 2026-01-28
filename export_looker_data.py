import json
import pandas as pd
import argparse
import sys

def export_to_csv(input_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {input_file} not found.")
        sys.exit(1)

    llm_analysis = data.get('llm_analysis', [])
    local_metrics = data.get('local_metrics', [])

    # 1. Sentiment Data
    sentiment_rows = []
    for batch in llm_analysis:
        s = batch.get('sentiment_breakdown', {})
        sentiment_rows.append({
            'Batch_ID': batch.get('batch_id', 0),
            'Positive_Pct': s.get('positive', 0),
            'Negative_Pct': s.get('negative', 0),
            'Neutral_Pct': s.get('neutral', 0),
            'Controversy_Score': batch.get('controversy_score', 0),
            'Summary': batch.get('overall_summary', '')
        })
    pd.DataFrame(sentiment_rows).to_csv('looker_sentiment.csv', index=False)
    print(f"✓ looker_sentiment.csv ({len(sentiment_rows)} rows)")

    # 2. Topics Data
    topic_rows = []
    for batch in llm_analysis:
        for topic in batch.get('top_topics', []):
            topic_rows.append({'Batch_ID': batch.get('batch_id', 0), 'Topic': topic})
    pd.DataFrame(topic_rows).to_csv('looker_topics.csv', index=False)
    print(f"✓ looker_topics.csv ({len(topic_rows)} rows)")

    # 3. Feature Requests
    request_rows = []
    for batch in llm_analysis:
        for req in batch.get('feature_requests', []):
            request_rows.append({'Batch_ID': batch.get('batch_id', 0), 'Request': req})
    pd.DataFrame(request_rows).to_csv('looker_feature_requests.csv', index=False)
    print(f"✓ looker_feature_requests.csv ({len(request_rows)} rows)")

    # 4. Influencer Mentions
    influencer_rows = []
    for batch in llm_analysis:
        for inf in batch.get('influencer_mentions', []):
            influencer_rows.append({'Batch_ID': batch.get('batch_id', 0), 'Influencer': inf})
    pd.DataFrame(influencer_rows).to_csv('looker_influencers.csv', index=False)
    print(f"✓ looker_influencers.csv ({len(influencer_rows)} rows)")

    # 5. Engagement Metrics (from local analysis)
    engagement_rows = []
    for m in local_metrics:
        engagement_rows.append({
            'Batch_ID': m.get('batch_id', 0),
            'Total_Comments': m.get('total_comments', 0),
            'Avg_Length': round(m.get('avg_length', 0), 1),
            'Short_Comments': m.get('short_comments', 0),
            'Long_Comments': m.get('long_comments', 0),
            'Questions': m.get('questions', 0),
            'Question_Rate_Pct': m.get('question_rate', 0),
            'Positive_Emojis': m.get('positive_emojis', 0),
            'Negative_Emojis': m.get('negative_emojis', 0),
            'Total_Votes': m.get('total_votes', 0),
            'Total_Replies': m.get('total_replies', 0),
            'Potential_Spam': m.get('potential_spam', 0)
        })
    pd.DataFrame(engagement_rows).to_csv('looker_engagement.csv', index=False)
    print(f"✓ looker_engagement.csv ({len(engagement_rows)} rows)")

    # 6. Aggregated Summary (single row for scorecards)
    agg = {
        'Total_Batches': len(local_metrics),
        'Total_Comments': sum(m.get('total_comments', 0) for m in local_metrics),
        'Avg_Positive_Pct': round(sum(b.get('sentiment_breakdown', {}).get('positive', 0) for b in llm_analysis) / len(llm_analysis), 1) if llm_analysis else 0,
        'Avg_Negative_Pct': round(sum(b.get('sentiment_breakdown', {}).get('negative', 0) for b in llm_analysis) / len(llm_analysis), 1) if llm_analysis else 0,
        'Avg_Controversy': round(sum(b.get('controversy_score', 0) for b in llm_analysis) / len(llm_analysis), 1) if llm_analysis else 0,
        'Total_Questions': sum(m.get('questions', 0) for m in local_metrics),
        'Total_Votes': sum(m.get('total_votes', 0) for m in local_metrics),
        'Total_Spam_Detected': sum(m.get('potential_spam', 0) for m in local_metrics),
    }
    pd.DataFrame([agg]).to_csv('looker_summary.csv', index=False)
    print(f"✓ looker_summary.csv (1 row)")

    print("\n🎉 All CSVs ready for Looker Studio!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export enhanced analysis to Looker CSVs.")
    parser.add_argument("input_file", help="Input JSON analysis file (analysis_full.json)")
    args = parser.parse_args()
    export_to_csv(args.input_file)
