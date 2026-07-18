import os
import glob
import hashlib
import shutil
import requests
import random

BGM_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bgm")
OPENVERSE_AUDIO_URL = "https://api.openverse.org/v1/audio/"


class SoundDesigner:
    def __init__(self):
        pass

    def get_local_fallback(self, keywords: list[str], output_dir: str) -> str | None:
        """Fallback method to grab a local BGM file if Openverse queries fail."""
        tracks = glob.glob(os.path.join(BGM_DIR, "*.mp3"))
        if not tracks:
            print("  [Fallback] No local bgm/*.mp3 files found.")
            return None
        seed = " ".join(keywords)
        idx = int(hashlib.md5(seed.encode()).hexdigest(), 16) % len(tracks)
        track = tracks[idx]
        print(f"  [Fallback] Selected local BGM: {os.path.basename(track)}")
        out = os.path.join(output_dir, "bg_music.mp3")
        shutil.copy2(track, out)
        return out

    def download_bgm(self, keywords: list[str], output_dir: str) -> str | None:
        """
        Attempts to search and download a CC0 background music track from Openverse.
        Falls back to local BGM files if search/download fails.
        """
        if not keywords:
            return self.get_local_fallback(["music"], output_dir)

        # Build search query from keywords
        q = " ".join(keywords[:2])  # Use top 2 keywords to avoid empty queries
        print(f"Searching Openverse for CC0 music with query: '{q}'")
        
        params = {
            "q": q,
            "category": "music",
            "license": "cc0",
            "page_size": 20
        }
        
        headers = {
            "User-Agent": "AutoYouShortsPipeline/3.0 (https://github.com/shahidswisdom/yt-shorts-automation)"
        }

        try:
            resp = requests.get(OPENVERSE_AUDIO_URL, params=params, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                
                # Filter tracks with valid direct URLs (preferably ending in .mp3)
                valid_tracks = []
                for track in results:
                    url = track.get("url")
                    if url and (url.endswith(".mp3") or ".mp3" in url):
                        valid_tracks.append(url)
                
                if valid_tracks:
                    # Choose a random track from the top results for variety
                    chosen_url = random.choice(valid_tracks[:5])
                    print(f"Downloading BGM from Openverse: {chosen_url}")
                    
                    out_path = os.path.join(output_dir, "bg_music.mp3")
                    audio_resp = requests.get(chosen_url, headers=headers, stream=True, timeout=30)
                    audio_resp.raise_for_status()
                    with open(out_path, "wb") as f:
                        for chunk in audio_resp.iter_content(chunk_size=8192):
                            f.write(chunk)
                    return out_path
                else:
                    print("No valid MP3 tracks found in Openverse results.")
            else:
                print(f"Openverse API returned status code {resp.status_code}.")
        except Exception as e:
            print(f"Openverse API error: {e}")

        print("Falling back to local BGM...")
        return self.get_local_fallback(keywords, output_dir)

    def download_sfx(self, query: str, output_dir: str) -> str | None:
        """
        Searches and downloads a CC0 sound effect from Openverse.
        """
        print(f"Searching Openverse for CC0 sound effect: '{query}'")
        params = {
            "q": query,
            "category": "sound_effect",
            "license": "cc0",
            "page_size": 10
        }
        
        headers = {
            "User-Agent": "AutoYouShortsPipeline/3.0 (https://github.com/shahidswisdom/yt-shorts-automation)"
        }

        try:
            resp = requests.get(OPENVERSE_AUDIO_URL, params=params, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                
                valid_sfx = []
                for item in results:
                    url = item.get("url")
                    if url and (url.endswith(".mp3") or url.endswith(".wav") or ".mp3" in url or ".wav" in url):
                        valid_sfx.append((url, url.split("?")[0].split(".")[-1]))
                
                if valid_sfx:
                    chosen_url, ext = random.choice(valid_sfx[:3])
                    if ext not in ("mp3", "wav"):
                        ext = "mp3"
                    print(f"Downloading SFX from Openverse: {chosen_url}")
                    
                    # Create a safe filename hash
                    hash_name = hashlib.md5(query.encode()).hexdigest()[:8]
                    out_path = os.path.join(output_dir, f"sfx_{hash_name}.{ext}")
                    
                    audio_resp = requests.get(chosen_url, headers=headers, stream=True, timeout=20)
                    audio_resp.raise_for_status()
                    with open(out_path, "wb") as f:
                        for chunk in audio_resp.iter_content(chunk_size=8192):
                            f.write(chunk)
                    return out_path
                else:
                    print("No valid MP3/WAV sound effects found in Openverse results.")
        except Exception as e:
            print(f"Failed to fetch sound effect from Openverse: {e}")
        
        return None
