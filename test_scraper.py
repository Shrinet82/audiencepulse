import yt_dlp
import json
import sys

def test_scrape(url):
    ydl_opts = {
        'skip_download': True,
        'writeinfojson': False,
        'getcomments': True,
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        # 'user_agent': ... let library decide
    }

    print(f"Testing {url}...")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Note: extract_flat=True usually doesn't get comments. We might need full extraction.
            # Let's try full extraction but skip download.
            ydl_opts['extract_flat'] = False 
            
            info = ydl.extract_info(url, download=False)
            comments = info.get('comments', [])
            
            print(f"Title: {info.get('title')}")
            print(f"Comments found: {len(comments)}")
            
            if comments:
                print("First comment:", comments[0].get('text'))
            else:
                print("No comments found in 'comments' key. Checking 'entries'...")
                # Sometimes comments are in entries? No, entries are for playlists.
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Test with the video I tried before or a generic popular one
    test_scrape("https://www.youtube.com/watch?v=9t78gqKrkbE")
