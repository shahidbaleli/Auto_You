import re
import tempfile
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, TextClip, concatenate_videoclips

import PIL.Image
if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

TARGET_W, TARGET_H = 1080, 1920
FONT = "DejaVu-Sans-Bold"


def _split_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _estimate_timings(sentences: list[str], total_duration: float) -> list[tuple[str, float]]:
    word_counts = [len(s.split()) for s in sentences]
    total_words = sum(word_counts)
    if total_words == 0:
        return [(sentences[0], total_duration)] if sentences else []
    result = []
    for s, wc in zip(sentences, word_counts):
        duration = (wc / total_words) * total_duration
        result.append((s, duration))
    return result


def _crop_to_portrait(clip: VideoFileClip) -> VideoFileClip:
    w, h = clip.size
    target_ratio = TARGET_W / TARGET_H
    current_ratio = w / h
    if current_ratio > target_ratio:
        new_w = int(h * target_ratio)
        x_center = w // 2
        clip = clip.crop(x1=x_center - new_w // 2, x2=x_center + new_w // 2)
    elif current_ratio < target_ratio:
        new_h = int(w / target_ratio)
        y_center = h // 2
        clip = clip.crop(y1=y_center - new_h // 2, y2=y_center + new_h // 2)
    return clip.resize((TARGET_W, TARGET_H))


class VideoEditor:
    def __init__(self, workdir: str | None = None):
        self.workdir = workdir or tempfile.mkdtemp(prefix="shorts_edit_")

    def compose(
        self,
        video_paths: list[str],
        audio_path: str,
        script: str,
        output_path: str,
        audio_duration: float,
    ) -> str:
        print("Loading video clips...")
        clips = []
        for path in video_paths:
            try:
                clip = VideoFileClip(path)
                clip = _crop_to_portrait(clip)
                clips.append(clip)
            except Exception as e:
                print(f"  Failed to load {path}: {e}")

        if not clips:
            raise RuntimeError("No usable video clips to compose")

        total_clip_duration = sum(c.duration for c in clips)

        if total_clip_duration < audio_duration:
            factor = int(audio_duration / total_clip_duration) + 1
            clips = clips * factor

        trimmed = []
        accumulated = 0.0
        for c in clips:
            needed = audio_duration - accumulated
            if needed <= 0:
                c.close()
                break
            if c.duration > needed:
                trimmed.append(c.subclip(0, needed))
                accumulated += needed
            else:
                trimmed.append(c)
                accumulated += c.duration

        print("Concatenating video...")
        final_video = concatenate_videoclips(trimmed, method="compose")

        print("Adding audio...")
        audio = AudioFileClip(audio_path)
        final_video = final_video.set_audio(audio)

        print("Generating subtitles...")
        sentences = _split_sentences(script)
        timings = _estimate_timings(sentences, audio_duration)

        subtitle_clips = []
        current_time = 0.0
        for text, dur in timings:
            txt = TextClip(
                text,
                fontsize=60,
                color="white",
                stroke_color="black",
                stroke_width=3,
                font=FONT,
                size=(TARGET_W - 200, None),
                method="caption",
                align="center",
            )
            txt = txt.set_start(current_time).set_duration(dur)
            txt = txt.set_position(("center", TARGET_H - 250))
            subtitle_clips.append(txt)
            current_time += dur

        print("Compositing final video...")
        final = CompositeVideoClip([final_video, *subtitle_clips], size=(TARGET_W, TARGET_H))

        print("Rendering...")
        final.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=30,
            preset="ultrafast",
            threads=2,
            bitrate="3000k",
            logger=None,
        )

        for c in clips:
            c.close()
        audio.close()
        final_video.close()
        final.close()
        for t in subtitle_clips:
            t.close()

        return output_path
