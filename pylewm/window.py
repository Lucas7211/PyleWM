import pylewm.commands
from pylewm.rects import Rect

import win32gui
import win32api
import win32con

import threading

class Window:
    def __init__(self, hwnd):
        self.handle = hwnd
        self.last_window_pos = win32gui.GetWindowRect(self.handle)
        self.rect = Rect(self.last_window_pos)
        self.window_class = win32gui.GetClassName(hwnd)
        self.window_title = win32gui.GetWindowText(hwnd)
        self.space = None
        self.closed = False

    def manage(self):
        self.command_queue = pylewm.commands.CommandQueue()

    def trigger_update(self):
        self.command_queue.queue_command(self.update)

    def update(self):
        if self.closed:
            return
        if not win32gui.IsWindow(self.handle):
            self.closed = True
            return

        new_rect = win32gui.GetWindowRect(self.handle)
        
        # TODO: Detect detachment from layout by moving

        # Move the window to the wanted rect if it has changed
        if self.rect.coordinates != new_rect:
            win32gui.SetWindowPos(self.handle, win32con.HWND_TOP,
                self.rect.left, self.rect.top,
                self.rect.width, self.rect.height,
                win32con.SWP_NOACTIVATE)

            self.last_window_pos = win32gui.GetWindowRect(self.handle)