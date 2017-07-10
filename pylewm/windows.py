from pylewm import pylecommand, queue
import pylewm.monitors
import pylewm.focus
import win32gui, win32con
import ctypes

IGNORED_CLASSES = {"applicationframewindow"}

def ignoreWindowClass(cls):
    IGNORED_CLASSES.add(cls.lower())

def isEmptyWindow(window):
    rect = win32gui.GetWindowRect(window)
    return rect[2] <= rect[0] or rect[3] <= rect[1]
    
def isRelevantWindow(window):
    cls = win32gui.GetClassName(window)
    return cls.lower() not in IGNORED_CLASSES

def gatherWindows():
    windows = []
    def enumWin(hwnd, param):
        if not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd)
        if len(title) == 0:
            return
        #TODO: HACK: Should detect the desktop window instead of using its title
        if title == "Program Manager":
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
    def getDim(rect):
        if dir == "left": return rect[0]
        if dir == "up": return rect[1]
        if dir == "right": return rect[0]
        return rect[1]
    def getOtherDim(rect):
        if dir == "left": return rect[1]
        if dir == "up": return rect[0]
        if dir == "right": return rect[1]
        return rect[0]
    def isAfter(A, B):
        if dir == "left" or dir == "up":
            return B < A
        else:
            return A < B
    curWindow = win32gui.GetForegroundWindow()
    curRect = win32gui.GetWindowRect(curWindow)
    curStart = getDim(curRect)
    curOtherDim = getOtherDim(curRect)
    maxDiff = float(1e20)
    selWin = None
    
    # Find which window is the closest in the particular direction
    def checkWindows():
        nonlocal maxDiff
        nonlocal selWin
        for otherWin in gatherWindows():
            if otherWin == curWindow:
                continue
            otherRect = win32gui.GetWindowRect(otherWin)
            otherStart = getDim(otherRect)
            otherOtherDim = getOtherDim(otherRect)
            
            # Skip windows not at all extended in the right direction
            if not isAfter(curStart, otherStart):
                continue
                
            diff = float(abs(curStart - otherStart)) + float(abs(curOtherDim - otherOtherDim) / 10000.0)
            if diff < maxDiff:
                # Closer to the window's starting edge
                maxDiff = diff
                selWin = otherWin
            
    # Focus the window we found
    checkWindows()
    if selWin is not None:
        pylewm.focus.set(selWin)
    else:
        # Wrap around to the other side
        curStart = getDim(pylewm.monitors.DesktopArea) - curStart
        checkWindows()
        if selWin is not None:
            pylewm.focus.set(selWin)