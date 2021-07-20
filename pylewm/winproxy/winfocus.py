import pylewm.winproxy.winfuncs as winfuncs
from pylewm.commands import Commands
from pylewm.rects import Rect
from pylewm.winproxy.windowproxy import WindowsByHandle, WindowProxy, ProxyCommands

import pythoncom, win32com
import functools

OnFocusChanged = None

FocusHWND = None
FocusWindowProxy = None

PendingFocusProxy = None
PendingFocusRect = None
PendingFocusTries = 0

CursorPos = (0, 0)
CursorPoint = winfuncs.w.POINT()

def update_focused_window():
    """ Update which tracked window currently has the user's focus. """
    global FocusHWND
    global FocusWindowProxy
    global PendingFocusProxy
    global PendingFocusTries
    global PendingFocusRect
    global CursorPos

    if winfuncs.GetCursorPos(winfuncs.c.byref(CursorPoint)):
        CursorPos = (CursorPoint.x, CursorPoint.y)

    CurFocus = winfuncs.GetForegroundWindow()
    force_update = False

    if PendingFocusProxy:
        if CurFocus == PendingFocusProxy._hwnd:
            # We've completed focusing our pending window
            PendingFocusProxy = None
        else:
            # Attempt to set focus, if it takes too many tries we stop
            attempt_focus_window_handle(PendingFocusProxy._hwnd, PendingFocusRect)

            PendingFocusTries += 1
            if PendingFocusTries > 10:
                PendingFocusProxy = None

                CurFocus = winfuncs.GetForegroundWindow()
                force_update = True
            else:
                CurFocus = PendingFocusProxy._hwnd


    if CurFocus != FocusHWND or force_update:
        FocusHWND = CurFocus
        if FocusHWND in WindowsByHandle:
            FocusWindowProxy = WindowsByHandle[FocusHWND]
        else:
            FocusWindowProxy = None

        # Send a message to the command thread to indicate that the focused window has changed
        Commands.queue(functools.partial(OnFocusChanged, FocusWindowProxy))


COM_INITIALIZED = False
def attempt_focus_window_handle(hwnd, rect=None):
    try:
        global COM_INITIALIZED
        if not COM_INITIALIZED:
            pythoncom.CoInitialize()
            ComInitialized = True

        # Send a bogus key to ourselves so we are 
        # marked as having received keyboard input, which
        # makes windows determine we have the power to change
        # window focus. Somehow.
        shell = win32com.client.Dispatch("WScript.Shell")
        shell.SendKeys('{F15}')
    except Exception as ex:
        pass

    winfuncs.SetForegroundWindow(hwnd)
    if rect:
        winfuncs.SetCursorPos(rect.left + 20, rect.top + 10)
    return True

def focus_window(proxy : WindowProxy, move_mouse = True):
    """ Set a new window to get focus. Called from command thread. """
    def focus_cmd():
        global PendingFocusProxy
        global PendingFocusTries
        global PendingFocusRect

        PendingFocusProxy = proxy
        PendingFocusTries = 0
        if move_mouse:
            PendingFocusRect = proxy._info.rect
        else:
            PendingFocusRect = None
    ProxyCommands.queue(focus_cmd)

def focus_shell_window(rect : Rect):
    """ Set a new window to get focus. Called from command thread. """
    def focus_cmd():
        global PendingFocusProxy
        global PendingFocusTries
        global PendingFocusRect

        PendingFocusProxy = winfuncs.GetShellWindow()
        PendingFocusTries = 0
        PendingFocusRect = rect
    ProxyCommands.queue(focus_cmd)

def get_cursor_position():
    return CursorPos