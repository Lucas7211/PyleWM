from pylewm import pylecommand, queue, config
import pylewm.focus
import pylewm.rects
import pylewm.selector
import pylewm.filters
import win32gui, win32con, win32api
import ctypes
import traceback

IGNORED_CLASSES = {
    "windows.ui.core.corewindow", # Always directly under an ApplicationFrameWindow, so safe to ignore
    "progman",
}

IGNORED_WINDOWS = {
    "program manager", # The desktop window
}

def ignoreWindowClass(cls):
    IGNORED_CLASSES.add(cls.lower())

def isEmptyWindow(window):
    rect = win32gui.GetWindowRect(window)
    return rect[2] <= rect[0] or rect[3] <= rect[1]

def isChildWindow(window):
    parent = win32api.GetWindowLong(window, win32con.GWL_HWNDPARENT)
    return win32gui.IsWindow(parent)

def isVisible(window):
    if not win32gui.IsWindow(window):
        return False
    if win32gui.IsIconic(window):
        return False
    return win32gui.IsWindowVisible(window)
    
def isRelevantWindow(window):
    if pylewm.filters.is_ignored(window):
        return False
    cls = win32gui.GetClassName(window)
    title = win32gui.GetWindowText(window)
    if isTaskbarIgnored(window):
        return False
    return cls.lower() not in IGNORED_CLASSES and title.lower() not in IGNORED_WINDOWS

def isTaskbarIgnored(window):
    style = win32api.GetWindowLong(window, win32con.GWL_STYLE)
    exStyle = win32api.GetWindowLong(window, win32con.GWL_EXSTYLE)
    # NOACTIVATE windows that aren't APPWINDOW are ignored by
    # the taskbar, so we probably should ignore them as well
    if (exStyle & win32con.WS_EX_NOACTIVATE) and not (exStyle & win32con.WS_EX_APPWINDOW):
        return True
    return False

def gatherWindows():
    windows = []
    def enumWin(hwnd, param):
        if not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd)
        if len(title) == 0:
            return
        if isEmptyWindow(hwnd):
            return
        if win32gui.IsIconic(hwnd):
            return
        if not isRelevantWindow(hwnd):
            return
        windows.append(hwnd)
    win32gui.EnumWindows(enumWin, None)
    return windows

@pylecommand
def close():
    """ Close the currently active window. """
    print(f"CLOSE {win32gui.GetWindowText(win32gui.GetForegroundWindow())}")
    win32gui.PostMessage(win32gui.GetForegroundWindow(), win32con.WM_CLOSE, 0, 0)
    
@pylecommand
def focus_dir(dir="left"):
    """ Switch focus to a window in a particular direction relative to the currently focused window. """
    curWindow = win32gui.GetForegroundWindow()
    if not win32gui.IsWindow(curWindow):
        return False
    curRect = win32gui.GetWindowRect(curWindow)
    
    selWin = pylewm.rects.getClosestInDirection(dir, curRect, gatherWindows(), 
        lambda win: win32gui.GetWindowRect(win), wrap=True, ignore=curWindow)
    if selWin is not None:
        pylewm.focus.set(selWin)
        return True
    else:
        return False

@pylecommand
def poke_size():
    """ Change the current window's size back and forth to make it update. """
    curWindow = win32gui.GetForegroundWindow()
    if not win32gui.IsWindow(curWindow):
        return

    curRect = win32gui.GetWindowRect(curWindow)
    move(curWindow, (curRect[0]+2, curRect[1]+2, curRect[2]-2, curRect[3]-2))
    move(curWindow, curRect)

def banish(window):
    if not win32gui.IsIconic(window):
        win32gui.ShowWindow(window, win32con.SW_MINIMIZE)

def summon(window):
    if win32gui.IsIconic(window):
        win32gui.ShowWindow(window, win32con.SW_RESTORE)

def move(window, newScreenRect, topmost=False, bottom=False):
    setting = win32con.HWND_TOP
    if bottom:
        setting = win32con.HWND_BOTTOM
    if topmost:
        setting = win32con.HWND_TOPMOST

    try:
        if len(newScreenRect) == 2:
            curRect = win32gui.GetWindowRect(window)
            width = curRect[2] - curRect[0]
            height = curRect[3] - curRect[1]
        else:
            width = newScreenRect[2] - newScreenRect[0]
            height = newScreenRect[3] - newScreenRect[1]
        clientPos = newScreenRect[0:2]

        if width < 16 or height < 16:
            return
        if not pylewm.rects.overlapsDesktopArea((clientPos[0], clientPos[1], clientPos[0]+width, clientPos[1]+height)):
            return

        win32gui.SetWindowPos(window, setting, clientPos[0], clientPos[1], width, height, win32con.SWP_NOACTIVATE)
    except:
        try:
            print("Error setting window {win32gui.getWindowText(window)} to position {newScreenRect}")
        except:
            pass
        traceback.print_exc()
        traceback.print_stack()

def set_top(window):
    try:
        win32gui.SetWindowPos(window, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                win32con.SWP_NOACTIVATE | win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
    except:
        try:
            print("Error setting window {win32gui.getWindowText(window)} to position {newScreenRect}")
        except:
            pass
        traceback.print_exc()
        traceback.print_stack()

def set_bottom(window):
    try:
        win32gui.SetWindowPos(window, win32con.HWND_BOTTOM, 0, 0, 0, 0,
                win32con.SWP_NOACTIVATE | win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
    except:
        try:
            print("Error setting window {win32gui.getWindowText(window)} to position {newScreenRect}")
        except:
            pass
        traceback.print_exc()
        traceback.print_stack()
