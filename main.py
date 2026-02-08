import sys
from PySide6 import QtWidgets, QtGui
from modules.main_window import MainWindow
from modules.styling import SpinBoxArrowStyle
from modules.hardware import try_set_per_monitor_dpi_awareness_v2
from modules.constants import APP_TITLE

def main():
    if sys.platform != "win32":
        print("This application requires Windows (Win32 API).")
        sys.exit(1)

    dpi_ok = try_set_per_monitor_dpi_awareness_v2()

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    
    # Globalni stil: naš QProxyStyle koji crta strelice u CC_SpinBox
    base_style = app.style()
    app.setStyle(SpinBoxArrowStyle(base_style))
    
    # Font rendering fix
    f = QtWidgets.QApplication.font()
    try:
        f.setHintingPreference(QtGui.QFont.HintingPreference.PreferFullHinting)
        QtWidgets.QApplication.setFont(f)
    except Exception:
        pass

    w = MainWindow(app)
    # Log DPI status to internal log if needed, or print
    print(f"DPI awareness set: {'OK' if dpi_ok else 'FAIL/Unsupported'}")
    w.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
