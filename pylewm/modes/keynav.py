import pylewm
import pylewm.modes.overlay_mode
import win32api, win32con, win32gui
import time
from pylewm.rects import Rect

class KeyNavMode(pylewm.modes.overlay_mode.OverlayMode):
    def __init__(self, hotkeys):
        self.window = pylewm.focus.FocusWindow
        self.cover_area = self.window.real_position.padded(8, 8)

        self.rect = Rect((8, 8, self.cover_area.width, self.cover_area.height))
        self.overlay_window(self.window)

        self.line_color = (255, 0, 0)
        self.line_width = 3

        self.target_color = (0, 255, 255)
        self.target_width = 6

        self.rect_history = []
        self.update_rect()

        super(KeyNavMode, self).__init__(hotkeys)

    def split_left(self):
        self.rect = Rect((
            self.rect.left,
            self.rect.top,
            self.rect.left + self.rect.width / 2,
            self.rect.bottom,
        ))
        self.update_rect()

    def split_right(self):
        self.rect = Rect((
            self.rect.left + self.rect.width / 2,
            self.rect.top,
            self.rect.right,
            self.rect.bottom,
        ))
        self.update_rect()

    def split_up(self):
        self.rect = Rect((
            self.rect.left,
            self.rect.top,
            self.rect.right,
            self.rect.top + self.rect.height / 2,
        ))
        self.update_rect()

    def split_down(self):
        self.rect = Rect((
            self.rect.left,
            self.rect.top + self.rect.height / 2,
            self.rect.right,
            self.rect.bottom,
        ))
        self.update_rect()

    def shift(self, x, y):
        w, h = self.rect.width, self.rect.height
        left = min(max(0, self.rect.left + x), self.cover_area.width - w)
        top = min(max(0, self.rect.top + y), self.cover_area.height - h)

        self.rect = Rect((left, top, left+w, top+h))
        self.update_rect()

    def shift_left(self):
        self.shift(-self.rect.width, 0)

    def shift_right(self):
        self.shift(self.rect.width, 0)

    def shift_up(self):
        self.shift(0, -self.rect.height)

    def shift_down(self):
        self.shift(0, self.rect.height)

    def undo_move(self):
        if len(self.rect_history) < 2:
            return
        self.rect = self.rect_history[-2]
        self.rect_history = self.rect_history[:-2]
        self.update_rect()

    def left_click(self):
        position = win32gui.ScreenToClient(self.window.proxy._hwnd, win32api.GetCursorPos())
        pylewm.commands.delay_pyle_command(0.1, lambda: win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, position[0], position[1], 0, 0))
        pylewm.commands.delay_pyle_command(0.15, lambda: win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, position[0], position[1], 0, 0))

    def double_click(self):
        position = win32gui.ScreenToClient(self.window.proxy._hwnd, win32api.GetCursorPos())
        pylewm.commands.delay_pyle_command(0.1, lambda: win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, position[0], position[1], 0, 0))
        pylewm.commands.delay_pyle_command(0.15, lambda: win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, position[0], position[1], 0, 0))
        pylewm.commands.delay_pyle_command(0.2, lambda: win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, position[0], position[1], 0, 0))
        pylewm.commands.delay_pyle_command(0.25, lambda: win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, position[0], position[1], 0, 0))

    def right_click(self):
        position = win32gui.ScreenToClient(self.window.proxy._hwnd, win32api.GetCursorPos())
        pylewm.commands.delay_pyle_command(0.1, lambda: win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, position[0], position[1], 0, 0))
        pylewm.commands.delay_pyle_command(0.15, lambda: win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, position[0], position[1], 0, 0))

    def middle_click(self):
        position = win32gui.ScreenToClient(self.window.proxy._hwnd, win32api.GetCursorPos())
        pylewm.commands.delay_pyle_command(0.1, lambda: win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEDOWN, position[0], position[1], 0, 0))
        pylewm.commands.delay_pyle_command(0.15, lambda: win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEUP, position[0], position[1], 0, 0))

    def update_rect(self):
        try:
            win32api.SetCursorPos((
                int(self.cover_area.left + self.rect.left + self.rect.width / 2),
                int(self.cover_area.top + self.rect.top + self.rect.height / 2),
            ))
        except:
            pass # Not allowed, probably an administrator window has focus or something

        self.rect_history.append(self.rect)

    def draw(self, overlay):
        overlay.draw_border(Rect((
            self.rect.left, self.rect.top,
            self.rect.left + self.rect.width / 2, self.rect.top + self.rect.height / 2
        )), self.line_color, self.line_width)
        overlay.draw_border(Rect((
            self.rect.left + self.rect.width / 2, self.rect.top,
            self.rect.right, self.rect.top + self.rect.height / 2
        )), self.line_color, self.line_width)
        overlay.draw_border(Rect((
            self.rect.left, self.rect.top + self.rect.height / 2,
            self.rect.left + self.rect.width / 2, self.rect.bottom
        )), self.line_color, self.line_width)
        overlay.draw_border(Rect((
            self.rect.left + self.rect.width / 2, self.rect.top + self.rect.height / 2,
            self.rect.right, self.rect.bottom
        )), self.line_color, self.line_width)
        overlay.draw_box(Rect((
            self.rect.left + self.rect.width / 2 - self.target_width, self.rect.top + self.rect.height / 2 - self.target_width,
            self.rect.left + self.rect.width / 2 + self.target_width, self.rect.top + self.rect.height / 2 + self.target_width,
        )), self.target_color)


@pylewm.commands.PyleCommand
def split_left():
    with pylewm.hotkeys.ModeLock:
        pylewm.hotkeys.ModeStack[0].split_left()

@pylewm.commands.PyleCommand
def split_right():
    with pylewm.hotkeys.ModeLock:
        pylewm.hotkeys.ModeStack[0].split_right()

@pylewm.commands.PyleCommand
def split_up():
    with pylewm.hotkeys.ModeLock:
        pylewm.hotkeys.ModeStack[0].split_up()

@pylewm.commands.PyleCommand
def split_down():
    with pylewm.hotkeys.ModeLock:
        pylewm.hotkeys.ModeStack[0].split_down()

@pylewm.commands.PyleCommand
def shift_left():
    with pylewm.hotkeys.ModeLock:
        pylewm.hotkeys.ModeStack[0].shift_left()

@pylewm.commands.PyleCommand
def shift_right():
    with pylewm.hotkeys.ModeLock:
        pylewm.hotkeys.ModeStack[0].shift_right()

@pylewm.commands.PyleCommand
def shift_up():
    with pylewm.hotkeys.ModeLock:
        pylewm.hotkeys.ModeStack[0].shift_up()

@pylewm.commands.PyleCommand
def shift_down():
    with pylewm.hotkeys.ModeLock:
        pylewm.hotkeys.ModeStack[0].shift_down()

@pylewm.commands.PyleCommand
def undo_move():
    with pylewm.hotkeys.ModeLock:
        pylewm.hotkeys.ModeStack[0].undo_move()

@pylewm.commands.PyleCommand
def left_click():
    with pylewm.hotkeys.ModeLock:
        pylewm.hotkeys.ModeStack[0].left_click()
    pylewm.hotkeys.queue_command(pylewm.hotkeys.escape_mode)

@pylewm.commands.PyleCommand
def double_click():
    with pylewm.hotkeys.ModeLock:
        pylewm.hotkeys.ModeStack[0].double_click()
    pylewm.hotkeys.queue_command(pylewm.hotkeys.escape_mode)

@pylewm.commands.PyleCommand
def right_click():
    with pylewm.hotkeys.ModeLock:
        pylewm.hotkeys.ModeStack[0].right_click()
    pylewm.hotkeys.queue_command(pylewm.hotkeys.escape_mode)

@pylewm.commands.PyleCommand
def middle_click():
    with pylewm.hotkeys.ModeLock:
        pylewm.hotkeys.ModeStack[0].middle_click()
    pylewm.hotkeys.queue_command(pylewm.hotkeys.escape_mode)

@pylewm.commands.PyleCommand
def start_keynav(hotkeys):
    if not pylewm.focus.FocusWindow:
        return
    KeyNavMode(hotkeys)()