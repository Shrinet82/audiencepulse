from googleapiclient.discovery import build
import streamlit as st
import toml

# Load secrets manually for test script
try:
    secrets = toml.load(".streamlit/secrets.toml")
    api_key = secrets["youtube"]["api_key"]
    print(f"🔑 Loaded Key: {api_key[:10]}...")
except Exception as e:
    print(f"❌ Failed to load key: {e}")
    exit(1)

def test_api(url):
    print(f"Testing API for {url}...")
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        # Extract Video ID
        if "v=" in url:
            video_id = url.split('v=')[-1].split('&')[0]
        elif "youtu.be/" in url:
            video_id = url.split('youtu.be/')[-1].split('?')[0]
        else:
            video_id = url

        # Get Total Count
        stats_req = youtube.videos().list(part="statistics", id=video_id)
        stats_resp = stats_req.execute()
        total_comments = 0
        if stats_resp['items']:
            total_comments = stats_resp['items'][0]['statistics'].get('commentCount', 0)
        
        print(f"📊 Total Comments on Video: {total_comments}")

        # Request Comments
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            order="relevance",
            textFormat="plainText"
        )
        response = request.execute()
        
        count = 0
        for item in response.get('items', []):
            snippet = item['snippet']['topLevelComment']['snippet']
            # print(f"- [{snippet['authorDisplayName']}] {snippet['textDisplay'][:50]}...")
            count += 1
            
        print(f"✅ API Success! Fetched {count} relevant comments.")

    except Exception as e:
        print(f"❌ API Failed: {e}")

if __name__ == "__main__":
    test_api("https://youtu.be/Kn8OTMHhcDE?si=5zPlDf1cbadwtgdo")
