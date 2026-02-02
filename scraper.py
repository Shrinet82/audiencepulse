import argparse
import json
import sys
import random
import time
import yt_dlp
import os
from datetime import datetime

# Mock comments removed by user request.



def get_comments(url, output_file, limit=None):
    comments = []
    metadata = {}

    # METHOD 1: OFFICIAL API (Priority)
    import streamlit as st
    api_key = None
    try:
        if "youtube" in st.secrets:
            api_key = st.secrets["youtube"]["api_key"]
    except:
        pass
    
    # Fallback to Env Var
    if not api_key:
        api_key = os.environ.get("YOUTUBE_API_KEY")

    if api_key:
        print("🔑 YouTube API Key found! Using Official Data API.")
        try:
            from googleapiclient.discovery import build
            youtube = build('youtube', 'v3', developerKey=api_key)
            
            # Extract Video ID
            if "v=" in url:
                video_id = url.split('v=')[-1].split('&')[0]
            elif "youtu.be/" in url:
                video_id = url.split('youtu.be/')[-1].split('?')[0]
            else:
                video_id = url # Assumption or error checking could go here
            
            # Pagination Loop
            next_page_token = None
            max_limit = limit if limit else 2000 # User requested scale up to 2000
            
            while len(comments) < max_limit:
                request = youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    maxResults=100,
                    order="relevance", # Fetches "Top comments" (most liked/replied) first
                    textFormat="plainText",
                    pageToken=next_page_token
                )
                response = request.execute()
                
                for item in response.get('items', []):
                    snippet = item['snippet']['topLevelComment']['snippet']
                    comments.append({
                        'text': snippet['textDisplay'],
                        'author': snippet['authorDisplayName'],
                        'votes': snippet['likeCount'],
                        'published_at': snippet['publishedAt']
                    })
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
                    
                print(f"   ...fetched {len(comments)} comments so far")
            
            success = True
            print(f"✅ API Success! Got {len(comments)} comments.")

        except Exception as e:
            print(f"⚠️ API Failed: {e}. Falling back to Scraper.")

    # METHOD 2: SCRAPER (Fallback)
    if not success:
        ydl_opts = {
            'skip_download': True,
            'extract_flat': True,
            'getcomments': True,
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {'youtube': {'player_client': ['web']}},
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # CHECK FOR COOKIES
        if os.path.exists('cookies.txt'):
            print("🍪 Cookies found! Using 'cookies.txt' for authentication.")
            ydl_opts['cookiefile'] = 'cookies.txt'
        else:
            print("⚠️ No cookies.txt found. Scraper might fail on Cloud IPs.")

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print(f"Fetching comments for {url} via Scraper...")
                info = ydl.extract_info(url, download=False)
                cwd_comments = info.get('comments')
                
                if cwd_comments:
                    comments = cwd_comments
                    success = True
                    print(f"✅ Scraper Success! Got {len(comments)} comments.")
                else:
                    print("❌ Scraper returned 0 comments. Possibly blocked.")
                    
        except Exception as e:
            print(f"❌ Scraper Failed: {e}")
    
    # OUTPUT
    count = 0
    if output_file and comments:
        mode = 'w'
        with open(output_file, mode, encoding='utf-8') as f:
            for comment in comments:
                # Normalize typical fields
                c_obj = {
                    'text': comment.get('text') or comment.get('content'),
                    'author': comment.get('author') or comment.get('uploader'),
                    'votes': comment.get('like_count', 0),
                    'published_at': comment.get('timestamp')
                }
                f.write(json.dumps(c_obj, ensure_ascii=False) + '\n')
                count += 1
                if limit and count >= limit:
                    break
        print(f"Saved {count} comments to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Scrape YouTube comments from a video URL.")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("-o", "--output", help="Output filename (json, csv)")
    parser.add_argument("-l", "--limit", type=int, help="Limit number of comments to download")
    
    args = parser.parse_args()
    get_comments(args.url, args.output, args.limit)

if __name__ == "__main__":
    main()
