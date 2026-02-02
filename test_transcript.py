from audiencepulse.video_analyzer import get_transcript, extract_video_id
import sys

url = "https://www.youtube.com/watch?v=y3cwyI5i95s" # iPad Pro M4 video
print(f"Testing URL: {url}")

vid = extract_video_id(url)
print(f"Extracted ID: '{vid}'")

try:
    data = get_transcript(url)
    if 'error' in data:
        print(f"❌ Error: {data['error']}")
    elif data.get('segments'):
        print(f"✅ Success! Got {len(data['segments'])} segments.")
        print(f"Word count: {data.get('word_count')}")
    else:
        print("⚠️ No segments found (but no error).")
except Exception as e:
    print(f"❌ Exception: {e}")
