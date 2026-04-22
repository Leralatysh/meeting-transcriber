# Meeting Transcriber

Инструмент для автоматической записи и транскрипции онлайн-встреч на macOS.

Записывает системный звук (голоса участников) через нативный Apple API, транскрибирует локально через Whisper и генерирует структурированное саммари через Ollama. Всё работает офлайн, без передачи данных в облако.

**Стек:** Python · Swift (ScreenCaptureKit) · OpenAI Whisper · Ollama (llama3.2) · macOS Tahoe

---

## Как пользоваться

1. Запустить демон (один раз после перезагрузки):
   ```bash
   python3 /path/to/meeting-transcriber/scripts/hotkey_daemon.py &
   ```

2. **Cmd+Shift+M** — начать запись (придёт уведомление)
3. **Cmd+Shift+M** ещё раз — остановить запись → автоматически запустится транскрипция → саммари
4. Файлы сохраняются в `meetings/YYYY-MM-DD/`: аудио, транскрипт и саммари

Несколько встреч в один день — каждая в отдельном файле с временем.

Проверить что демон работает: `launchctl list | grep meeting-transcriber`
Остановить вручную: `launchctl unload ~/Library/LaunchAgents/com.meeting-transcriber.daemon.plist`

---

## Архитектура

```
scripts/
├── hotkey_daemon.py     — фоновый демон, слушает Cmd+Shift+M
├── record_simple.py     — захват системного звука, сохраняет audio_HH-MM.wav
├── capture_audio.swift  — ScreenCaptureKit (Apple native API)
├── transcribe.py        — транскрипция через Whisper
└── summarize.py         — саммари через Ollama

meetings/
└── 2024-01-15/
    ├── audio_14-30.wav
    ├── audio_14-30.txt
    └── audio_14-30_summary.md
```

---

## Установка

**Зависимости:**
```bash
brew install ffmpeg ollama
ollama pull llama3.2
pip3 install openai-whisper pynput numpy python-dotenv requests
```

**Разрешения macOS (выдать один раз):**
- System Settings → Privacy → Accessibility → Terminal
- System Settings → Privacy → Screen Recording → Terminal

---

## Системные требования

- macOS Tahoe или новее
- Python 3.9+
- Xcode Command Line Tools (для Swift)
