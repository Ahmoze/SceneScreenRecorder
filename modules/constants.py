import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Tuple

APP_TITLE = "Scene-Grade Screen Recorder"
APP_VERSION = "v2.8 (Modular Edition)"
FFMPEG_PATH = "ffmpeg"
FFMPEG_LOGLEVEL = "error"
STOP_TIMEOUT_SEC = 5.0

# Putanje
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
CONFIG_FILE = CONFIG_DIR / "config.json"
DEFAULT_OUTPUT_ROOT = str(Path.home() / "Videos" / "ScreenCaptures")

VIDEO_SUBDIR = "video"
SCREENSHOT_SUBDIR = "screenshot"

# Presets Data Class
@dataclass
class Preset:
    name: str
    fps: int
    crf: int
    mode: str
    width: Optional[int] = None
    height: Optional[int] = None

PRESETS: List[Preset] = [
    Preset("Scene: Native / Balanced (30fps, CRF23)", 30, 23, "Native"),
    Preset("YouTube 1080p30 (CRF21)", 30, 21, "Custom", 1920, 1080),
    Preset("Tutorial 1440p60 (CRF20)", 60, 20, "Custom", 2560, 1440),
    Preset("Full Dump Native / HQ (60fps, CRF18)", 60, 18, "Native"),
]

def suggest_preset_for_monitor(w: int, h: int) -> int:
    if w <= 1920 and h <= 1080:
        return 1
    if w <= 2560 and h <= 1440:
        return 2
    return 3

# Config Helperi
def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def load_config() -> dict:
    try:
        if CONFIG_FILE.exists():
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict): return data
    except Exception: pass
    return {}

def save_config(cfg: dict) -> None:
    try:
        ensure_dir(CONFIG_DIR)
        CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception: pass

# 🔑 OVO JE FALILO: Funkcija za proveru output foldera
def ensure_output_root(root: str) -> Tuple[bool, str]:
    if not root or not root.strip():
        return False, "Output root folder nije podešen."
    try:
        root_path = Path(root)
        ensure_dir(root_path)
        ensure_dir(root_path / VIDEO_SUBDIR)
        ensure_dir(root_path / SCREENSHOT_SUBDIR)
        return True, f"Output root folder spreman: {root_path}"
    except Exception as e:
        return False, f"Ne mogu da kreiram output strukturu: {e}"
