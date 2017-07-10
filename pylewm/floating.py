from pylewm import pylecommand, pyletick
import pylewm.focus
import pylewm.style
import pylewm.rects
import win32gui,win32con, win32api

FloatingWindows = []

@pylecommand
def focus_dir(dir="left"):
    """ Switch focus to a window in a particular direction relative to the currently focused window. """
    curWindow = win32gui.GetForegroundWindow()
    if not win32gui.IsWindow(curWindow):
        return
    curRect = win32gui.GetWindowRect(curWindow)
    
    selWin = pylewm.rects.getClosestInDirection(dir, curRect,
        (win for win in FloatingWindows if not win.hidden), 
        lambda win: win32gui.GetWindowRect(win.window), wrap=True,
        ignore=getFloatingWindowFor(curWindow))
    if selWin is not None:
        selWin.focus()
        
def getFloatingWindowFor(hwnd):
    for win in FloatingWindows:
        if win.window == hwnd:
            return win
    return None
    
def isFloatingFocused():
    curWindow = win32gui.GetForegroundWindow()
    return getFloatingWindowFor(curWindow) is not None
    
def getClosestFloatingWindow(toRect):
    if not FloatingWindows:
        return None
    return pylewm.rects.getClosestTo(toRect,
        (win for win in FloatingWindows if not win.hidden),
        lambda win: win32gui.GetWindowRect(win.window))

class FloatingWindow:
    def __init__(self, window):
        self.window = window
        self.parent = win32api.GetWindowLong(window, win32con.GWL_HWNDPARENT)
        
        self.parentStack = [self.parent]
        check = self.parent
        while win32gui.IsWindow(check):
            self.parentStack.append(check)
            check = win32api.GetWindowLong(check, win32con.GWL_HWNDPARENT)
     
        self.show()          
        print(f"ADD FLOATING {self.title}")
    
    def update(self):
        return win32gui.IsWindow(self.window)
    
    @property
    def title(self):
        return win32gui.GetWindowText(self.window)
        
    def focus(self):
        print(f"FOCUS FLOATING {self.title} hidden:{self.hidden}")
        pylewm.focus.set(self.window)
        
    def show(self):
        # Floating windows are always on top
        print(f"SHOW FLOATING {self.title}")
        self.rect = win32gui.GetWindowRect(self.window)
        win32gui.SetWindowPos(self.window, win32con.HWND_TOPMOST,
                        self.rect[0], self.rect[1],
                        self.rect[2] - self.rect[0], self.rect[3] - self.rect[1],
                        win32con.SWP_NOACTIVATE)
        self.hidden = False
        
    def hide(self):
        print(f"HIDE FLOATING {self.title}")
        self.rect = win32gui.GetWindowRect(self.window)
        win32gui.SetWindowPos(self.window, win32con.HWND_BOTTOM,
                        self.rect[0], self.rect[1],
                        self.rect[2] - self.rect[0], self.rect[3] - self.rect[1],
                        win32con.SWP_NOACTIVATE)
        self.hidden = True

def hideWithParent(parent):
    for win in FloatingWindows:
        if parent in win.parentStack:
            win.hide()
    
def showWithParent(parent):
    for win in FloatingWindows:
        if parent in win.parentStack:
            win.show()
    
def onWindowCreated(window):
    FloatingWindows.append(FloatingWindow(window))
    
@pyletick
def tickFloating():
    for win in FloatingWindows[:]:
        if not win.update():
            FloatingWindows.remove(win)