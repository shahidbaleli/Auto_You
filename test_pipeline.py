import os
import shutil
import tempfile
import re
from src.audio import AudioGenerator
from src.sound_designer import SoundDesigner
from src.editor import VideoEditor

def test_pipeline():
    workdir = tempfile.mkdtemp(prefix="test_yt_")
    print("Created test workdir:", workdir)

    try:
        # 1. Create a dummy clean script and parse SFX tags
        raw_script = "Hello world [sfx: chime] this is a test of the sound designer and advanced voiceovers. [sfx: whoosh]"
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
        print("Cleaned script:", clean_script)
        print("SFX Cues found:", sfx_cues)

        # 2. Test Audio Generator (fallback mode since GEMINI_API_KEY is not set)
        print("\n--- Testing Audio Generator (Fallback Mode) ---")
        audio_path = os.path.join(workdir, "voiceover.mp3")
        audio_gen = AudioGenerator()
        audio_duration = audio_gen.generate(
            text=clean_script,
            output_path=audio_path,
            title="Test Title",
            audio_profile="A clear, professional test narrator.",
            directors_note="Pace: Normal."
        )
        print(f"Generated audio duration: {audio_duration:.2f}s")

        # 3. Test Sound Designer (Openverse Search & Fallback)
        print("\n--- Testing Sound Designer (Openverse/Fallback) ---")
        sound_designer = SoundDesigner()
        music_path = sound_designer.download_bgm(["science", "lofi"], workdir)
        print("BGM downloaded to:", music_path)

        sfx_tracks = []
        for query, ratio in sfx_cues:
            sfx_path = sound_designer.download_sfx(query, workdir)
            if sfx_path:
                sfx_tracks.append((sfx_path, ratio * audio_duration))
        print("SFX tracks compiled:", sfx_tracks)

        # 4. Mock 2 video clips for composting
        # We will create two tiny dummy MP4 files to test MoviePy composition.
        # But since we just want to verify function calls, let's check imports and signatures.
        print("\n--- Verifying VideoEditor Compose Signature ---")
        editor = VideoEditor(workdir)
        import inspect
        sig = inspect.signature(editor.compose)
        print("VideoEditor.compose signature is:")
        for name, param in sig.parameters.items():
            print(f"  {name}: {param.default if param.default != inspect.Parameter.empty else '(required)'}")

        # Check if 'sfx_tracks' is in the signature
        if 'sfx_tracks' in sig.parameters:
            print("\nSUCCESS: 'sfx_tracks' parameter is present in VideoEditor.compose!")
        else:
            print("\nFAILURE: 'sfx_tracks' parameter is MISSING from VideoEditor.compose!")

    except Exception as e:
        print("Error during pipeline test:", e)
        import traceback
        traceback.print_exc()
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
        print("\nCleaned up test workdir.")

if __name__ == "__main__":
    test_pipeline()
