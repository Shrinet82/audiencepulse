import argparse
import json
import itertools
from youtube_comment_downloader import YoutubeCommentDownloader
import pandas as pd
import sys
from tqdm import tqdm
import signal

def get_comments(url, output_file, limit=None):
    downloader = YoutubeCommentDownloader()
    try:
        print(f"Fetching comments for {url}...")
        # sort_by=1 for relevant, 0 for newest
        comments = downloader.get_comments_from_url(url, sort_by=1) 
        
        # Generator for processing
        iterator = comments
        if limit:
            iterator = itertools.islice(comments, limit)

        count = 0
        pbar = tqdm(desc="Fetching comments", unit=" comments")
        
        # Open file in append mode or streaming mode
        f_json = None
        f_csv = None
        
        if output_file:
            if output_file.endswith('.json') or output_file.endswith('.jsonl'):
                # Using JSON Lines format which is better for streaming
                f_json = open(output_file, 'w', encoding='utf-8')
            elif output_file.endswith('.csv'):
                f_csv = open(output_file, 'w', encoding='utf-8')
                # We need to know headers, so we might delay first write or just assume standard fields
                # For simplicity, we'll write headers on first item
            else:
                print(f"Unsupported streaming format for {output_file}. Only .json (jsonlines) and .csv supported for large scrapes.")
                sys.exit(1)

        headers_written = False

        try:
            for comment in iterator:
                count += 1
                pbar.update(1)
                
                if f_json:
                    f_json.write(json.dumps(comment, ensure_ascii=False) + '\n')
                    f_json.flush() # Ensure data is written
                elif f_csv:
                    df = pd.DataFrame([comment])
                    if not headers_written:
                        df.to_csv(f_csv, index=False, encoding='utf-8', header=True)
                        headers_written = True
                    else:
                        df.to_csv(f_csv, index=False, encoding='utf-8', header=False)
                    f_csv.flush()
                else:
                    # Print to console if no file, but only first 10 to avoid spam
                    if count <= 10:
                        print(comment.get('text', ''))

        except KeyboardInterrupt:
            print("\nScraping interrupted by user. Saving progress...")

        finally:
            pbar.close()
            if f_json:
                f_json.close()
                print(f"\nSaved {count} comments to {output_file} (JSON Lines format).")
            if f_csv:
                f_csv.close()
                print(f"\nSaved {count} comments to {output_file}.")

    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Scrape YouTube comments from a video URL.")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("-o", "--output", help="Output filename (json, csv)")
    parser.add_argument("-l", "--limit", type=int, help="Limit number of comments to download")
    
    args = parser.parse_args()
    
    get_comments(args.url, args.output, args.limit)

if __name__ == "__main__":
    main()
