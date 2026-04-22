#!/usr/bin/env python3
"""Summarize transcript using Ollama (local) or Anthropic API."""

import os
import sys
import json
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

MEETINGS_DIR = Path(__file__).parent.parent / "meetings"
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

PROMPT_TEMPLATE = """Ты помощник для обработки транскриптов встреч.

Транскрипт встречи:
{transcript}

Напиши краткое саммари на русском языке в формате:

## Ключевые темы
- ...

## Решения
- ...

## Задачи и следующие шаги
- ...

## Прочее
- ...
"""


def find_latest_transcript() -> Path:
    files = sorted(MEETINGS_DIR.glob("????-??-??/audio_??-??.txt"), reverse=True)
    if files:
        return files[0]
    raise FileNotFoundError("No transcripts found in meetings/")


def summarize_ollama(transcript: str) -> str:
    prompt = PROMPT_TEMPLATE.format(transcript=transcript)
    response = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["response"].strip()


def summarize(transcript_path: Path) -> Path:
    transcript = transcript_path.read_text(encoding="utf-8")
    print(f"Summarizing with Ollama ({OLLAMA_MODEL})...")
    summary = summarize_ollama(transcript)

    summary_path = transcript_path.with_name(transcript_path.stem + "_summary.md")
    header = f"# Саммари встречи {transcript_path.parent.name}\n\n"
    summary_path.write_text(header + summary, encoding="utf-8")
    print(f"Saved: {summary_path}")
    return summary_path


if __name__ == "__main__":
    transcript_path = Path(sys.argv[1]) if len(sys.argv) > 1 else find_latest_transcript()
    summarize(transcript_path)
