import pylewm
import win32api, win32con

WindowsWithTitlebar = set()

def applyTiled(window):
    pass
    # if pylewm.config.get("HideTitlebar", False):
        # style = win32api.GetWindowLong(window, win32con.GWL_STYLE)
        # if style & win32con.WS_CAPTION:
            # style = style & ~win32con.WS_CAPTION
            # win32api.SetWindowLong(window, win32con.GWL_STYLE, style)
            # WindowsWithTitlebar.add(window)
    
def applyFloating(window):
    pass