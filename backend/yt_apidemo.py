"""
yt search api demo and boilerplate
- https://developers.google.com/youtube/v3/docs/search/list
- https://developers.google.com/youtube/v3/docs/videos/list
usage:
    python youtube_apidemo.py --query "bench press" --limit 5
"""

import argparse
import json
import sys
from urllib import request, parse, error

API_KEY = "AIzaSyB1fVoyoG-KBQZ9GhVTRRxseFTCgGos1Fo"

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"

def http_get(url, params):
    url = f"{url}?{parse.urlencode(params)}"
    req = request.Request(url)
    try:
        with request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as e:
        sys.stderr.write(f"[HTTP ERROR] {e.code} {e.reason}\n")
        body = e.read().decode("utf-8", "ignore")
        if body:
            sys.stderr.write(body + "\n")
        sys.exit(1)
    except error.URLError as e:
        sys.stderr.write(f"[URL ERROR] {e.reason}\n")
        sys.exit(1)


def search_videos(query, limit=5, order="relevance"):
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": limit,
        "order": order,
        "key": API_KEY,
    }
    data = http_get(SEARCH_URL, params)
    return data.get("items", [])


def get_video_details(video_ids):
    if not video_ids:
        return []
    params = {
        "part": "snippet,statistics,contentDetails",
        "id": ",".join(video_ids),
        "key": API_KEY,
    }
    data = http_get(VIDEOS_URL, params)
    return data.get("items", [])


def main():
    parser = argparse.ArgumentParser(description="YouTube Search + Video Details (hardcoded API key)")
    parser.add_argument("--query", required=True, help="Search query term")
    parser.add_argument("--limit", type=int, default=5, help="Number of results to retrieve (default 5)")
    parser.add_argument("--order", default="relevance",
                        help="Search order: date, rating, relevance, title, videoCount, viewCount")
    args = parser.parse_args()

    search_items = search_videos(args.query, args.limit, args.order)
    video_ids = [item["id"]["videoId"] for item in search_items if item["id"]["kind"] == "youtube#video"]

    if not video_ids:
        print("No videos found.")
        return

    details = get_video_details(video_ids)
    details_by_id = {d["id"]: d for d in details}

    for idx, item in enumerate(search_items, 1):
        vid = item["id"]["videoId"]
        snippet = item["snippet"]
        title = snippet.get("title")
        channel = snippet.get("channelTitle")
        published = snippet.get("publishedAt")

        print(f"\n[{idx}] {title}")
        print(f"    Video ID:   {vid}")
        print(f"    Channel:    {channel}")
        print(f"    Published:  {published}")

        full = details_by_id.get(vid)
        if full:
            stats = full.get("statistics", {})
            view_count = stats.get("viewCount", "N/A")
            like_count = stats.get("likeCount", "N/A")
            print(f"    Views:      {view_count}")
            print(f"    Likes:      {like_count}")
        else:
            print("    (No additional stats found)")

    print("\nDone.")


if __name__ == "__main__":
    main()


#NOTE NOTE NOTE youtube links and embeddings are assembled via the videoID pulled here. need to add a module that
#can build an embed link from this data and make it accessible to the JS front end. todo for increment 3.