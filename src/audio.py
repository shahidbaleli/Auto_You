import os
import asyncio
import edge_tts
from moviepy.editor import AudioFileClip

VOICE = os.environ.get("TTS_VOICE", "en-US-JennyNeural")


class AudioGenerator:
    def generate(self, text: str, output_path: str) -> float:
        asyncio.run(self._generate_async(text, output_path))
        with AudioFileClip(output_path) as clip:
            return clip.duration

    async def _generate_async(self, text: str, output_path: str):
        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(output_path)
