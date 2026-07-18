import os
import glob
import hashlib
import shutil

BGM_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bgm")


class MusicDownloader:
    def download(self, keywords: list[str], output_dir: str) -> str | None:
        tracks = glob.glob(os.path.join(BGM_DIR, "*.mp3"))
        if not tracks:
            print("  No bgm/*.mp3 files found — skipping background music")
            print("  Add MP3 files to the bgm/ folder and commit")
            return None
        seed = " ".join(keywords)
        idx = int(hashlib.md5(seed.encode()).hexdigest(), 16) % len(tracks)
        track = tracks[idx]
        print(f"  Background music: {os.path.basename(track)}")
        out = os.path.join(output_dir, "bg_music.mp3")
        shutil.copy2(track, out)
        return out
