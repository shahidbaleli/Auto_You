import os
import requests

PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY")
PIXABAY_MUSIC_URL = "https://pixabay.com/api/music/"


class MusicDownloader:
    def __init__(self):
        self.enabled = bool(PIXABAY_API_KEY)

    def download(self, keywords: list[str], output_dir: str) -> str | None:
        if not self.enabled:
            print("  No PIXABAY_API_KEY set — skipping background music")
            return None
        for kw in keywords:
            try:
                params = {"key": PIXABAY_API_KEY, "q": kw, "per_page": 3}
                resp = requests.get(PIXABAY_MUSIC_URL, params=params, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                hits = data.get("hits", [])
                if hits:
                    track = hits[0]
                    url = track.get("preview_url") or track.get("url")
                    if not url:
                        continue
                    print(f"  Pixabay: {track.get('tags', 'unknown')}")
                    out = os.path.join(output_dir, "bg_music.mp3")
                    r = requests.get(url, stream=True, timeout=60)
                    r.raise_for_status()
                    with open(out, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    return out
            except Exception as e:
                print(f"  Music search failed for '{kw}': {e}")
                continue
        print("  No music found via Pixabay")
        return None
