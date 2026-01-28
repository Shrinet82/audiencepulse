#!/usr/bin/env python3
"""
YouTube Comment Analysis Pipeline
==================================
Usage: python pipeline.py <VIDEO_URL> [--limit N]

This runs the full pipeline:
1. Scrape comments from YouTube video
2. Analyze with Groq LLM (10 metrics)
3. Export to Looker-ready CSVs
"""

import argparse
import subprocess
import sys
import os
from datetime import datetime

def run_step(name, cmd):
    """Run a pipeline step and handle errors."""
    print(f"\n{'='*50}")
    print(f"🔹 {name}")
    print(f"{'='*50}")
    
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode != 0:
        print(f"❌ {name} FAILED (exit code {result.returncode})")
        sys.exit(1)
    
    print(f"✓ {name} completed")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="YouTube Comment Analysis Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pipeline.py https://youtu.be/VIDEO_ID
  python pipeline.py https://youtu.be/VIDEO_ID --limit 500
  python pipeline.py https://youtu.be/VIDEO_ID --output my_analysis
        """
    )
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("-l", "--limit", type=int, help="Limit comments to scrape")
    parser.add_argument("-o", "--output", default="pipeline_output", help="Output directory name")
    
    args = parser.parse_args()
    
    # Check API key
    if not os.getenv("GROQ_API_KEY"):
        print("❌ Error: GROQ_API_KEY environment variable not set")
        print("   Run: export GROQ_API_KEY='your_key'")
        sys.exit(1)
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"{args.output}_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    comments_file = f"{output_dir}/comments.jsonl"
    analysis_file = f"{output_dir}/analysis_full.json"
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║           YouTube Comment Analysis Pipeline                  ║
╠══════════════════════════════════════════════════════════════╣
║  URL:    {args.url[:50]}...
║  Output: {output_dir}
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Step 1: Scrape
    limit_arg = f"--limit {args.limit}" if args.limit else ""
    run_step("Step 1: Scraping Comments", 
             f'python3 scraper.py "{args.url}" -o "{comments_file}" {limit_arg}')
    
    # Step 2: Analyze
    run_step("Step 2: AI Analysis (Groq LLM)",
             f'python3 analyze_groq.py "{comments_file}"')
    
    # Move analysis outputs
    os.rename('analysis_full.json', analysis_file)
    if os.path.exists('comments_for_chat.json'):
        os.rename('comments_for_chat.json', f'{output_dir}/comments_for_chat.json')
    
    # Step 3: Export
    run_step("Step 3: Exporting Looker CSVs",
             f'python3 export_looker_data.py "{analysis_file}"')
    
    # Step 4: Upload to Sheets (Optional)
    if os.path.exists("service_account.json"):
        run_step("Step 4: Uploading to Google Sheets",
                 f'python3 upload_to_sheets.py "{output_dir}"')
    else:
        print("\nℹ️  Skipping Google Sheets upload (service_account.json not found)")

    # Move CSV outputs
    csv_files = ['looker_sentiment.csv', 'looker_topics.csv', 'looker_engagement.csv',
                 'looker_feature_requests.csv', 'looker_influencers.csv', 'looker_summary.csv']
    for f in csv_files:
        if os.path.exists(f):
            if os.path.exists(f'{output_dir}/{f}'):
                 os.remove(f'{output_dir}/{f}') # Clean overwrite
            os.rename(f, f'{output_dir}/{f}')
    
    # Summary
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    ✅ PIPELINE COMPLETE                      ║
╠══════════════════════════════════════════════════════════════╣
║  Output Directory: {output_dir}
║  
║  Files Generated:
║    📄 comments.jsonl         - Raw scraped comments
║    📊 analysis_full.json     - Full AI analysis
║    📈 looker_*.csv           - 6 Looker-ready CSVs
║
║  Next Steps:
║    1. Upload CSVs to Google Sheets
║    2. Connect to Looker Studio
║    3. Run: streamlit run app.py (for chat Q&A)
╚══════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    main()
