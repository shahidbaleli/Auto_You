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
        # Formulate search queries to try in order of specificity
        queries_to_try = []
        if keywords:
            # 1. Try first two keywords combined
            queries_to_try.append(" ".join(keywords[:2]))
            # 2. Try keywords individually
            for kw in keywords[:3]:
                queries_to_try.append(kw)
        
        # 3. Always add a generic fallback query at the end
        queries_to_try.extend(["lofi", "ambient", "cinematic", "science tech"])

        headers = {
            "User-Agent": "AutoYouShortsPipeline/3.0 (https://github.com/shahidswisdom/yt-shorts-automation)"
        }

        for q in queries_to_try:
            print(f"Searching Openverse for CC0 music with query: '{q}'")
            params = {
                "q": q,
                "categories": "music",
                "license": "cc0",
                "page_size": 20
            }
            try:
                resp = requests.get(OPENVERSE_AUDIO_URL, params=params, headers=headers, timeout=15)
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results", [])
                    
                    valid_tracks = []
                    for track in results:
                        url = track.get("url")
                        if url:
                            valid_tracks.append(url)
                    
                    if valid_tracks:
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
                        print(f"No valid tracks found for '{q}'. Trying next query...")
            except Exception as e:
                print(f"Openverse BGM search error for '{q}': {e}")

        print("Falling back to local BGM...")
        return self.get_local_fallback(keywords, output_dir)

    def download_sfx(self, query: str, output_dir: str) -> str | None:
        """
        Searches and downloads a CC0 sound effect from Openverse.
        Falls back to simpler terms or transitions if not found.
        """
        # Formulate search queries to try in order of specificity
        queries_to_try = [query]
        # Split terms to try simpler keywords
        words = query.split()
        if len(words) > 1:
            queries_to_try.extend(words)
        
        # Add a generic transition sound effect as the ultimate fallback
        queries_to_try.extend(["whoosh", "swoosh", "transition click", "beep"])

        headers = {
            "User-Agent": "AutoYouShortsPipeline/3.0 (https://github.com/shahidswisdom/yt-shorts-automation)"
        }

        for q in queries_to_try:
            print(f"Searching Openverse for CC0 sound effect: '{q}'")
            params = {
                "q": q,
                "categories": "sound_effect",
                "license": "cc0",
                "page_size": 10
            }
            try:
                resp = requests.get(OPENVERSE_AUDIO_URL, params=params, headers=headers, timeout=15)
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results", [])
                    
                    valid_sfx = []
                    for item in results:
                        url = item.get("url")
                        if url:
                            valid_sfx.append(url)
                    
                    if valid_sfx:
                        chosen_url = random.choice(valid_sfx[:3])
                        print(f"Downloading SFX from Openverse: {chosen_url}")
                        
                        # Create a safe filename hash
                        hash_name = hashlib.md5(query.encode()).hexdigest()[:8]
                        out_path = os.path.join(output_dir, f"sfx_{hash_name}.mp3")
                        
                        audio_resp = requests.get(chosen_url, headers=headers, stream=True, timeout=20)
                        audio_resp.raise_for_status()
                        with open(out_path, "wb") as f:
                            for chunk in audio_resp.iter_content(chunk_size=8192):
                                f.write(chunk)
                        return out_path
                    else:
                        print(f"No valid tracks found for SFX '{q}'. Trying next query...")
            except Exception as e:
                print(f"Failed to fetch sound effect '{q}' from Openverse: {e}")
        
        return None
