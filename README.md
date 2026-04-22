# Meeting Transcriber

Инструмент для автоматической записи и транскрипции онлайн-встреч на macOS.

Записывает системный звук (голоса участников) через нативный Apple API, транскрибирует локально через Whisper и генерирует структурированное саммари через Ollama. Всё работает офлайн, без передачи данных в облако.

**Стек:** Python · Swift (ScreenCaptureKit) · OpenAI Whisper · Ollama (llama3.2) · macOS Tahoe

---

## Как пользоваться

1. Запустить демон (один раз после перезагрузки):
   ```bash
   python3 /Users/work_lera/Documents/meeting-transcriber/scripts/hotkey_daemon.py &
   ```

2. **Cmd+Shift+M** — начать запись (придёт уведомление)
3. **Cmd+Shift+M** ещё раз — остановить запись → автоматически запустится транскрипция → саммари
4. Файлы сохраняются в `meetings/YYYY-MM-DD/audio_HH-MM.wav`, `audio_HH-MM.txt`, `audio_HH-MM_summary.md`

Несколько встреч в один день — каждая в отдельном файле с временем.

---

## Архитектура

```
scripts/
├── hotkey_daemon.py     — фоновый демон, слушает Cmd+Shift+M
├── record_simple.py     — запускает capture_audio.swift, сохраняет audio_HH-MM.wav
├── capture_audio.swift  — захват системного звука через ScreenCaptureKit (Apple API)
├── transcribe.py        — транскрипция через Whisper (модель medium)
└── summarize.py         — саммари через Ollama (модель llama3.2, локально)

meetings/
└── 2026-04-21/
    ├── audio_14-30.wav
    ├── audio_14-30.txt
    └── audio_14-30_summary.md
```

---

## Системные требования и зависимости

- macOS Tahoe (26) / M4
- Python 3.9+
- Swift (встроен в Xcode Command Line Tools)
- Ollama (запущен как сервис: `brew services start ollama`)
- ffmpeg (`brew install ffmpeg`)

Python пакеты (`pip3 install`):
```
openai-whisper
sounddevice
pynput
numpy
python-dotenv
requests
rumps
```

---

## После перезагрузки

Нужно сделать вручную:
1. Запустить Ollama если не запущен: `brew services start ollama`
2. Запустить демон:
   ```bash
   python3 /Users/work_lera/Documents/meeting-transcriber/scripts/hotkey_daemon.py > /tmp/meeting-transcriber.log 2>&1 &
   ```

**TODO:** настроить автозапуск демона через Login Items (System Settings → General → Login Items).

---

## Разрешения macOS (нужно выдать один раз)

- **Accessibility** → Terminal — для горячих клавиш (pynput)
- **Screen Recording** → Terminal — для захвата системного звука (ScreenCaptureKit)
- **Microphone** → Terminal / Python — для записи микрофона (если понадобится)

---

## Захват системного звука

Используется **ScreenCaptureKit** (Apple native API) через Swift скрипт.
Запускается как `swift capture_audio.swift` (не скомпилированный бинарник — важно, чтобы наследовались разрешения Terminal).

Аудио формат: Float32 non-interleaved → конвертируется в Int16 interleaved → WAV 48000 Hz stereo.

### Что пробовали и не сработало

**BlackHole 2ch** (виртуальный аудиодрайвер):
- Установили через `brew install blackhole-2ch`
- Настроили Multi-Output Device в Audio MIDI Setup (EarPods + BlackHole)
- BlackHole записывал только тишину (amplitude ~25/32767)
- Причина: известный баг macOS Tahoe с аудио маршрутизацией через Multi-Output Device и Atmos
- Переустановка не помогла
- **Решение:** отказались в пользу ScreenCaptureKit

**meeting output / meeting recorder** (Aggregate Device):
- Создавали в Audio MIDI Setup
- Не нужны — удали их в Audio MIDI Setup (кнопка `-`)
- Output в System Settings → Sound должен стоять на **EarPods** (не meeting output)

---

## Транскрипция

Используется **OpenAI Whisper** локально.

Текущая модель: `medium` (~1.5GB, ~2-3 мин на 1 час записи на M4)

Доступные модели в `~/.cache/whisper/`:
- `small` — быстрая, низкое качество для русского
- `medium` — текущая, хороший баланс
- `large-v3` — лучшее качество, но медленная (~10 мин на 1 час)

Менять модель: в `scripts/transcribe.py` строка `WHISPER_MODEL = "medium"`

**Известная проблема:** на паузах и музыке Whisper галлюцинирует (повторяет слова). На чистой речи работает хорошо.

---

## Саммари

Используется **Ollama** с моделью `llama3.2` локально.

Ollama должен быть запущен: `brew services start ollama`

Промпт выдаёт структурированное саммари: темы, решения, задачи, следующие шаги.

**TODO:** когда появится баланс на Anthropic API — добавить `summarize_claude()` в `summarize.py`. API ключ уже есть, нужно пополнить баланс на console.anthropic.com.

---

## Известные проблемы и TODO

- [ ] **Качество аудио** — последняя проблема: голос тонкий, робовойс. Исправлена конвертация float32 non-interleaved → int16 interleaved, но нужно проверить на новой записи
- [ ] **Автозапуск демона** при входе в систему (Login Items)
- [ ] **Инструкция по настройке на новом компьютере** (написать после стабилизации)
- [ ] **Репозиторий** — решить куда заливать: рабочий GitLab или личный GitHub (meetings/ в .gitignore)
- [ ] **Саммари через Claude API** — когда появится баланс
- [ ] **Тест на реальной встрече в Телемосте** — проверить полный цикл на живой встрече
- [ ] **Сравнить модели Whisper** — medium vs large-v3 по качеству и скорости на реальной речи
- [ ] **Удалить лишние аудио устройства** — в Audio MIDI Setup удалить meeting output и meeting recorder, Output в Sound → EarPods
- [ ] **Микрофон + системный звук** — ВАЖНО: сейчас записывается только системный звук (голоса собеседников), голос пользователя не попадает в запись. Нужно добавить параллельную запись с микрофона EarPods и смешивать два потока перед транскрипцией. Без этого транскрипция неполная.
