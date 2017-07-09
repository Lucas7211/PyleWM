from pylewm import pylecommand, queue
import win32gui, win32con

def isEmptyWindow(window):
    rect = win32gui.GetWindowRect(window)
    return rect[2] <= rect[0] or rect[3] <= rect[1]

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
        windows.append(hwnd)
    win32gui.EnumWindows(enumWin, None)
    return windows

@pylecommand
def close():
    """ Close the currently active window. """
    win32gui.PostMessage(win32gui.GetForegroundWindow(), win32con.WM_CLOSE, 0, 0)
    
def setFocusToWM():
    win32gui.SetForegroundWindow(win32gui.GetActiveWindow())
    
def setFocusTo(window, num=10):
    try:
        win32gui.SetForegroundWindow(window)
        return True
    except:
        # Try it a few more times. Maybe windows will let us do it later.
        if num > 0:
            queue(lambda: setFocusTo(window, num-1))
        else:
            print("COULD NOT SET FOREGROUND TO "+win32gui.GetWindowText(window))
    
@pylecommand
def focus_dir(dir="left"):
    """ Switch focus to a window in a particular direction relative to the currently focused window. """
    def getEndDim(rect):
        if dir == "left": return rect[0]
        if dir == "up": return rect[1]
        if dir == "right": return rect[2]
        return rect[3]
    def getStartDim(rect):
        if dir == "left": return rect[2]
        if dir == "up": return rect[3]
        if dir == "right": return rect[0]
        return rect[1]
    def isAfter(A, B):
        if dir == "left" or dir == "up":
            return B < A
        else:
            return A < B
    curWindow = win32gui.GetForegroundWindow()
    curRect = win32gui.GetWindowRect(curWindow)
    curStart = getStartDim(curRect)
    curEnd = getEndDim(curRect)
    maxDiff = 1e20
    minBorderDiff = 0
    selWin = None
    
    # Find which window is the closest in the particular direction
    for otherWin in gatherWindows():
        if otherWin == curWindow:
            continue
        otherRect = win32gui.GetWindowRect(otherWin)
        otherStart = getStartDim(otherRect)
        otherEnd = getEndDim(otherRect)
        
        # Skip windows not at all extended in the right direction
        if not isAfter(curEnd, otherEnd):
            continue
            
        # Check which window is the closest window to the end
        if isAfter(curEnd, otherStart):
            # No overlap, start is the start of the other window
            intersect = otherStart
        else:
            # Has overlap, start is the end of the current window
            intersect = curEnd
        
        diff = abs(intersect - curEnd)
        borderDiff = abs(otherEnd - curEnd)
        if diff < maxDiff:
            # Closer to the window's starting edge
            maxDiff = diff
            minBorderDiff = borderDiff
            selWin = otherWin
        elif diff == maxDiff:
            # Both overlapping the window, use the one with the closest far edge
            if borderDiff < minBorderDiff:
                minBorderDiff = borderDiff
                selWin = otherWin
            
    # Focus the window we found
    selName = win32gui.GetWindowText(selWin)
    if selWin is not None:
        setFocusTo(selWin)