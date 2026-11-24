"""Word-level timestamps for burned-in captions using faster-whisper."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel


class Word(BaseModel):
    text: str
    start: float
    end: float


def transcribe_words(
    audio_path: Path, language: str = "en", model_size: str = "base"
) -> list[Word]:
    from faster_whisper import WhisperModel  # lazy: optional [media] dependency

    model = WhisperModel(model_size, device="auto", compute_type="int8")
    segments, _ = model.transcribe(str(audio_path), language=language, word_timestamps=True)
    return [
        Word(text=w.word.strip(), start=w.start, end=w.end)
        for seg in segments
        for w in (seg.words or [])
        if w.word.strip()
    ]


def chunk_words(words: list[Word], size: int = 2) -> list[Word]:
    """Group words into caption chunks of `size` words."""
    chunks: list[Word] = []
    for i in range(0, len(words), size):
        group = words[i:i + size]
        chunks.append(Word(
            text=" ".join(w.text for w in group),
            start=group[0].start,
            end=group[-1].end,
        ))
    return chunks
