"""Assemble voice + scene visuals + captions + music into a 9:16 MP4 (MoviePy 2).

First pass: static-style captions per chunk; word-highlight animation is on the roadmap.
"""

from __future__ import annotations

from pathlib import Path

from ..captions import Word
from ..config import MusicConfig, RenderSettings
from ..models import Script


def scene_durations(script: Script, total: float) -> list[float]:
    """Split total voice length across scenes by narration word count.

    The hook is folded into the first scene and the CTA into the last.
    """
    counts = [len(s.narration.split()) for s in script.scenes]
    counts[0] += len(script.hook.split())
    counts[-1] += len(script.cta.split())
    words = sum(counts) or 1
    return [total * c / words for c in counts]


def render_video(
    script: Script,
    voice_path: Path,
    scene_assets: list[Path],
    captions: list[Word],
    out_path: Path,
    render: RenderSettings,
    music: MusicConfig | None = None,
) -> Path:
    from moviepy import (  # lazy: optional [media] dependency
        AudioFileClip,
        CompositeAudioClip,
        CompositeVideoClip,
        ImageClip,
        TextClip,
        VideoFileClip,
        concatenate_videoclips,
        vfx,
    )

    W, H = render.width, render.height
    voice = AudioFileClip(str(voice_path))
    durations = scene_durations(script, voice.duration)

    def fit(clip):
        scale = max(W / clip.w, H / clip.h)
        clip = clip.resized(scale)
        return clip.cropped(x_center=clip.w / 2, y_center=clip.h / 2, width=W, height=H)

    scenes = []
    for asset, dur in zip(scene_assets, durations, strict=True):
        if asset.suffix.lower() in {".mp4", ".mov", ".webm"}:
            clip = VideoFileClip(str(asset)).without_audio()
            clip = clip.subclipped(0, dur) if clip.duration >= dur else clip.with_effects(
                [vfx.Loop(duration=dur)])
            scenes.append(fit(clip))
        else:
            img = fit(ImageClip(str(asset))).with_duration(dur)
            # Ken Burns: slow zoom-in, re-cropped to the canvas
            img = img.resized(lambda t: 1 + 0.04 * t).with_position("center")
            scenes.append(CompositeVideoClip([img], size=(W, H)).with_duration(dur))

    base = concatenate_videoclips(scenes, method="compose")

    font = render.font if Path(render.font).exists() else None  # None = Pillow default
    caption_clips = [
        TextClip(
            font=font,
            text=c.text.upper(),
            font_size=render.caption_font_size,
            color="white",
            stroke_color="black",
            stroke_width=6,
            method="caption",
            size=(int(W * 0.85), None),
            text_align="center",
        )
        .with_start(c.start)
        .with_duration(max(c.end - c.start, 0.15))
        .with_position(("center", int(H * 0.68)))
        for c in captions
    ]

    audio = [voice]
    if music and music.track and Path(music.track).exists():
        bg = AudioFileClip(music.track)
        bg = bg.subclipped(0, min(bg.duration, voice.duration)).with_volume_scaled(music.volume)
        audio.append(bg)

    final = (
        CompositeVideoClip([base, *caption_clips], size=(W, H))
        .with_audio(CompositeAudioClip(audio))
        .with_duration(voice.duration)
    )
    final.write_videofile(str(out_path), fps=render.fps, codec="libx264", audio_codec="aac")
    final.save_frame(str(out_path.with_name("thumbnail.jpg")), t=min(1.0, voice.duration / 2))
    return out_path
