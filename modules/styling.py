from dataclasses import dataclass
from PySide6 import QtWidgets, QtGui, QtCore

@dataclass
class Theme:
    name: str
    accent: str
    accent_soft: str
    text_primary: str
    text_secondary: str
    window_base: str
    panel_rgba: str
    input_rgba: str
    idle: str
    recording: str
    paused: str

CRIMSON = Theme("Crimson", "#FF9A0028", "#559A0028", "#FFF5F5", "#FFB0A0", "#050000", "rgba(10, 2, 4, 0.84)", "rgba(0, 0, 0, 0.35)", "#55202020", "#FF9A0028", "#FFCC66")
TERMINAL = Theme("Terminal Green", "#00FF66", "#5500FF66", "#E0FFE0", "#99FFCC", "#020702", "rgba(2, 16, 6, 0.84)", "rgba(0, 0, 0, 0.35)", "#335533", "#00FF66", "#FFFF66")

def build_qss(theme: Theme) -> str:
    return f"""
    QMainWindow, QWidget {{ background-color: {theme.window_base}; color: {theme.text_secondary}; font-family: "Segoe UI"; font-size: 11px; }}
    QLabel {{ padding: 1px 0 2px 0; min-height: 16px; }}
    QLabel#HeaderTitle {{ color: {theme.text_primary}; font-size: 18px; font-weight: 800; }}
    QLabel#HeaderSubTitle {{ color: {theme.text_secondary}; font-size: 11px; }}
    QGroupBox {{ border: 1px solid {theme.accent_soft}; border-radius: 10px; margin-top: 8px; padding: 8px; background-color: {theme.panel_rgba}; }}
    QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; padding: 0 6px; color: {theme.text_primary}; font-weight: 700; }}
    QLineEdit, QPlainTextEdit {{ background-color: {theme.input_rgba}; color: {theme.text_primary}; border: 1px solid {theme.accent_soft}; border-radius: 8px; min-height: 30px; padding: 4px 8px; selection-background-color: rgba(255,255,255,0.18); }}
    QComboBox {{ background-color: rgba(15,15,15,0.90); color: {theme.text_primary}; border: 1px solid {theme.accent_soft}; border-radius: 8px; min-height: 30px; padding: 4px 28px 4px 8px; }}
    QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right; width: 24px; border-left: 0px; }}
    QComboBox QAbstractItemView {{ background-color: rgba(15,15,15,0.98); color: {theme.text_primary}; selection-background-color: rgba(255,255,255,0.14); selection-color: {theme.text_primary}; outline: 0; border: 1px solid {theme.accent_soft}; }}
    QPushButton {{ min-height: 30px; padding: 6px 12px; background-color: rgba(0,0,0,0.28); color: {theme.text_primary}; border: 1px solid {theme.accent_soft}; border-radius: 8px; font-weight: 800; }}
    QPushButton:hover {{ border: 1px solid {theme.accent}; background-color: rgba(0,0,0,0.34); }}
    QPushButton:disabled {{ color: #777777; border: 1px solid #444444; background-color: rgba(0,0,0,0.18); }}
    QCheckBox {{ color: {theme.text_primary}; font-weight: 700; }}
    QLabel#StatusLabel {{ color: #88FF88; font-weight: 900; }}
    QLabel#RecLabel {{ color: {theme.text_secondary}; font-weight: 900; }}
    """

class SpinBoxArrowStyle(QtWidgets.QProxyStyle):
    def drawComplexControl(self, control, option, painter, widget=None):
        if control == QtWidgets.QStyle.ComplexControl.CC_SpinBox and isinstance(option, QtWidgets.QStyleOptionSpinBox):
            opt = QtWidgets.QStyleOptionSpinBox(option)
            opt.subControls = QtWidgets.QStyle.SubControl.SC_SpinBoxFrame | QtWidgets.QStyle.SubControl.SC_SpinBoxEditField
            super().drawComplexControl(control, opt, painter, widget)

            up_rect = self.subControlRect(control, option, QtWidgets.QStyle.SubControl.SC_SpinBoxUp, widget)
            down_rect = self.subControlRect(control, option, QtWidgets.QStyle.SubControl.SC_SpinBoxDown, widget)
            
            active = option.activeSubControls
            up_hover = bool(active & QtWidgets.QStyle.SubControl.SC_SpinBoxUp)
            down_hover = bool(active & QtWidgets.QStyle.SubControl.SC_SpinBoxDown)

            if widget:
                pal = widget.palette()
                arrow_color = pal.color(QtGui.QPalette.ColorRole.ButtonText)
                if not arrow_color.isValid(): arrow_color = pal.color(QtGui.QPalette.ColorRole.Text)
                hover_bg = pal.color(QtGui.QPalette.ColorRole.Button)
                hover_bg.setAlpha(80)
            else:
                arrow_color = QtGui.QColor(240, 240, 240)
                hover_bg = QtGui.QColor(255, 255, 255, 40)

            painter.save()
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)

            def draw_tri(r, up, hov):
                if r.width() <= 0: return
                if hov:
                    painter.save()
                    painter.setPen(QtCore.Qt.PenStyle.NoPen)
                    painter.setBrush(hover_bg)
                    painter.drawRect(r.adjusted(1,1,-1,-1))
                    painter.restore()
                
                s = max(6, min(r.width(), r.height()) - 6) // 2
                c = r.center()
                dy = -s if up else s
                # Koordinate za trougao
                if up:
                    pts = [QtCore.QPoint(c.x(), c.y() - s), QtCore.QPoint(c.x() - s, c.y() + s), QtCore.QPoint(c.x() + s, c.y() + s)]
                else:
                    pts = [QtCore.QPoint(c.x() - s, c.y() - s), QtCore.QPoint(c.x() + s, c.y() - s), QtCore.QPoint(c.x(), c.y() + s)]
                
                painter.setPen(QtCore.Qt.PenStyle.NoPen)
                painter.setBrush(arrow_color)
                painter.drawPolygon(QtGui.QPolygon(pts))

            draw_tri(up_rect, True, up_hover)
            draw_tri(down_rect, False, down_hover)
            painter.restore()
            return
        super().drawComplexControl(control, option, painter, widget)
