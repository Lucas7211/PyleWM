import win32con
import time

import pylewm.window
import pylewm.focus
from pylewm.winproxy.winfocus import focus_window, focus_shell_window, get_cursor_position, determine_window_proxy_under_cursor

from pylewm.commands import PyleCommand
from pylewm.hotkeys import MouseState
from pylewm.window_update import WINDOW_UPDATE_FUNCS

class DragState:
    DRAG_ALLOWED = False
    DRAG_WINDOW : pylewm.window.Window = None
    DRAG_MOUSE_POS = None
    DRAG_WINDOW_POS = None
    DRAG_RESIZE_MODE = None
    DRAG_ACTIVATE_TIME = 0
    DRAG_START_TIME = 0

@PyleCommand
def activate_window_drag_resize():
    """
        While this key is down:
            Pressing left mouse on a window allows dragging it around.
            Pressing right mouse on a window allows resizing it.
    """

    if DragState.DRAG_ALLOWED:
        return

    DragState.DRAG_ALLOWED = True
    DragState.DRAG_ACTIVATE_TIME = time.time()
    MouseState.MOUSE_HOOKS.append(window_drag_hook)
    WINDOW_UPDATE_FUNCS.append(drag_update)

def window_drag_hook(wParam):
    if wParam == win32con.WM_LBUTTONDOWN or wParam == win32con.WM_RBUTTONDOWN:
        if not DragState.DRAG_WINDOW:
            DragState.DRAG_MOUSE_POS = get_cursor_position()
            window : pylewm.window.Window = None

            cursor_proxy = determine_window_proxy_under_cursor()
            if cursor_proxy:
                window = pylewm.window.get_window(cursor_proxy)
                if window:
                    if window.state == pylewm.window.WindowState.IgnorePermanent:
                        window = None
                    elif window.is_hung() or window.window_info.cloaked or window.closed:
                        window = None

            if not window:
                available_windows = pylewm.window.get_windows_at_position(DragState.DRAG_MOUSE_POS)
                if not available_windows:
                    return

                if len(available_windows) > 1 and pylewm.focus.FocusWindow in available_windows:
                    window = pylewm.focus.FocusWindow
                else:
                    window = available_windows[0]
            
            if not window.is_hung():
                DragState.DRAG_WINDOW = window
                DragState.DRAG_WINDOW_POS = DragState.DRAG_WINDOW.real_position.copy()
                DragState.DRAG_START_TIME = time.time()
                pylewm.winproxy.winfuncs.SetForegroundWindow(window.proxy._hwnd)

                if wParam == win32con.WM_RBUTTONDOWN:
                    pct_x = float(DragState.DRAG_MOUSE_POS[0] - window.real_position.left) / float(window.real_position.width)
                    pct_y = float(DragState.DRAG_MOUSE_POS[1] - window.real_position.top) / float(window.real_position.height)

                    mode_x = 0
                    if pct_x < 0.5:
                        mode_x = -1
                    else:
                        mode_x = 1

                    mode_y = 0
                    if pct_y < 0.5:
                        mode_y = -1
                    else:
                        mode_y = 1

                    DragState.DRAG_RESIZE_MODE = (mode_x, mode_y)
                else:
                    pylewm.commands.set_responsive_mode(True)
                    DragState.DRAG_RESIZE_MODE = None

        return True
    elif wParam == win32con.WM_LBUTTONUP or wParam == win32con.WM_RBUTTONUP:
        if DragState.DRAG_WINDOW:
            DragState.DRAG_WINDOW = None
            return True
    elif wParam == win32con.WM_MBUTTONDOWN or wParam == win32con.WM_MBUTTONUP:
        stop_window_drag_resize()
        return True

    return False

def drag_update():
    active_time = time.time() - DragState.DRAG_START_TIME

    window = DragState.DRAG_WINDOW
    if not window:
        return

    # Stop dragging if we no longer have focus on this window
    drag_time = time.time() - DragState.DRAG_START_TIME
    if drag_time > 1.0 and pylewm.focus.FocusWindow != window:
        DragState.DRAG_WINDOW = None
        return

    mouse_pos = get_cursor_position()
    if mouse_pos == DragState.DRAG_MOUSE_POS:
        return

    if window.is_tiled():
        window.make_floating()
    if window != pylewm.focus.FocusWindow:
        pylewm.focus.set_focus_no_mouse(window)

    delta = (mouse_pos[0] - DragState.DRAG_MOUSE_POS[0], mouse_pos[1] - DragState.DRAG_MOUSE_POS[1])
    DragState.DRAG_MOUSE_POS = mouse_pos

    pos = DragState.DRAG_WINDOW_POS.copy()
    if DragState.DRAG_RESIZE_MODE == None:
        pos = pos.shifted(delta)
    else:
        if DragState.DRAG_RESIZE_MODE[0] == -1:
            pos.left += delta[0]
        elif DragState.DRAG_RESIZE_MODE[0] == 1:
            pos.right += delta[0]

        if DragState.DRAG_RESIZE_MODE[1] == -1:
            pos.top += delta[1]
        elif DragState.DRAG_RESIZE_MODE[1] == 1:
            pos.bottom += delta[1]

    DragState.DRAG_WINDOW_POS = pos

    window.move_floating_to(pos)

def stop_window_drag_resize():
    if not DragState.DRAG_ALLOWED:
        return

    MouseState.MOUSE_HOOKS.remove(window_drag_hook)
    WINDOW_UPDATE_FUNCS.remove(drag_update)
    DragState.DRAG_ALLOWED = False
    DragState.DRAG_WINDOW = None
    pylewm.commands.set_responsive_mode(False)

activate_window_drag_resize.release_event = stop_window_drag_resize