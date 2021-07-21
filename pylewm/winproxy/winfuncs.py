import ctypes as c
import ctypes.wintypes as w

tEnumWindowFunc = c.CFUNCTYPE(None, w.HWND, w.LPARAM)

def no_errcheck(result, func, args):
    return result

EnumWindows = c.windll.user32.EnumWindows
EnumWindows.errcheck = no_errcheck
EnumWindows.argtypes = (
    tEnumWindowFunc,
    w.LPARAM,
)

GetWindowTextW = c.windll.user32.GetWindowTextW
GetWindowTextW.errcheck = no_errcheck
GetWindowTextW.restype = c.c_int
GetWindowTextW.argtypes = (
    w.HWND, # Window handle
    w.LPWSTR, # Output String buffer
    c.c_int, # Output buffer length
)

def WindowGetTitle(hwnd):
    buffer = c.create_unicode_buffer(256)
    GetWindowTextW(hwnd, buffer, c.sizeof(buffer))
    return buffer.value

GetClassNameW = c.windll.user32.GetClassNameW
GetClassNameW.errcheck = no_errcheck
GetClassNameW.restype = c.c_int
GetClassNameW.argtypes = (
    w.HWND, # Window handle
    w.LPWSTR, # Output String buffer
    c.c_int, # Output buffer length
)

IsWindow = c.windll.user32.IsWindow
IsWindow.errcheck = no_errcheck
IsWindow.restype = c.c_bool
IsWindow.argtypes = (w.HWND,)

IsWindowVisible = c.windll.user32.IsWindowVisible
IsWindowVisible.errcheck = no_errcheck
IsWindowVisible.restype = c.c_bool
IsWindowVisible.argtypes = (w.HWND,)

def WindowGetClass(hwnd):
    buffer = c.create_unicode_buffer(256)
    GetClassNameW(hwnd, buffer, c.sizeof(buffer))
    return buffer.value

GetWindowLongA = c.windll.user32.GetWindowLongA
GetWindowLongA.errcheck = no_errcheck
GetWindowLongA.restype = w.LONG
GetWindowLongA.argtypes = (w.HWND, c.c_int)

GWL_EXSTYLE = -20
def WindowGetExStyle(hwnd):
    return GetWindowLongA(hwnd, GWL_EXSTYLE)

GWL_STYLE = -16
def WindowGetStyle(hwnd):
    return GetWindowLongA(hwnd, GWL_STYLE)

GetWindowLongPtrW = c.windll.user32.GetWindowLongPtrW
GetWindowLongPtrW.errcheck = no_errcheck
GetWindowLongPtrW.restype = w.HANDLE
GetWindowLongPtrW.argtypes = (w.HWND, c.c_int)

GWL_HWNDPARENT = -8
def WindowIsChild(hwnd):
    return IsWindow(GetWindowLongPtrW(hwnd, GWL_HWNDPARENT))

DwmGetWindowAttribute = c.windll.dwmapi.DwmGetWindowAttribute
DwmGetWindowAttribute.errcheck = no_errcheck
DwmGetWindowAttribute.argtypes = (
    w.HWND, # Window Handle
    w.DWORD, # Attribute ID
    c.c_void_p, # Buffer pointer
    w.DWORD, # Buffer size (bytes)
)

DWMWA_CLOAKED = 14
def WindowIsCloaked(hwnd):
    output = (c.c_uint * 1)()
    DwmGetWindowAttribute(hwnd, DWMWA_CLOAKED, output, 4)
    return output[0] != 0

GetWindowRect = c.windll.user32.GetWindowRect
GetWindowRect.errcheck = no_errcheck
GetWindowRect.restype = c.c_bool
GetWindowRect.argtypes = (w.HWND, c.POINTER(w.RECT))

AdjustWindowRectEx = c.windll.user32.AdjustWindowRectEx
AdjustWindowRectEx.errcheck = no_errcheck
AdjustWindowRectEx.argtypes = (
    c.POINTER(w.RECT),
    c.c_uint,
    c.c_bool,
    c.c_uint,
)

SetWindowPos = c.windll.user32.SetWindowPos
SetWindowPos.errcheck = no_errcheck
SetWindowPos.restype = w.BOOL
SetWindowPos.argtypes = (
    w.HWND, # Window Handle
    w.HWND, # Insert after Window
    c.c_int, # X
    c.c_int, # Y
    c.c_int, # cx
    c.c_int, # cy
    w.UINT, # uFlags
)

HWND_BOTTOM = 1
HWND_TOP = 0
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2

SW_SHOW = 5
SW_SHOWNOACTIVATE = 4
SW_HIDE = 0

SWP_NOACTIVATE = 0x0010
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001

def WindowSetPositionInLayout(hwnd, pos_x, pos_y, pos_cx, pos_cy):
    return SetWindowPos(
        hwnd,
        HWND_BOTTOM,
        pos_x, pos_y,
        pos_cx, pos_cy,
        SWP_NOACTIVATE,
    )

GetForegroundWindow = c.windll.user32.GetForegroundWindow
GetForegroundWindow.errcheck = no_errcheck
GetForegroundWindow.restype = w.HWND
GetForegroundWindow.argtypes = ()

SetForegroundWindow = c.windll.user32.SetForegroundWindow
SetForegroundWindow.errcheck = no_errcheck
SetForegroundWindow.restype = w.BOOL
SetForegroundWindow.argtypes = (w.HWND,)

SetCursorPos = c.windll.user32.SetCursorPos
SetCursorPos.errcheck = no_errcheck
SetCursorPos.restype = w.BOOL
SetCursorPos.argtypes = (c.c_int, c.c_int)

GetCursorPos = c.windll.user32.GetCursorPos
GetCursorPos.errcheck = no_errcheck
GetCursorPos.restype = w.BOOL
GetCursorPos.argtypes = (w.LPPOINT,)

GetShellWindow = c.windll.user32.GetShellWindow
GetShellWindow.errcheck = no_errcheck
GetShellWindow.restype = w.HWND
GetShellWindow.argtypes = ()

IsHungAppWindow = c.windll.user32.IsHungAppWindow
IsHungAppWindow.errcheck = no_errcheck
IsHungAppWindow.restype = w.BOOL
IsHungAppWindow.argtypes = (w.HWND,)

ShowWindowAsync = c.windll.user32.ShowWindowAsync
ShowWindowAsync.errcheck = no_errcheck
ShowWindowAsync.restype = w.BOOL
ShowWindowAsync.argtypes = (w.HWND, c.c_int)