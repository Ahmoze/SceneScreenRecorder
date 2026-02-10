from PySide6 import QtWidgets, QtCore, QtGui
from .constants import APP_TITLE, APP_VERSION, DEFAULT_OUTPUT_ROOT, PRESETS, load_config, save_config, ensure_output_root, suggest_preset_for_monitor
from .styling import CRIMSON, TERMINAL, build_qss
from .hardware import win32_list_monitors_with_dpi, GlobalHotkeys, GlobalHotkeyFilter
from .ffmpeg_ctrl import FfmpegController
from datetime import datetime

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.controller = FfmpegController()
        self.controller.sig_log.connect(self._log)
        self.controller.sig_status.connect(self._status)
        self.controller.sig_process_ended.connect(self._on_end)
        
        self.monitors = []
        self.current_theme = CRIMSON
        self.hotkeys = GlobalHotkeys()
        self.hk_filter = GlobalHotkeyFilter(self._hk_home, self._hk_end)
        self.app.installNativeEventFilter(self.hk_filter)

        self.tray = None  # da ne puca u closeEvent ako tray ne postoji
        
        self._init_ui()
        self._load_cfg()
        self._refresh_monitors()
        self.hotkeys.register()

        # Log startup
        self._log("GUI inicijalizovan.")
        self._log("Global hotkeys: HOME=pause/resume, END=stop.")

    def _init_ui(self):
        self.setWindowTitle(f"{APP_TITLE} - {APP_VERSION}")
        self.setMinimumSize(900, 620)
        cw = QtWidgets.QWidget()
        self.setCentralWidget(cw)
        layout = QtWidgets.QVBoxLayout(cw)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Header
        gb_head = QtWidgets.QGroupBox()
        gb_head.setTitle("")
        h = QtWidgets.QHBoxLayout(gb_head)
        left = QtWidgets.QVBoxLayout()

        lbl_title = QtWidgets.QLabel(APP_TITLE)
        lbl_title.setObjectName("HeaderTitle")
        lbl_sub = QtWidgets.QLabel("Win32 Physical Capture • Modular Edition")
        lbl_sub.setObjectName("HeaderSubTitle")

        left.addWidget(lbl_title)
        left.addWidget(lbl_sub)
        
        self.combo_theme = QtWidgets.QComboBox()
        self.combo_theme.addItems([CRIMSON.name, TERMINAL.name])
        self.combo_theme.currentIndexChanged.connect(self._theme_change)
        
        self.rec_dot = QtWidgets.QLabel()
        self.rec_dot.setFixedSize(14, 14)
        self.lbl_status = QtWidgets.QLabel("Idle")
        self.lbl_status.setObjectName("RecLabel")
        
        h.addLayout(left, 1)
        h.addWidget(QtWidgets.QLabel("Tema:"))
        h.addWidget(self.combo_theme)
        h.addSpacing(10)
        h.addWidget(self.rec_dot)
        h.addWidget(self.lbl_status)
        layout.addWidget(gb_head)
        
        # Settings
        gb_set = QtWidgets.QGroupBox("Settings")
        gl = QtWidgets.QGridLayout(gb_set)
        
        self.cb_mon = QtWidgets.QComboBox()
        self.cb_mon.currentIndexChanged.connect(self._mon_change)

        self.cb_res = QtWidgets.QComboBox()
        self.cb_res.addItems(["Native", "Custom"])
        self.cb_res.currentIndexChanged.connect(
            lambda: [
                self.ed_w.setEnabled(self.cb_res.currentIndex() == 1),
                self.ed_h.setEnabled(self.cb_res.currentIndex() == 1),
            ]
        )
        
        self.ed_w = QtWidgets.QLineEdit()
        self.ed_h = QtWidgets.QLineEdit()
        self.ed_w.setEnabled(False)
        self.ed_h.setEnabled(False)
        self.ed_w.setFixedWidth(110)
        self.ed_h.setFixedWidth(110)
        
        self.ed_out = QtWidgets.QLineEdit()
        self.btn_browse = QtWidgets.QPushButton("Browse...")
        self.btn_browse.clicked.connect(self._browse)
        
        self.sb_fps = QtWidgets.QSpinBox()
        self.sb_fps.setRange(1, 240)
        self.sb_fps.setValue(30)
        self.sb_fps.setFixedWidth(110)
        self.sb_fps.setFixedHeight(30)
        
        self.chk_delay = QtWidgets.QCheckBox("Delay start (2s)")
        self.chk_delay.setChecked(True)
        self.chk_tray = QtWidgets.QCheckBox("Start => Tray")
        self.chk_tray.setChecked(True)

        # NOVO: checkbox za sistemski zvuk (WASAPI)
        self.chk_sys_audio = QtWidgets.QCheckBox("Snimaj sistemski zvuk (WASAPI)")
        self.chk_sys_audio.setChecked(False)
        
        gl.addWidget(QtWidgets.QLabel("Monitor:"), 0, 0)
        gl.addWidget(self.cb_mon, 1, 0)
        gl.addWidget(QtWidgets.QLabel("Output:"), 0, 1)
        row_out = QtWidgets.QHBoxLayout()
        row_out.addWidget(self.ed_out, 1)
        row_out.addWidget(self.btn_browse)
        gl.addLayout(row_out, 1, 1)
        
        gl.addWidget(QtWidgets.QLabel("Rezolucija:"), 2, 0)
        gl.addWidget(self.cb_res, 3, 0)
        gl.addWidget(QtWidgets.QLabel("FPS:"), 2, 1)
        gl.addWidget(self.sb_fps, 3, 1)
        
        row_wh = QtWidgets.QHBoxLayout()
        row_wh.addWidget(QtWidgets.QLabel("W:"))
        row_wh.addWidget(self.ed_w)
        row_wh.addWidget(QtWidgets.QLabel("H:"))
        row_wh.addWidget(self.ed_h)
        gl.addLayout(row_wh, 4, 0)
        
        gl.addWidget(self.chk_delay, 4, 1)
        gl.addWidget(self.chk_tray, 5, 1)
        gl.addWidget(self.chk_sys_audio, 6, 1)  # audio checkbox
        
        # Info text
        inf = QtWidgets.QLabel(
            "Info: Win32 physical bounds. Start optionally hides to tray. "
            "SpinBox arrows are manually drawn."
        )
        inf.setWordWrap(True)
        gl.addWidget(inf, 0, 2, 7, 1)
        
        layout.addWidget(gb_set)
        
        # Controls
        gb_ctrl = QtWidgets.QGroupBox("Controls")
        vl = QtWidgets.QVBoxLayout(gb_ctrl)
        row_preset = QtWidgets.QHBoxLayout()
        self.cb_preset = QtWidgets.QComboBox()
        for p in PRESETS:
            self.cb_preset.addItem(p.name)
        self.cb_preset.currentIndexChanged.connect(self._preset_change)
        row_preset.addWidget(QtWidgets.QLabel("Preset:"))
        row_preset.addWidget(self.cb_preset, 1)
        
        row_btn = QtWidgets.QHBoxLayout()
        row_btn.setSpacing(12)
        self.btn_start = QtWidgets.QPushButton("START Recording")
        self.btn_start.clicked.connect(self._start)
        self.btn_start.setFixedWidth(190)
        self.btn_stop = QtWidgets.QPushButton("STOP")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.controller.stop_recording)
        self.btn_stop.setFixedWidth(190)
        
        row_btn.addStretch(1)
        row_btn.addWidget(self.btn_start)
        row_btn.addWidget(self.btn_stop)
        row_btn.addStretch(1)
        
        vl.addLayout(row_preset)
        vl.addLayout(row_btn)
        layout.addWidget(gb_ctrl)
        
        # Log
        gb_log = QtWidgets.QGroupBox("Log")
        l_log = QtWidgets.QVBoxLayout(gb_log)
        self.txt_log = QtWidgets.QPlainTextEdit()
        self.txt_log.setReadOnly(True)
        self.status = QtWidgets.QLabel("Spremno.")
        self.status.setObjectName("StatusLabel")
        l_log.addWidget(self.txt_log)
        l_log.addWidget(self.status)
        layout.addWidget(gb_log)
        
        # Tray
        self._setup_tray()
        
        self._apply_styles(CRIMSON)

    def _setup_tray(self):
        if not QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QtWidgets.QSystemTrayIcon(self)
        pix = QtGui.QPixmap(64, 64)
        pix.fill(QtCore.Qt.GlobalColor.transparent)
        p = QtGui.QPainter(pix)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        p.setBrush(QtGui.QColor(20, 20, 20, 220))
        p.drawEllipse(6, 6, 52, 52)
        p.setBrush(QtGui.QColor(80, 255, 120, 240))
        p.drawEllipse(40, 16, 10, 10)
        p.end()
        self.tray.setIcon(QtGui.QIcon(pix))
        
        menu = QtWidgets.QMenu()
        a1 = menu.addAction("Show/Hide")
        a1.triggered.connect(self._tray_toggle)
        a2 = menu.addAction("Stop & Save")
        a2.triggered.connect(self._tray_stop)
        menu.addSeparator()
        a3 = menu.addAction("Exit")
        a3.triggered.connect(self.close)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            lambda r: self._tray_toggle()
            if r == QtWidgets.QSystemTrayIcon.ActivationReason.Trigger
            else None
        )
        self.tray.show()

    def _log(self, t):
        self.txt_log.appendPlainText(f"[{datetime.now().strftime('%H:%M:%S')}] {t}")

    def _status(self, t, c):
        self.status.setText(t)
        self.status.setStyleSheet(
            f"QLabel#StatusLabel{{ color: {c}; font-weight: 900; }}"
        )
        self.lbl_status.setText(t.split(" ")[0])  # Short status for header
        
        # Update dot
        col = self.current_theme.idle
        if "Snimanje" in t or "Recording" in t:
            col = self.current_theme.recording
        if "Pauz" in t or "Paused" in t:
            col = self.current_theme.paused
        self.rec_dot.setStyleSheet(
            f"background-color: {col}; border-radius: 7px; "
            "border: 1px solid rgba(0,0,0,0.55);"
        )

    def _apply_styles(self, theme):
        self.setStyleSheet(build_qss(theme))
        self.current_theme = theme

    def _theme_change(self):
        self._apply_styles(TERMINAL if self.combo_theme.currentIndex() == 1 else CRIMSON)
    
    def _browse(self):
        d = QtWidgets.QFileDialog.getExistingDirectory(self, "Folder", self.ed_out.text())
        if d:
            self.ed_out.setText(d)
            self._save_cfg()

    def _refresh_monitors(self):
        self.monitors = win32_list_monitors_with_dpi()
        self.cb_mon.clear()
        for m in self.monitors:
            self.cb_mon.addItem(m.text)
        
    def _mon_change(self):
        if self.cb_mon.currentIndex() >= 0:
            m = self.monitors[self.cb_mon.currentIndex()]
            idx = suggest_preset_for_monitor(m.w, m.h)
            if idx < self.cb_preset.count():
                self.cb_preset.setCurrentIndex(idx)

    def _preset_change(self):
        p = PRESETS[self.cb_preset.currentIndex()]
        self.sb_fps.setValue(p.fps)
        self.controller.current_crf = p.crf
        self.cb_res.setCurrentIndex(1 if p.mode == "Custom" else 0)
        if p.width:
            self.ed_w.setText(str(p.width))
            self.ed_h.setText(str(p.height))

    def _start(self):
        if self.cb_mon.currentIndex() < 0:
            return
        mon = self.monitors[self.cb_mon.currentIndex()]
        root = self.ed_out.text()
        
        mode = "Custom" if self.cb_res.currentIndex() == 1 else "Native"
        cwh = (int(self.ed_w.text()), int(self.ed_h.text())) if mode == "Custom" else None

        record_sys_audio = self.chk_sys_audio.isChecked()
        
        if self.chk_tray.isChecked():
            self.hide()
        
        def run():
            if self.controller.start_recording(
                mon, mode, cwh, root, self.sb_fps.value(), self.controller.current_crf,
                record_audio=record_sys_audio
            ):
                self.btn_stop.setEnabled(True)
            else:
                self.show()
        
        ms = 2000 if self.chk_delay.isChecked() else 150
        QtCore.QTimer.singleShot(ms, run)
        
    def _on_end(self, code):
        self.btn_stop.setEnabled(False)
        self.show()

    def _hk_home(self):
        self.controller.pause_toggle()

    def _hk_end(self):
        self.controller.stop_recording()
    
    def _tray_toggle(self):
        if self.isVisible():
            self.hide()
        else:
            self.showNormal()
            self.activateWindow()

    def _tray_stop(self):
        self.controller.stop_recording()

    def _load_cfg(self):
        cfg = load_config()
        self.ed_out.setText(cfg.get("OutputFolder", DEFAULT_OUTPUT_ROOT))
        
    def _save_cfg(self):
        save_config({"OutputFolder": self.ed_out.text(), "Theme": self.current_theme.name})
        
    def closeEvent(self, e):
        self.hotkeys.unregister()
        if self.controller.is_recording:
            self.controller.stop_recording()
        self._save_cfg()
        if self.tray:
            self.tray.hide()
        super().closeEvent(e)