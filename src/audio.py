import os
import asyncio
import mimetypes
import struct
from moviepy.editor import AudioFileClip

import edge_tts

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
VOICE_NAME = os.environ.get("TTS_VOICE", "Aoede")  # Default to Aoede
MODEL_NAME = os.environ.get("TTS_MODEL", "gemini-3.1-flash-tts-preview")
EDGE_VOICE = os.environ.get("EDGE_TTS_VOICE", "en-US-AndrewNeural")


class AudioGenerator:
    def generate(
        self,
        text: str,
        output_path: str,
        title: str = "",
        audio_profile: str = "A deep, resonant narrator of mysteries.",
        directors_note: str = 'Style: The "Vocal Smile": The soft palate is raised to keep the tone bright, sunny, and explicitly inviting. Pace: The Drift. Accent: American (Valley Girl).'
    ) -> float:
        if GEMINI_API_KEY and HAS_GENAI:
            try:
                print(f"Generating voiceover using Gemini TTS ({MODEL_NAME}) with voice '{VOICE_NAME}'...")
                self._generate_gemini(text, output_path, title, audio_profile, directors_note)
                with AudioFileClip(output_path) as clip:
                    return clip.duration
            except Exception as e:
                print(f"Gemini TTS generation failed: {e}. Falling back to edge-tts...")
        
        print(f"Generating voiceover using edge-tts with voice '{EDGE_VOICE}'...")
        asyncio.run(self._generate_edge_async(text, output_path))
        with AudioFileClip(output_path) as clip:
            return clip.duration

    def _generate_gemini(
        self,
        text: str,
        output_path: str,
        title: str,
        audio_profile: str,
        directors_note: str
    ):
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        prompt = f"""Read the following transcript based on the audio profile and director's note.

# Audio Profile
{audio_profile}

# Director's note
{directors_note}

## Scene:
{title}

## Transcript:
{text}"""

        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            temperature=1.0,
            response_modalities=["audio"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=VOICE_NAME
                    )
                )
            ),
        )

        audio_data = b""
        mime_type = None

        for chunk in client.models.generate_content_stream(
            model=MODEL_NAME,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.parts is None:
                continue
            if chunk.parts[0].inline_data and chunk.parts[0].inline_data.data:
                inline_data = chunk.parts[0].inline_data
                audio_data += inline_data.data
                if mime_type is None:
                    mime_type = inline_data.mime_type

        if not audio_data:
            raise RuntimeError("No audio data returned from Gemini TTS API")

        file_extension = mimetypes.guess_extension(mime_type) if mime_type else None
        
        if file_extension is None:
            audio_data = self._convert_to_wav(audio_data, mime_type or "audio/L16;rate=24000")
            
        with open(output_path, "wb") as f:
            f.write(audio_data)
        print(f"Gemini voiceover saved to: {output_path}")

    async def _generate_edge_async(self, text: str, output_path: str):
        communicate = edge_tts.Communicate(text, EDGE_VOICE)
        await communicate.save(output_path)

    def _convert_to_wav(self, audio_data: bytes, mime_type: str) -> bytes:
        parameters = self._parse_audio_mime_type(mime_type)
        bits_per_sample = parameters["bits_per_sample"]
        sample_rate = parameters["rate"]
        num_channels = 1
        data_size = len(audio_data)
        bytes_per_sample = bits_per_sample // 8
        block_align = num_channels * bytes_per_sample
        byte_rate = sample_rate * block_align
        chunk_size = 36 + data_size

        header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",
            chunk_size,
            b"WAVE",
            b"fmt ",
            16,
            1,
            num_channels,
            sample_rate,
            byte_rate,
            block_align,
            bits_per_sample,
            b"data",
            data_size
        )
        return header + audio_data

    def _parse_audio_mime_type(self, mime_type: str) -> dict[str, int]:
        bits_per_sample = 16
        rate = 24000

        parts = mime_type.split(";")
        for param in parts:
            param = param.strip()
            if param.lower().startswith("rate="):
                try:
                    rate_str = param.split("=", 1)[1]
                    rate = int(rate_str)
                except (ValueError, IndexError):
                    pass
            elif param.startswith("audio/L"):
                try:
                    bits_per_sample = int(param.split("L", 1)[1])
                except (ValueError, IndexError):
                    pass

        return {"bits_per_sample": bits_per_sample, "rate": rate}
