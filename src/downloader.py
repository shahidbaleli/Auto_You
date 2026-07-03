import os
import requests
import tempfile
from pathlib import Path

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
PEXELS_SEARCH_URL = "https://api.pexels.com/videos/search"
HEADERS = {"Authorization": PEXELS_API_KEY}


class VideoDownloader:
    def __init__(self):
        if not PEXELS_API_KEY:
            raise ValueError("PEXELS_API_KEY environment variable not set")

    def search_clips(self, keywords: list[str], per_page: int = 5) -> list[dict]:
        seen = set()
        clips = []
        for kw in keywords:
            params = {"query": kw, "per_page": min(per_page, 5), "orientation": "portrait"}
            resp = requests.get(PEXELS_SEARCH_URL, headers=HEADERS, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            for video in data.get("videos", []):
                vid_id = video["id"]
                if vid_id in seen:
                    continue
                seen.add(vid_id)
                for file in video.get("video_files", []):
                    if file["quality"] in ("sd", "hd") and file.get("link"):
                        clips.append({
                            "id": vid_id,
                            "url": file["link"],
                            "width": file.get("width", 0),
                            "height": file.get("height", 0),
                            "duration": video.get("duration", 10),
                        })
                        break
                if len(clips) >= 5:
                    break
            if len(clips) >= 5:
                break
        return clips[:5]

    def download_clip(self, clip: dict, output_dir: str) -> str | None:
        url = clip["url"]
        ext = Path(url.split("?")[0]).suffix or ".mp4"
        out_path = os.path.join(output_dir, f"clip_{clip['id']}{ext}")
        try:
            resp = requests.get(url, stream=True, timeout=60)
            resp.raise_for_status()
            with open(out_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            return out_path
        except Exception as e:
            print(f"  Failed to download clip {clip['id']}: {e}")
            return None

    def download_all(self, keywords: list[str], output_dir: str | None = None) -> list[str]:
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="shorts_")
        else:
            os.makedirs(output_dir, exist_ok=True)

        print("Searching Pexels for video clips...")
        clips = self.search_clips(keywords)
        print(f"  Found {len(clips)} clips")

        paths = []
        for clip in clips:
            path = self.download_clip(clip, output_dir)
            if path:
                paths.append(path)
        return paths
