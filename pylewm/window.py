import pylewm.commands
import pylewm.focus
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

def minimize_window_handle(hwnd):
    ctypes.windll.user32.ShowWindowAsync(hwnd, win32con.SW_FORCEMINIMIZE)

def is_left_mouse_held():
    return win32api.GetAsyncKeyState(win32con.VK_LBUTTON) != 0

class Window:
    def __init__(self, hwnd):
        self.handle = hwnd
        self.last_window_pos = win32gui.GetWindowRect(self.handle)
        self.last_received_pos = self.last_window_pos
        self.rect = Rect(self.last_window_pos)
        self.floating_rect = self.rect.copy()
        self.last_set_rect = self.rect.copy()
        self.window_class = win32gui.GetClassName(hwnd)
        self.window_title = win32gui.GetWindowText(hwnd)
        self.space = None
        self.closed = False
        self.focused = False
        self.hidden = False
        self.becoming_visible = False
        self.floating = False
        self.can_tile = True
        self.take_new_rect = False
        self.force_closed = False
        self.always_top = False
        self.force_always_top = False
        self.force_borders = None
        self.minimized = False
        self.is_dropdown = False

        parent_handle = win32api.GetWindowLong(self.handle, win32con.GWL_HWNDPARENT)
        self.is_child_window = win32gui.IsWindow(parent_handle)

        self.dragging = False
        self.drag_ticks_with_movement = 0
        self.drag_ticks_since_start = 0
        self.drag_ticks_since_last_movement = 0

        self.drop_space = None
        self.drop_slot = None
        self.drop_ticks_inside_slot = 0

    def reset(self):
        print("Close due to reset: "+self.window_title)
        self.closed = True
        if self.hidden:
            self.hidden = False
            self.becoming_visible = True
            ctypes.windll.user32.ShowWindowAsync(self.handle, win32con.SW_SHOWNOACTIVATE)
        if self.always_top:
            self.set_always_top(False)

    def show(self):
        def show_cmd():
            if not self.hidden:
                return
            self.hidden = False
            self.becoming_visible = True
            ctypes.windll.user32.ShowWindowAsync(self.handle, win32con.SW_SHOWNOACTIVATE)
            self.bring_to_front()

            #if win32gui.IsIconic(self.handle):
                #win32gui.ShowWindow(self.handle, win32con.SW_RESTORE)
            #self.last_window_pos = self.get_actual_rect()
        self.command_queue.queue_command(show_cmd)

    def SetWindowPos(self, hwnd, insert_hwnd, pos_x, pos_y, pos_cx, pos_cy, flags):
        result = ctypes.windll.user32.SetWindowPos(
            hwnd, insert_hwnd,
            pos_x, pos_y,
            pos_cx, pos_cy,
            flags
        )
        return (result != 0)

    def show_with_rect(self, new_rect):
        self.rect = new_rect
        def show_with_rect_cmd():
            if not self.hidden:
                return
            self.hidden = False
            self.becoming_visible = True

            try_position = [
                self.rect.left,
                self.rect.top,
                self.rect.width,
                self.rect.height,
            ]
            self.SetWindowPos(self.handle, win32con.HWND_TOPMOST,
                try_position[0], try_position[1],
                try_position[2], try_position[3],
                win32con.SWP_SHOWWINDOW)

            ctypes.windll.user32.ShowWindowAsync(self.handle, win32con.SW_SHOW)

        self.command_queue.queue_command(show_with_rect_cmd)

    def hide(self):
        def hide_cmd():
            if self.hidden:
                return
            self.hidden = True
            self.becoming_visible = False
            time.sleep(0.05)
            ctypes.windll.user32.ShowWindowAsync(self.handle, win32con.SW_HIDE)

            #if not win32gui.IsIconic(self.handle):
                #win32gui.ShowWindow(self.handle, win32con.SW_FORCEMINIMIZE)
        self.command_queue.queue_command(hide_cmd)

    def minimize(self):
        def minimize_cmd():
            minimize_window_handle(self.handle)

        self.minimized = True
        self.floating = True
        self.dragging = False
        self.command_queue.queue_command(minimize_cmd)

    def remove_titlebar(self):
        def remove_titlebar_cmd():
            style = win32api.GetWindowLong(self.handle, win32con.GWL_STYLE)
            if style & win32con.WS_CAPTION:
                style = style & ~win32con.WS_CAPTION
                win32api.SetWindowLong(self.handle, win32con.GWL_STYLE, style)
        self.command_queue.queue_command(remove_titlebar_cmd)

    def manage(self):
        self.command_queue = pylewm.commands.CommandQueue()
        def manage_window_cmd():
            if self.is_maximized():
                self.remove_maximize()
                self.last_window_pos = win32gui.GetWindowRect(self.handle)
            if self.floating:
                self.set_always_top(True)
            elif self.force_always_top:
                self.set_always_top(True)
            else:
                self.bring_to_front()
        self.command_queue.queue_command(manage_window_cmd)

    def trigger_update(self):
        self.command_queue.queue_command(self.update)

    def stop_managing(self):
        self.command_queue.stop()
        self.remove_drop_space()

    def is_cloaked(self):
        return is_window_handle_cloaked(self.handle)

    def is_maximized(self):
        try:
            style = win32api.GetWindowLong(self.handle, win32con.GWL_STYLE)
            return style & win32con.WS_MAXIMIZE
        except:
            return False

    def is_minimized(self):
        try:
            style = win32api.GetWindowLong(self.handle, win32con.GWL_STYLE)
            return style & win32con.WS_MINIMIZE
        except:
            return False

    def is_window_hidden(self):
        try:
            return not win32gui.IsWindowVisible(self.handle)
        except:
            return False

    def remove_maximize(self):
        win32gui.ShowWindow(self.handle, win32con.SW_SHOWNOACTIVATE)

    def get_actual_rect(self):
        try:
            return win32gui.GetWindowRect(self.handle)
        except:
            return self.rect.coordinates

    def can_move(self):
        if ctypes.windll.user32.IsHungAppWindow(self.handle):
            return False
        return True

    def update_drag(self):
        new_rect = self.get_actual_rect()
        if self.take_new_rect:
            self.last_window_pos = new_rect
            self.take_new_rect = False
            self.dragging = False
            self.remove_drop_space()

        # Some rudimentary tracking for when windows are being dragged
        if new_rect != self.last_window_pos:
            if is_left_mouse_held():
                if self.dragging:
                    self.drag_ticks_since_last_movement = 0
                    self.drag_ticks_since_start += 1
                    self.drag_ticks_with_movement += 1
                else:
                    self.dragging = True
                    self.drag_ticks_since_last_movement = 0
                    self.drag_ticks_since_start = 1
                    self.drag_ticks_with_movement = 1
        else:
            if self.dragging:
                self.drag_ticks_since_start += 1
                self.drag_ticks_since_last_movement += 1

                if not is_left_mouse_held():
                    self.dragging = False

        self.last_window_pos = new_rect
        if self.floating:
            self.rect.coordinates = new_rect
            self.floating_rect.coordinates = new_rect

    def update_float_drop(self):
        if not self.can_tile:
            return
        if self.dragging and self.drag_ticks_with_movement > 5:
            hover_space = pylewm.focus.get_cursor_space()
            hover_slot = None
            if hover_space:
                hover_slot, force_drop = hover_space.get_drop_slot(pylewm.focus.get_cursor_position(), self.rect)

                # Only allow forced drops when drag&dropping
                if not force_drop:
                    hover_slot = None
            
            if hover_slot is not None:
                self.set_drop_space(hover_space, hover_slot)
            else:
                self.remove_drop_space()
        elif not self.dragging and self.drop_space and self.drop_slot is not None and self.drop_ticks_inside_slot >= 3:
            self.floating = False
            self.take_new_rect = True
            self.drop_space.add_window(self, at_slot=self.drop_slot)
            self.remove_drop_space()
        else:
            self.remove_drop_space()

    def set_drop_space(self, new_space, new_slot):
        if self.drop_space == new_space and self.drop_slot == new_slot:
            if self.drop_ticks_inside_slot == 2:
                self.drop_space.set_pending_drop_slot(self.drop_slot)
            self.drop_ticks_inside_slot += 1
        else:
            if self.drop_space:
                self.drop_space.set_pending_drop_slot(None)
            self.drop_space = new_space
            self.drop_slot = new_slot
            self.drop_ticks_inside_slot = 0

    def remove_drop_space(self):
        if self.drop_space:
            self.drop_space.set_pending_drop_slot(None)
        self.drop_ticks_inside_slot = 0
        self.drop_space = None
        self.drop_slot = None

    def update(self):
        if self.hidden:
            return
        if self.closed:
            return
        if not win32gui.IsWindow(self.handle):
            print("Close due to not handle: "+self.window_title)
            self.closed = True
            return
        if self.is_cloaked():
            print("Close due to cloaked: "+self.window_title)
            self.closed = True
            return
        if self.is_minimized() or (self.is_window_hidden() and not self.becoming_visible):
            # Manually minimized windows are considered closed
            if not self.minimized:
                print("Close due to minimize: "+self.window_title)
                self.minimized = True
                self.floating = True
                self.dragging = False
                return
        else:
            if not self.is_window_hidden():
                self.becoming_visible = False
            if self.minimized:
                print("Reopen from minimize: "+self.window_title)
                self.minimized = False
                if not self.can_tile:
                    return
                hover_space = pylewm.focus.get_cursor_space()
                if hover_space:
                    hover_slot, force_drop = hover_space.get_drop_slot(self.rect.center, self.rect)
                    if hover_slot and not self.take_new_rect:
                        hover_space.add_window(self, at_slot=hover_slot)
                    else:
                        hover_space.add_window(self)
                    self.floating = False
                else:
                    self.floating = True
                self.take_new_rect = True
        if self.minimized:
            return
        if self.floating:
            self.update_drag()
            if self.dragging or self.drop_space:
                self.update_float_drop()
            return

        self.update_drag()

        # Move back to the bottom if we managed to get always on top
        if self.always_top and not self.force_always_top:
            self.set_always_top(False)

        # If the window has been moved outside of PyleWM we 'unsnap' it from the layout
        #  This is the same operation as 'closing' it since we are no longer managing it
        if self.is_maximized() or (self.dragging and (self.drag_ticks_with_movement > 2 or is_left_mouse_held())):
            self.set_always_top(True)
            self.floating = True
            self.dragging = False
            return

        # Move the window to the wanted rect if it has changed
        if not self.dragging and self.space and (
                not Rect.equal_coordinates(self.last_window_pos, self.last_received_pos)
                or not self.rect.equals(self.last_set_rect)):

            new_rect = self.rect.copy()
            try_position = [
                self.rect.left,
                self.rect.top,
                self.rect.width,
                self.rect.height,
            ]
            self.adjust_position_for_window(try_position)

            set_position_allowed = True
            needed_tries = 0
            for tries in range(0, 10):
                set_position_allowed = self.SetWindowPos(self.handle, win32con.HWND_BOTTOM,
                    try_position[0], try_position[1],
                    try_position[2], try_position[3],
                    win32con.SWP_NOACTIVATE)
                if not set_position_allowed:
                    break

                self.last_window_pos = self.get_actual_rect()

                if (try_position[0] != self.last_window_pos[0]
                    or try_position[1] != self.last_window_pos[1]
                    or try_position[2] != (self.last_window_pos[2] - self.last_window_pos[0])
                    or try_position[3] != (self.last_window_pos[3] - self.last_window_pos[1])
                ):
                    # Keep trying!
                    continue
                else:
                    needed_tries = tries+1
                    break

            if set_position_allowed:
                self.last_set_rect.assign(new_rect)
                self.last_window_pos = self.get_actual_rect()
                self.last_received_pos = self.last_window_pos

                print(f"Received {self.last_received_pos} for {self.window_title} which wants {new_rect} after {needed_tries} tries")
            else:
                print(f"Failed to set {new_rect} on {self.window_title}")

    def adjust_position_for_window(self, position):
        if self.force_borders is not None:
            if self.force_borders == 0:
                return
            else:
                position[0] += self.force_borders
                position[1] += self.force_borders
                position[2] -= self.force_borders*2
                position[3] -= self.force_borders*2
                return

        style = win32api.GetWindowLong(self.handle, win32con.GWL_STYLE)

        if not (style & win32con.WS_SYSMENU):
            position[0] += 2
            position[2] -= 4
            position[3] -= 3
            return

        exStyle = win32api.GetWindowLong(self.handle, win32con.GWL_EXSTYLE)

        adjusted = ctypes.wintypes.RECT()
        adjusted.left = position[0]
        adjusted.top = position[1]
        adjusted.right = position[0] + position[2]
        adjusted.bottom = position[1] + position[3]

        ctypes.windll.user32.AdjustWindowRectEx(
            ctypes.pointer(adjusted),
            ctypes.c_uint(style),
            False,
            ctypes.c_uint(exStyle),
        )

        position[0] = adjusted.left + 3
        position[1] += 2
        position[2] = adjusted.right - adjusted.left - 6
        position[3] = adjusted.bottom - position[1] - 3

    def make_floating(self):
        space = self.space
        if space:
            space.remove_window(self)

        self.floating = True
        self.can_tile = False

        def float_cmd():
            # Floating windows are always on top of everything
            self.set_always_top(True)

            # Return window to the position it had before
            try_position = [
                self.floating_rect.left,
                self.floating_rect.top,
                self.floating_rect.width,
                self.floating_rect.height,
            ]

            self.SetWindowPos(self.handle, win32con.HWND_TOPMOST,
                    try_position[0], try_position[1],
                    try_position[2], try_position[3],
                    win32con.SWP_NOACTIVATE)

        self.command_queue.queue_command(float_cmd)

    def poke(self):
        def poke_cmd():
            self.SetWindowPos(self.handle, win32con.HWND_BOTTOM,
                self.rect.left+2, self.rect.top+2,
                self.rect.width-4, self.rect.height-4,
                win32con.SWP_NOACTIVATE)
            self.SetWindowPos(self.handle, win32con.HWND_BOTTOM,
                self.rect.left, self.rect.top,
                self.rect.width, self.rect.height,
                win32con.SWP_NOACTIVATE)
        self.command_queue.queue_command(poke_cmd)

    def bring_to_front(self):
        if self.force_always_top:
            return

        self.SetWindowPos(self.handle, win32con.HWND_TOP, 0, 0, 0, 0,
                win32con.SWP_NOACTIVATE | win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)

    def send_to_bottom(self):
        if self.force_always_top:
            return
        self.SetWindowPos(self.handle, win32con.HWND_BOTTOM, 0, 0, 0, 0,
                win32con.SWP_NOACTIVATE | win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)

    def set_always_top(self, always_top):
        self.always_top = always_top
        try:
            if always_top:
                self.SetWindowPos(self.handle, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                        win32con.SWP_NOACTIVATE | win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            else:
                self.SetWindowPos(self.handle, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                        win32con.SWP_NOACTIVATE | win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        except:
            pass