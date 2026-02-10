import subprocess
import threading
import time
import sys
from pathlib import Path
from datetime import datetime
from PySide6 import QtCore
from .constants import FFMPEG_PATH, FFMPEG_LOGLEVEL, STOP_TIMEOUT_SEC, VIDEO_SUBDIR, ensure_dir, ensure_output_root

class FfmpegController(QtCore.QObject):
    sig_log = QtCore.Signal(str)
    sig_status = QtCore.Signal(str, str)
    sig_process_ended = QtCore.Signal(int)

    def __init__(self, ffmpeg_path: str = FFMPEG_PATH):
        super().__init__()
        self.ffmpeg_path = ffmpeg_path
        self.proc = None
        self._stderr_thread = None
        self._stderr_stop = threading.Event()
        self.is_recording = False
        self.is_paused = False
        self.current_crf = 23

    def _emit_log(self, msg):
        self.sig_log.emit(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    def _emit_status(self, msg, col):
        self.sig_status.emit(msg, col)
    
    def _read_stderr(self):
        while not self._stderr_stop.is_set() and self.proc:
            try:
                line = self.proc.stderr.readline()
                if not line:
                    break
                if line.strip():
                    self.sig_log.emit(f"ffmpeg: {line.strip()}")
            except:
                break

    def start_recording(self, mon, res_mode, custom_wh, root, fps, crf, record_audio=False):
        if self.is_recording:
            return False
        
        # Check output
        ok, msg = ensure_output_root(root)
        if not ok:
            self._emit_status(msg, "#FF4444")
            return False

        out_path = Path(root) / VIDEO_SUBDIR
        ensure_dir(out_path)
        outfile = out_path / f"capture_{mon.index}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

        # Video (gdigrab)
        args = [
            self.ffmpeg_path,
            "-y",
            "-hide_banner",
            "-loglevel", FFMPEG_LOGLEVEL,
            "-f", "gdigrab",
            "-framerate", str(fps),
            "-offset_x", str(mon.left),
            "-offset_y", str(mon.top),
            "-video_size", f"{mon.w}x{mon.h}",
            "-i", "desktop",
        ]

        # Audio (WASAPI sistemski zvuk)
        if record_audio:
            args += [
                "-f", "wasapi",
                "-i", "default",  # ili npr. "Speakers (Realtek(R) Audio)"
            ]
        
        # Scale ako je custom rezolucija
        if res_mode == "Custom" and custom_wh:
            args += ["-vf", f"scale={custom_wh[0]}:{custom_wh[1]}"]
            
        # Output
        if record_audio:
            args += [
                "-vsync", "cfr",
                "-r", str(fps),
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", str(crf),
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                str(outfile),
            ]
        else:
            args += [
                "-vsync", "cfr",
                "-r", str(fps),
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", str(crf),
                "-pix_fmt", "yuv420p",
                str(outfile),
            ]
        
        self._emit_log(f"CMD: {' '.join(args)}")
        
        try:
            cf = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            self.proc = subprocess.Popen(
                args,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                creationflags=cf,
            )
            time.sleep(0.5)
            if self.proc.poll() is not None:
                self._emit_status("FFmpeg fail (start)", "#FF4444")
                return False
            
            self.is_recording = True
            self.is_paused = False
            self._stderr_stop.clear()
            self._stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)
            self._stderr_thread.start()
            self._emit_status("Snimanje u toku", "#88FF88")
            return True
        except Exception as e:
            self._emit_log(f"Error: {e}")
            self._emit_status("Greška pri startu", "#FF4444")
            self.proc = None
            return False

    def stop_recording(self):
        if not self.proc:
            return
        self._emit_status("Zaustavljam...", "#FFCC00")
        try:
            if self.proc.stdin:
                self.proc.stdin.write("q\n")
                self.proc.stdin.flush()
        except:
            pass
        
        try:
            self.proc.wait(timeout=STOP_TIMEOUT_SEC)
        except:
            self.proc.kill()
        
        self._stderr_stop.set()
        self.is_recording = False
        self.is_paused = False
        self.sig_process_ended.emit(self.proc.poll() if self.proc else -1)
        self.proc = None
        self._emit_status("Sačuvano.", "#88FF88")

    def pause_toggle(self):
        if not self.is_recording or not self.proc:
            return
        try:
            self.proc.stdin.write("p\n")
            self.proc.stdin.flush()
            self.is_paused = not self.is_paused
            self._emit_status(
                "PAUZIRANO" if self.is_paused else "SNIMANJE",
                "#FFCC00" if self.is_paused else "#88FF88",
            )
        except:
            pass