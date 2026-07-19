import os
import sys
import shutil
import tempfile
import traceback

from src.reader import ScriptReader
from src.audio import AudioGenerator
from src.downloader import VideoDownloader
from src.editor import VideoEditor
from src.uploader import YouTubeUploader
from src.sound_designer import SoundDesigner


def cleanup(paths: list[str]):
    for p in paths:
        try:
            if os.path.isfile(p):
                os.remove(p)
            elif os.path.isdir(p):
                shutil.rmtree(p, ignore_errors=True)
        except Exception:
            pass


def main():
    workdir = tempfile.mkdtemp(prefix="yt_shorts_")
    temp_files = [workdir]

    try:
        print("=" * 50)
        print("YouTube Shorts Automation Pipeline")
        print("=" * 50)

        print("\n[1/6] Reading next script from queue...")
        reader = ScriptReader()
        content = reader.get_next()
        print(f"  Title: {content['title']}")
        print(f"  Keywords: {', '.join(content['visual_keywords'])}")

        import re
        
        # Parse SFX tags and clean the script
        raw_script = content["voiceover_script"]
        clean_script = raw_script
        sfx_cues = []
        
        while True:
            match = re.search(r'\[sfx:\s*([^\]]+)\]', clean_script)
            if not match:
                break
            query = match.group(1).strip()
            start_idx = match.start()
            clean_script = clean_script[:start_idx] + clean_script[match.end():]
            ratio = start_idx / max(1, len(clean_script))
            sfx_cues.append((query, ratio))
            
        clean_script = re.sub(r'\s+', ' ', clean_script).strip()

        print("\n[2/6] Generating voiceover audio...")
        audio_path = os.path.join(workdir, "voiceover.mp3")
        audio_gen = AudioGenerator()
        audio_duration = audio_gen.generate(
            text=clean_script,
            output_path=audio_path,
            title=content.get("title", ""),
            audio_profile=content.get("audio_profile", "A deep, resonant narrator of mysteries."),
            directors_note=content.get("directors_note", 'Style: The "Vocal Smile": The soft palate is raised to keep the tone bright, sunny, and explicitly inviting. Pace: The Drift. Accent: American (Valley Girl).')
        )
        print(f"  Audio duration: {audio_duration:.1f}s")
        temp_files.append(audio_path)

        print("\n[3/6] Downloading video clips and images...")
        downloader = VideoDownloader()
        video_paths, image_paths = downloader.download_all(content["visual_keywords"], workdir)
        temp_files.extend(video_paths + image_paths)
        print(f"  Downloaded {len(video_paths)} clips + {len(image_paths)} images")

        if len(video_paths) < 2:
            raise RuntimeError(
                f"Need at least 2 video clips, got {len(video_paths)}"
            )

        print("\n[4/6] Downloading background music & sound effects...")
        sound_designer = SoundDesigner()
        music_path = sound_designer.download_bgm(content["visual_keywords"], workdir)
        if music_path:
            temp_files.append(music_path)
            
        sfx_tracks = []
        for query, ratio in sfx_cues:
            sfx_path = sound_designer.download_sfx(query, workdir)
            if sfx_path:
                temp_files.append(sfx_path)
                sfx_tracks.append((sfx_path, ratio * audio_duration))

        print("\n[5/6] Composing video...")
        output_path = os.path.join(workdir, "final_short.mp4")
        editor = VideoEditor(workdir)
        editor.compose(
            video_paths=video_paths,
            audio_path=audio_path,
            script=clean_script,
            output_path=output_path,
            audio_duration=audio_duration,
            image_paths=image_paths,
            music_path=music_path,
            sfx_tracks=sfx_tracks,
        )
        temp_files.append(output_path)
        print(f"  Video saved: {output_path}")

        print("\n[6/6] Uploading to YouTube...")
        uploader = YouTubeUploader()
        uploader.upload(
            video_path=output_path,
            title=content["title"],
            description=content["description"],
            tags=content["tags"],
        )

        print("\nDone! Video uploaded successfully.")

    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
    finally:
        print("\nCleaning up temporary files...")
        cleanup(temp_files)


if __name__ == "__main__":
    main()
