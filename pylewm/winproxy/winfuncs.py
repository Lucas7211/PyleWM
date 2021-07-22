import ctypes as c
import ctypes.wintypes as w

tEnumWindowFunc = c.CFUNCTYPE(None, w.HWND, w.LPARAM)

def no_errcheck(result, func, args):
    return result

EnumWindows = c.WINFUNCTYPE(
    w.BOOL,
    tEnumWindowFunc, w.LPARAM
)(("EnumWindows", c.windll.user32))

GetWindowTextW = c.WINFUNCTYPE(
    c.c_int,
    w.HWND, w.LPWSTR, c.c_int,
)(("GetWindowTextW", c.windll.user32))

def WindowGetTitle(hwnd):
    buffer = c.create_unicode_buffer(256)
    GetWindowTextW(hwnd, buffer, c.sizeof(buffer))
    return buffer.value

GetClassNameW = c.WINFUNCTYPE(
    c.c_int,
    w.HWND, w.LPWSTR, c.c_int,
)(("GetClassNameW", c.windll.user32))

def WindowGetClass(hwnd):
    buffer = c.create_unicode_buffer(256)
    GetClassNameW(hwnd, buffer, c.sizeof(buffer))
    return buffer.value

IsWindow = c.WINFUNCTYPE(
    w.BOOL,
    w.HWND,
)(("IsWindow", c.windll.user32))

IsWindowVisible = c.WINFUNCTYPE(
    w.BOOL,
    w.HWND,
)(("IsWindowVisible", c.windll.user32))

GetWindowLongA = c.WINFUNCTYPE(
    w.LONG,
    w.HWND, c.c_int,
)(("GetWindowLongA", c.windll.user32))

SetWindowLongA = c.WINFUNCTYPE(
    w.LONG,
    w.HWND, c.c_int, w.LONG,
)(("SetWindowLongA", c.windll.user32))

GWL_EXSTYLE = -20
def WindowGetExStyle(hwnd):
    return GetWindowLongA(hwnd, GWL_EXSTYLE)

GWL_STYLE = -16
def WindowGetStyle(hwnd):
    return GetWindowLongA(hwnd, GWL_STYLE)

def WindowSetStyle(hwnd, style):
    return SetWindowLongA(hwnd, GWL_STYLE, style)

GetWindowLongPtrW = c.WINFUNCTYPE(
    w.HANDLE,
    w.HWND, c.c_int,
)(("GetWindowLongPtrW", c.windll.user32))

GWL_HWNDPARENT = -8
def WindowIsChild(hwnd):
    return IsWindow(GetWindowLongPtrW(hwnd, GWL_HWNDPARENT))

DwmGetWindowAttribute = c.WINFUNCTYPE(
    None,
    w.HWND, w.DWORD, c.c_void_p, w.DWORD,
)(("DwmGetWindowAttribute", c.windll.dwmapi))

DWMWA_CLOAKED = 14
def WindowIsCloaked(hwnd):
    output = (c.c_uint * 1)()
    DwmGetWindowAttribute(hwnd, DWMWA_CLOAKED, output, 4)
    return output[0] != 0

GetWindowRect = c.WINFUNCTYPE(
    w.BOOL,
    w.HWND, c.POINTER(w.RECT),
)(("GetWindowRect", c.windll.user32))

AdjustWindowRectEx = c.WINFUNCTYPE(
    w.BOOL,
    c.POINTER(w.RECT), c.c_uint, c.c_bool, c.c_uint,
)(("AdjustWindowRectEx", c.windll.user32))

SetWindowPos = c.WINFUNCTYPE(
    w.BOOL,

    w.HWND, # Window Handle
    w.HWND, # Insert after Window
    c.c_int, # X
    c.c_int, # Y
    c.c_int, # cx
    c.c_int, # cy
    w.UINT, # uFlags
)(("SetWindowPos", c.windll.user32))

HWND_BOTTOM = 1
HWND_TOP = 0
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2

SW_SHOW = 5
SW_SHOWNOACTIVATE = 4
SW_FORCEMINIMIZE = 11
SW_RESTORE = 9
SW_HIDE = 0

SWP_NOACTIVATE = 0x0010
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001

GetForegroundWindow = c.WINFUNCTYPE(
    w.HWND,
)(("GetForegroundWindow", c.windll.user32))

SetForegroundWindow = c.WINFUNCTYPE(
    w.BOOL,
    w.HWND,
)(("SetForegroundWindow", c.windll.user32))

SetCursorPos = c.WINFUNCTYPE(
    w.BOOL,
    c.c_int, c.c_int,
)(("SetCursorPos", c.windll.user32))

GetCursorPos = c.WINFUNCTYPE(
    w.BOOL,
    w.LPPOINT,
)(("GetCursorPos", c.windll.user32))

GetShellWindow = c.WINFUNCTYPE(
    w.HWND,
)(("GetShellWindow", c.windll.user32))

IsHungAppWindow = c.WINFUNCTYPE(
    w.BOOL,
    w.HWND,
)(("IsHungAppWindow", c.windll.user32))

ShowWindowAsync = c.WINFUNCTYPE(
    w.BOOL,
    w.HWND, c.c_int,
)(("ShowWindowAsync", c.windll.user32))

WM_CLOSE = 0x0010

PostMessageW = c.WINFUNCTYPE(
    w.BOOL,

    w.HWND, # Window Handle
    w.UINT, # Message Type
    w.WPARAM, # wParam
    w.LPARAM, # lParam
)(("PostMessageW", c.windll.user32))

MessageBoxW = c.WINFUNCTYPE(
    c.c_int,

    w.HWND, # Parent Window Handle
    w.LPCWSTR, # Text
    w.LPCWSTR, # Caption
    w.UINT, # uType
)(("MessageBoxW", c.windll.user32))

def ShowMessageBox(title, content):
    MessageBoxW(None, content, title, 0)

GetAsyncKeyState = c.WINFUNCTYPE(
    w.SHORT,
    c.c_int,
)(("GetAsyncKeyState", c.windll.user32))