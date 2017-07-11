import pylewm
import win32api, win32con, win32gui

WindowsWithTitlebar = set()

def applyTiled(window):
    className = win32gui.GetClassName(window)
    if className in pylewm.config.get("HideTitlebarWindowClasses", {}):
        style = win32api.GetWindowLong(window, win32con.GWL_STYLE)
        if style & win32con.WS_CAPTION:
            style = style & ~win32con.WS_CAPTION
            win32api.SetWindowLong(window, win32con.GWL_STYLE, style)
            WindowsWithTitlebar.add(window)
    
def applyFloating(window):
    pass