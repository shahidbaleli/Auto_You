import os
import sys
import shutil
import tempfile

from src.reader import ScriptReader
from src.audio import AudioGenerator
from src.downloader import VideoDownloader
from src.editor import VideoEditor
from src.uploader import YouTubeUploader


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

        print("\n[1/5] Reading next script from queue...")
        reader = ScriptReader()
        content = reader.get_next()
        print(f"  Title: {content['title']}")
        print(f"  Keywords: {', '.join(content['visual_keywords'])}")

        print("\n[2/5] Generating voiceover audio...")
        audio_path = os.path.join(workdir, "voiceover.mp3")
        audio_gen = AudioGenerator()
        audio_duration = audio_gen.generate(content["voiceover_script"], audio_path)
        print(f"  Audio duration: {audio_duration:.1f}s")
        temp_files.append(audio_path)

        print("\n[3/5] Downloading video clips...")
        downloader = VideoDownloader()
        video_paths = downloader.download_all(content["visual_keywords"], workdir)
        temp_files.extend(video_paths)
        print(f"  Downloaded {len(video_paths)} clips")

        if len(video_paths) < 2:
            raise RuntimeError(
                f"Need at least 2 video clips, got {len(video_paths)}"
            )

        print("\n[4/5] Composing video...")
        output_path = os.path.join(workdir, "final_short.mp4")
        editor = VideoEditor(workdir)
        editor.compose(
            video_paths=video_paths,
            audio_path=audio_path,
            script=content["voiceover_script"],
            output_path=output_path,
            audio_duration=audio_duration,
        )
        temp_files.append(output_path)
        print(f"  Video saved: {output_path}")

        print("\n[5/5] Uploading to YouTube...")
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
        sys.exit(1)
    finally:
        print("\nCleaning up temporary files...")
        cleanup(temp_files)


if __name__ == "__main__":
    main()
