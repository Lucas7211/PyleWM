import pylewm.winproxy.winfuncs as winfuncs
from pylewm.commands import Commands
from pylewm.rects import Rect
from pylewm.winproxy.windowproxy import WindowsByHandle, WindowProxy, ProxyCommands, WindowProxyLock

import pythoncom, win32com
import functools

OnFocusChanged = None

FocusHWND = None
FocusWindowProxy = None

PendingFocusProxy = None
PendingFocusRect = None
PendingFocusTries = 0

ShellWindowProxy = None

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
        if not PendingFocusProxy.valid:
            PendingFocusProxy = None
        else:
            # Attempt to set focus, if it takes too many tries we stop
            attempt_focus_window_handle(PendingFocusProxy._hwnd, PendingFocusRect)

            PendingFocusTries += 1
            CurFocus = winfuncs.GetForegroundWindow()

            if CurFocus == PendingFocusProxy._hwnd:
                # We've completed focusing our pending window
                PendingFocusProxy = None
            elif PendingFocusTries > 10:
                PendingFocusProxy = None
                force_update = True
            else:
                CurFocus = PendingFocusProxy._hwnd


    if CurFocus != FocusHWND or force_update:
        proxy = get_proxy(CurFocus)
        if proxy and proxy.initialized:
            FocusHWND = CurFocus
            FocusWindowProxy = proxy

            # Send a message to the command thread to indicate that the focused window has changed
            Commands.queue(functools.partial(OnFocusChanged, FocusWindowProxy))


COM_INITIALIZED = False
def attempt_focus_window_handle(hwnd, rect=None):
    print(f"Attempt focus {get_proxy(hwnd)}")
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
            if proxy._layout_dirty:
                with WindowProxyLock:
                    PendingFocusRect = proxy._layout_position.copy()
            else:
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
        global ShellWindowProxy

        if not ShellWindowProxy:
            shell_hwnd = winfuncs.GetShellWindow()
            ShellWindowProxy = get_proxy(shell_hwnd)

        PendingFocusProxy = ShellWindowProxy
        PendingFocusTries = 0
        PendingFocusRect = rect
    ProxyCommands.queue(focus_cmd)

def get_cursor_position():
    return CursorPos

def get_proxy(hwnd) -> WindowProxy:
    global WindowsByHandle
    if hwnd in WindowsByHandle:
        return WindowsByHandle[hwnd]
    else:
        return None