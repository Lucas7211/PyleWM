import pylewm.commands
from pylewm.rects import Rect

import win32gui
import win32api
import win32con
import ctypes
import time

import threading

def is_window_handle_cloaked(hwnd):
    output = (ctypes.c_uint * 1)()
    result = ctypes.windll.dwmapi.DwmGetWindowAttribute(
        hwnd,
        ctypes.c_uint(14),
        output, 4)
    return output[0] != 0

def is_window_handle_minimized(hwnd):
    try:
        style = win32api.GetWindowLong(hwnd, win32con.GWL_STYLE)
        return style & win32con.WS_MINIMIZE
    except:
        return False

class Window:
    def __init__(self, hwnd):
        self.handle = hwnd
        self.last_window_pos = win32gui.GetWindowRect(self.handle)
        self.rect = Rect(self.last_window_pos)
        self.window_class = win32gui.GetClassName(hwnd)
        self.window_title = win32gui.GetWindowText(hwnd)
        self.space = None
        self.closed = False
        self.focused = False
        self.hidden = False

    def show(self):
        self.hidden = False
        def show_cmd():
            if win32gui.IsIconic(self.handle):
                win32gui.ShowWindow(self.handle, win32con.SW_RESTORE)
                self.set_layer_top()
            self.last_window_pos = self.get_actual_rect()
        self.command_queue.queue_command(show_cmd)

    def hide(self):
        self.hidden = True
        def hide_cmd():
            time.sleep(0.05)
            if not win32gui.IsIconic(self.handle):
                win32gui.ShowWindow(self.handle, win32con.SW_MINIMIZE)
        self.command_queue.queue_command(hide_cmd)

    def manage(self):
        self.command_queue = pylewm.commands.CommandQueue()
        if self.is_maximized():
            self.remove_maximize()
            self.last_window_pos = win32gui.GetWindowRect(self.handle)
        self.set_layer_bottom()

    def trigger_update(self):
        self.command_queue.queue_command(self.update)

    def stop_managing(self):
        self.command_queue.stop()

    def is_cloaked(self):
        return is_window_handle_cloaked(self.handle)

    def is_maximized(self):
        try:
            style = win32api.GetWindowLong(self.handle, win32con.GWL_STYLE)
            return style & win32con.WS_MAXIMIZE
        except:
            self.closed = True
            return False

    def remove_maximize(self):
        win32gui.ShowWindow(self.handle, win32con.SW_SHOWNOACTIVATE)

    def get_actual_rect(self):
        try:
            return win32gui.GetWindowRect(self.handle)
        except:
            self.closed = True
            return self.rect.coordinates

    def update(self):
        if self.hidden:
            return
        if self.closed:
            return
        if not win32gui.IsWindow(self.handle) or self.is_cloaked():
            self.closed = True
            return

        new_rect = self.get_actual_rect()

        # If the window has been moved outside of PyleWM we 'unsnap' it from the layout
        #  This is the same operation as 'closing' it since we are no longer managing it
        if new_rect != self.last_window_pos or self.is_maximized():
            self.set_layer_alwaystop()
            self.closed = True
            return

        # Move the window to the wanted rect if it has changed
        if not self.rect.equal_coordinates(new_rect):
            try:
                #print(f"move {self.window_title} {new_rect} -> {self.rect}")
                win32gui.SetWindowPos(self.handle, win32con.HWND_BOTTOM,
                    self.rect.left, self.rect.top,
                    self.rect.width, self.rect.height,
                    win32con.SWP_NOACTIVATE)
            except:
                pass

            self.last_window_pos = self.get_actual_rect()

    def set_layer_top(self):
        try:
            win32gui.SetWindowPos(self.handle, win32con.HWND_TOP, 0, 0, 0, 0,
                    win32con.SWP_NOACTIVATE | win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        except:
            pass

    def set_layer_bottom(self):
        try:
            win32gui.SetWindowPos(self.handle, win32con.HWND_BOTTOM, 0, 0, 0, 0,
                    win32con.SWP_NOACTIVATE | win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        except:
            pass

    def set_layer_alwaystop(self):
        try:
            win32gui.SetWindowPos(self.handle, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                    win32con.SWP_NOACTIVATE | win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        except:
            pass