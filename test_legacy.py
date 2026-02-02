from youtube_comment_downloader import YoutubeCommentDownloader
import itertools

def test_legacy(url):
    print(f"Testing Legacy Downloader for {url}...")
    try:
        downloader = YoutubeCommentDownloader()
        comments = downloader.get_comments_from_url(url, sort_by=1) # 1 = Top, 0 = Newest
        
        # Try to get 5 comments
        iterator = itertools.islice(comments, 5)
        count = 0
        for comment in iterator:
            print(f"- {comment['text'][:50]}...")
            count += 1
            
        if count > 0:
            print(f"✅ Success! Got {count} comments.")
        else:
            print("❌ Zero comments returned (Generator empty).")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_legacy("https://www.youtube.com/watch?v=9t78gqKrkbE")
