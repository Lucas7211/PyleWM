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
        self.last_set_rect = self.rect.copy()
        self.window_class = win32gui.GetClassName(hwnd)
        self.window_title = win32gui.GetWindowText(hwnd)
        self.space = None
        self.closed = False
        self.focused = False
        self.hidden = False
        self.floating = False
        self.can_tile = True
        self.take_new_rect = False
        self.force_closed = False
        self.always_top = False
        self.force_always_top = False
        self.ignore_borders = False

        parent_handle = win32api.GetWindowLong(self.handle, win32con.GWL_HWNDPARENT)
        self.is_child_window = win32gui.IsWindow(parent_handle)

        self.dragging = False
        self.drag_ticks_with_movement = 0
        self.drag_ticks_since_start = 0
        self.drag_ticks_since_last_movement = 0

        self.drop_space = None
        self.drop_slot = 0
        self.drop_ticks_inside_slot = 0

    def reset(self):
        self.closed = True
        if self.hidden:
            self.hidden = False
            ctypes.windll.user32.ShowWindowAsync(self.handle, win32con.SW_SHOWNOACTIVATE)
        if self.always_top:
            self.set_always_top(False)

    def show(self):
        def show_cmd():
            if not self.hidden:
                return
            self.hidden = False
            ctypes.windll.user32.ShowWindowAsync(self.handle, win32con.SW_SHOWNOACTIVATE)
            self.bring_to_front()

            #if win32gui.IsIconic(self.handle):
                #win32gui.ShowWindow(self.handle, win32con.SW_RESTORE)
            #self.last_window_pos = self.get_actual_rect()
        self.command_queue.queue_command(show_cmd)

    def hide(self):
        def hide_cmd():
            if self.hidden:
                return
            self.hidden = True
            time.sleep(0.05)
            ctypes.windll.user32.ShowWindowAsync(self.handle, win32con.SW_HIDE)

            #if not win32gui.IsIconic(self.handle):
                #win32gui.ShowWindow(self.handle, win32con.SW_FORCEMINIMIZE)
        self.command_queue.queue_command(hide_cmd)

    def minimize(self):
        def minimize_cmd():
            minimize_window_handle(self.handle)
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
        if self.is_maximized():
            self.remove_maximize()
            self.last_window_pos = win32gui.GetWindowRect(self.handle)
        if self.floating:
            self.set_always_top(True)
        elif self.force_always_top:
            self.set_always_top(True)
        else:
            self.bring_to_front()

    def trigger_update(self):
        self.command_queue.queue_command(self.update)

    def stop_managing(self):
        self.command_queue.stop()
        self.set_drop_space(None)

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
            self.set_drop_space(None)

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

    def update_float_drop(self):
        if not self.can_tile:
            return
        if self.dragging and self.drag_ticks_with_movement > 5:
            hover_space = pylewm.focus.get_cursor_space()
            if hover_space:
                hover_slot, force_drop = hover_space.get_drop_slot(pylewm.focus.get_cursor_position(), self.rect)

                # Only allow forced drops when drag&dropping
                if not force_drop:
                    hover_slot = None

            self.set_drop_space(hover_space)

            if hover_slot is None:
                self.drop_slot = None
                self.set_drop_space(None)
            elif hover_slot == self.drop_slot:
                self.drop_ticks_inside_slot += 1
                if self.drop_ticks_inside_slot > 3:
                    if self.drop_space:
                        self.drop_space.set_pending_drop_slot(hover_slot)
            else:
                self.drop_slot = hover_slot
                self.drop_ticks_inside_slot = 0

        elif not self.dragging and self.drop_space and self.drop_space.pending_drop_slot != -1:
            self.floating = False
            self.take_new_rect = True
            self.drop_space.add_window(self, at_slot=self.drop_slot)
            self.set_drop_space(None)
        else:
            self.set_drop_space(None)

    def set_drop_space(self, new_space):
        if self.drop_space == new_space:
            return
        if self.drop_space:
            self.drop_space.set_pending_drop_slot(None)
        self.drop_space = new_space
        self.drop_ticks_inside_slot = 0
        self.drop_slot = -1

    def update(self):
        if self.hidden:
            return
        if self.closed:
            return
        if not win32gui.IsWindow(self.handle) or self.is_cloaked():
            self.closed = True
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
        if self.is_maximized() or (self.dragging and self.drag_ticks_with_movement > 2):
            self.set_always_top(True)
            self.floating = True
            self.dragging = False
            return

        # Manually minimized windows are considered closed
        if self.is_minimized() or self.is_window_hidden():
            self.closed = True
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
                try:
                    win32gui.SetWindowPos(self.handle, win32con.HWND_BOTTOM,
                        try_position[0], try_position[1],
                        try_position[2], try_position[3],
                        win32con.SWP_NOACTIVATE)
                except:
                    set_position_allowed = False
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
        if self.ignore_borders:
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

    def poke(self):
        def poke_cmd():
            try:
                win32gui.SetWindowPos(self.handle, win32con.HWND_BOTTOM,
                    self.rect.left+2, self.rect.top+2,
                    self.rect.width-4, self.rect.height-4,
                    win32con.SWP_NOACTIVATE)
            except:
                pass
            try:
                win32gui.SetWindowPos(self.handle, win32con.HWND_BOTTOM,
                    self.rect.left, self.rect.top,
                    self.rect.width, self.rect.height,
                    win32con.SWP_NOACTIVATE)
            except:
                pass
        self.command_queue.queue_command(poke_cmd)

    def bring_to_front(self):
        if self.force_always_top:
            return

        try:
            win32gui.SetWindowPos(self.handle, win32con.HWND_TOP, 0, 0, 0, 0,
                    win32con.SWP_NOACTIVATE | win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        except:
            pass

    def send_to_bottom(self):
        if self.force_always_top:
            return

        try:
            win32gui.SetWindowPos(self.handle, win32con.HWND_BOTTOM, 0, 0, 0, 0,
                    win32con.SWP_NOACTIVATE | win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        except:
            pass

    def set_always_top(self, always_top):
        self.always_top = always_top
        try:
            if always_top:
                win32gui.SetWindowPos(self.handle, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                        win32con.SWP_NOACTIVATE | win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            else:
                win32gui.SetWindowPos(self.handle, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                        win32con.SWP_NOACTIVATE | win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        except:
            pass