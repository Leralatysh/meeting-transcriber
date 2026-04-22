#!/usr/bin/env python3
"""Transcribe audio from the latest meeting folder (or a given path)."""

import sys
from pathlib import Path

import whisper

MEETINGS_DIR = Path(__file__).parent.parent / "meetings"
WHISPER_MODEL = "medium"


def find_latest_audio() -> Path:
    files = sorted(MEETINGS_DIR.glob("????-??-??/audio_??-??.wav"), reverse=True)
    if files:
        return files[0]
    raise FileNotFoundError("No audio files found in meetings/")


def transcribe(audio_path: Path) -> Path:
    print(f"Loading Whisper model '{WHISPER_MODEL}'...")
    model = whisper.load_model(WHISPER_MODEL)

    print(f"Transcribing: {audio_path}")
    result = model.transcribe(str(audio_path), language="ru", fp16=False)

    transcript_path = audio_path.with_suffix(".txt")
    transcript_path.write_text(result["text"].strip(), encoding="utf-8")
    print(f"Saved: {transcript_path}")
    return transcript_path


if __name__ == "__main__":
    audio_path = Path(sys.argv[1]) if len(sys.argv) > 1 else find_latest_audio()
    transcribe(audio_path)
