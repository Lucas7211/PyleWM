import ctypes as c
import ctypes.wintypes as w

tEnumWindowFunc = c.CFUNCTYPE(None, w.HWND, w.LPARAM)

EnumWindows = c.windll.user32.EnumWindows
EnumWindows.argtypes = (
    tEnumWindowFunc,
    w.LPARAM,
)

GetWindowTextW = c.windll.user32.GetWindowTextW
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
GetClassNameW.restype = c.c_int
GetClassNameW.argtypes = (
    w.HWND, # Window handle
    w.LPWSTR, # Output String buffer
    c.c_int, # Output buffer length
)

IsWindow = c.windll.user32.IsWindow
IsWindow.restype = c.c_bool
IsWindow.argtypes = (w.HWND,)

IsWindowVisible = c.windll.user32.IsWindowVisible
IsWindowVisible.restype = c.c_bool
IsWindowVisible.argtypes = (w.HWND,)

def WindowGetClass(hwnd):
    buffer = c.create_unicode_buffer(256)
    GetClassNameW(hwnd, buffer, c.sizeof(buffer))
    return buffer.value

GetWindowLongA = c.windll.user32.GetWindowLongA
GetWindowLongA.restype = w.LONG
GetWindowLongA.argtypes = (w.HWND, c.c_int)

GWL_EXSTYLE = -20
def WindowGetExStyle(hwnd):
    return GetWindowLongA(hwnd, GWL_EXSTYLE)

GWL_STYLE = -16
def WindowGetStyle(hwnd):
    return GetWindowLongA(hwnd, GWL_STYLE)

GetWindowLongPtrW = c.windll.user32.GetWindowLongPtrW
GetWindowLongPtrW.restype = w.HANDLE
GetWindowLongPtrW.argtypes = (w.HWND, c.c_int)

GWL_HWNDPARENT = -8
def WindowIsChild(hwnd):
    return IsWindow(GetWindowLongPtrW(hwnd, GWL_HWNDPARENT))

DwmGetWindowAttribute = c.windll.dwmapi.DwmGetWindowAttribute
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
GetWindowRect.restype = c.c_bool
GetWindowRect.argtypes = (w.HWND, c.POINTER(w.RECT))

AdjustWindowRectEx = c.windll.user32.AdjustWindowRectEx
AdjustWindowRectEx.argtypes = (
    c.POINTER(w.RECT),
    c.c_uint,
    c.c_bool,
    c.c_uint,
)

SetWindowPos = c.windll.user32.SetWindowPos
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
SWP_NOACTIVATE = 0x0010
def WindowSetPositionInLayout(hwnd, pos_x, pos_y, pos_cx, pos_cy):
    return SetWindowPos(
        hwnd,
        HWND_BOTTOM,
        pos_x, pos_y,
        pos_cx, pos_cy,
        SWP_NOACTIVATE,
    )

GetForegroundWindow = c.windll.user32.GetForegroundWindow
GetForegroundWindow.restype = w.HWND
GetForegroundWindow.argtypes = ()

SetForegroundWindow = c.windll.user32.SetForegroundWindow
SetForegroundWindow.restype = w.BOOL
SetForegroundWindow.argtypes = (w.HWND,)

SetCursorPos = c.windll.user32.SetCursorPos
SetCursorPos.restype = w.BOOL
SetCursorPos.argtypes = (c.c_int, c.c_int)

GetCursorPos = c.windll.user32.GetCursorPos
GetCursorPos.restype = w.BOOL
GetCursorPos.argtypes = (w.LPPOINT,)

GetShellWindow = c.windll.user32.GetShellWindow
GetShellWindow.restype = w.HWND
GetShellWindow.argtypes = ()

IsHungAppWindow = c.windll.user32.IsHungAppWindow
IsHungAppWindow.restype = w.BOOL
IsHungAppWindow.argtypes = (w.HWND,)