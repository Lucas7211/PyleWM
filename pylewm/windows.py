from pylewm import pylecommand, queue, config
import pylewm.focus
import pylewm.rects
import pylewm.selector
import win32gui, win32con
import ctypes

IGNORED_CLASSES = {"applicationframewindow"}
IGNORED_WINDOWS = {"program manager"}

def ignoreWindowClass(cls):
    IGNORED_CLASSES.add(cls.lower())

def isEmptyWindow(window):
    rect = win32gui.GetWindowRect(window)
    return rect[2] <= rect[0] or rect[3] <= rect[1]
    
def isRelevantWindow(window):
    if pylewm.selector.matches(window, config.get("IgnoreWindows", [])):
        return False
    cls = win32gui.GetClassName(window)
    title = win32gui.GetWindowText(window)
    return cls.lower() not in IGNORED_CLASSES and title.lower() not in IGNORED_WINDOWS

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
        return
    curRect = win32gui.GetWindowRect(curWindow)
    
    selWin = pylewm.rects.getClosestInDirection(dir, curRect, gatherWindows(), 
        lambda win: win32gui.GetWindowRect(win), wrap=True, ignore=curWindow)
    if selWin is not None:
        pylewm.focus.set(selWin)

def banish(window):
    if not win32gui.IsIconic(window):
        win32gui.ShowWindow(window, win32con.SW_MINIMIZE)

def summon(window):
    if win32gui.IsIconic(window):
        win32gui.ShowWindow(window, win32con.SW_RESTORE)
