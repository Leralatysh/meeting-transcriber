#!/usr/bin/env python3
"""Background daemon. Cmd+Shift+M to start/stop recording."""

import os
import signal
import subprocess
import sys
import threading
from pathlib import Path

from pynput import keyboard

SCRIPTS = Path(__file__).parent
STATE_FILE = SCRIPTS.parent / ".recording_pid"


def notify(title, message):
    subprocess.run([
        "osascript", "-e",
        f'display notification "{message}" with title "{title}" sound name "default"'
    ])


def start_recording():
    proc = subprocess.Popen(
        [sys.executable, str(SCRIPTS / "record_simple.py")],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    STATE_FILE.write_text(str(proc.pid))
    notify("🎙 Запись началась", "Нажми Cmd+Shift+M чтобы остановить")


def stop_and_process():
    if not STATE_FILE.exists():
        return
    pid = int(STATE_FILE.read_text().strip())
    STATE_FILE.unlink()
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass

    notify("⏹ Запись остановлена", "Транскрипция...")

    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "transcribe.py")],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        notify("Ошибка транскрипции", result.stderr[-150:])
        return

    notify("Транскрипция готова", "Делаю саммари...")
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "summarize.py")],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        notify("Ошибка саммари", result.stderr[-150:])
    else:
        notify("✅ Готово!", "Транскрипт и саммари сохранены в meetings/")


def on_activate():
    if STATE_FILE.exists():
        threading.Thread(target=stop_and_process, daemon=True).start()
    else:
        threading.Thread(target=start_recording, daemon=True).start()


with keyboard.GlobalHotKeys({"<cmd>+<shift>+m": on_activate}) as h:
    print("Daemon running. Cmd+Shift+M to start/stop recording.")
    h.join()
