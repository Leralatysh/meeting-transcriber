#!/usr/bin/env python3
"""Background recorder using ScreenCaptureKit — captures system audio."""

import os
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPTS = Path(__file__).parent
SWIFT_SCRIPT = SCRIPTS / "capture_audio.swift"
MEETINGS_DIR = SCRIPTS.parent / "meetings"

now = datetime.now()
folder = MEETINGS_DIR / now.strftime("%Y-%m-%d")
folder.mkdir(parents=True, exist_ok=True)
output_path = folder / f"audio_{now.strftime('%H-%M')}.wav"

proc = subprocess.Popen(
    ["swift", str(SWIFT_SCRIPT), str(output_path)],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)


def stop(signum, frame):
    proc.send_signal(signal.SIGTERM)
    proc.wait()
    sys.exit(0)


signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)

proc.wait()
