import sys
import ctypes
from dataclasses import dataclass
from typing import Optional, List
from PySide6 import QtCore
from ctypes import wintypes

@dataclass
class WinMonitor:
    index: int
    device: str
    left: int
    top: int
    right: int
    bottom: int
    dpi_x: Optional[int] = None
    dpi_y: Optional[int] = None
    scale_pct: Optional[int] = None

    @property
    def w(self) -> int: return self.right - self.left
    @property
    def h(self) -> int: return self.bottom - self.top
    @property
    def text(self) -> str:
        dpi_info = f" | DPI {self.dpi_x} ({self.scale_pct}%)" if self.dpi_x else ""
        return f"Monitor {self.index} - {self.w}x{self.h} ({self.device}) @ {self.left},{self.top}{dpi_info}"

def try_set_per_monitor_dpi_awareness_v2() -> bool:
    if sys.platform != "win32": return False
    try:
        user32 = ctypes.windll.user32
        if hasattr(user32, "SetProcessDpiAwarenessContext"):
            val = -4 # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
            return bool(user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(val)))
        if hasattr(user32, "SetProcessDPIAware"):
            return bool(user32.SetProcessDPIAware())
    except Exception: return False
    return False

def win32_list_monitors_with_dpi() -> List[WinMonitor]:
    if sys.platform != "win32": return []
    user32 = ctypes.windll.user32
    monitors = []

    class RECT(ctypes.Structure):
        _fields_ = [("left", wintypes.LONG), ("top", wintypes.LONG), ("right", wintypes.LONG), ("bottom", wintypes.LONG)]
    class MONITORINFOEXW(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", RECT), ("rcWork", RECT), ("dwFlags", wintypes.DWORD), ("szDevice", wintypes.WCHAR * 32)]

    def _callback(hmon, hdc, lprc, lparam):
        info = MONITORINFOEXW()
        info.cbSize = ctypes.sizeof(MONITORINFOEXW)
        if user32.GetMonitorInfoW(hmon, ctypes.byref(info)):
            m = WinMonitor(len(monitors)+1, info.szDevice, int(info.rcMonitor.left), int(info.rcMonitor.top), int(info.rcMonitor.right), int(info.rcMonitor.bottom))
            try:
                shcore = ctypes.windll.shcore
                dx, dy = ctypes.c_uint(0), ctypes.c_uint(0)
                if shcore.GetDpiForMonitor(hmon, 0, ctypes.byref(dx), ctypes.byref(dy)) == 0:
                    m.dpi_x, m.dpi_y = int(dx.value), int(dy.value)
                    m.scale_pct = int(round((m.dpi_x / 96.0) * 100.0))
            except: pass
            monitors.append(m)
        return True

    MonitorEnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(RECT), wintypes.LPARAM)
    user32.EnumDisplayMonitors(0, 0, MonitorEnumProc(_callback), 0)
    return monitors

class GlobalHotkeys:
    def __init__(self): self.registered = False
    def register(self) -> bool:
        if sys.platform != "win32": return False
        try:
            u32 = ctypes.windll.user32
            ok1 = u32.RegisterHotKey(None, 1, 0x4000, 0x24) # HOME
            ok2 = u32.RegisterHotKey(None, 2, 0x4000, 0x23) # END
            self.registered = bool(ok1 and ok2)
            return self.registered
        except: return False
    def unregister(self):
        if self.registered:
            try:
                ctypes.windll.user32.UnregisterHotKey(None, 1)
                ctypes.windll.user32.UnregisterHotKey(None, 2)
            except: pass

class GlobalHotkeyFilter(QtCore.QAbstractNativeEventFilter):
    def __init__(self, on_home, on_end):
        super().__init__()
        self.on_home = on_home
        self.on_end = on_end
    def nativeEventFilter(self, eventType, message):
        if sys.platform == "win32" and eventType in (b"windows_generic_MSG", b"windows_dispatcher_MSG"):
            msg = ctypes.cast(int(message), ctypes.POINTER(wintypes.MSG)).contents
            if msg.message == 0x0312: # WM_HOTKEY
                if int(msg.wParam) == 1: self.on_home(); return True, 0
                if int(msg.wParam) == 2: self.on_end(); return True, 0
        return False, 0
