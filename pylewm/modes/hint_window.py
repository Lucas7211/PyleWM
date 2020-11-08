import pylewm.modes.overlay_mode
import pylewm.modes.hint_helpers
import pylewm
from pylewm.rects import Rect
import win32gui, win32api, win32con

class WindowItem:
    pass

class HintWindowMode(pylewm.modes.overlay_mode.OverlayMode):
    def __init__(self, hintkeys, hotkeys):
        super(HintWindowMode, self).__init__(hotkeys)
        self.hintkeys = hintkeys
        self.item_list = []
        self.overlay_global()

        self.bg_color = (0,0,0)
        self.hint_color = (255,255,0)
        self.border_color = (0, 128, 255)
        self.title_color = (128,128,128)
        self.floating_border = (255,0,255)
        self.border_width = 1
        self.box_size = (200, 50)

        self.selection_text = ""
        self.max_hidden_row = 10
        self.closed = False
        self.dirty = True

        hidden_windows = {}
        for hwnd, window in pylewm.windows.Windows.items():
            if win32gui.IsWindow(hwnd):
                if window.space and not window.space.visible:
                    if window.space.monitor not in hidden_windows:
                        hidden_windows[window.space.monitor] = []
                    hidden_windows[window.space.monitor].append(window)
                    continue

                item = WindowItem()
                item.window = window
                item.rect = window.rect
                item.is_hidden = False
                self.item_list.append(item)

        for monitor, window_list in hidden_windows.items():
            show_count = len(window_list)
            item_width = monitor.rect.width / min(self.max_hidden_row, show_count)
            for i in range(0, show_count):
                window = window_list[i]

                item = WindowItem()
                item.window = window
                item.title = win32gui.GetWindowText(window.handle)
                item.rect = Rect.from_pos_size(
                    (monitor.rect.left + (i%self.max_hidden_row) * item_width,
                        monitor.rect.bottom - 30*(int(i/self.max_hidden_row)+1)),
                    (item_width, 30))
                item.is_hidden = True
                self.item_list.append(item)

        pylewm.modes.hint_helpers.create_hints(self.item_list, self.hintkeys)

    def should_clear(self):
        return True

    def should_draw(self):
        if self.dirty:
            self.dirty = False
            return True
        return False

    def close(self):
        self.closed = True
        pylewm.hotkeys.queue_command(pylewm.hotkeys.escape_mode)

    def confirm_selection(self, item):
        pylewm.focus.set_focus(item.window)
        self.close()

    def end_mode(self):
        super(HintWindowMode, self).end_mode()

    def update_selection(self):
        self.dirty = True
        any_hints = False
        for item in self.item_list:
            if item.hint == self.selection_text:
                self.confirm_selection(item)
                break
            elif item.hint.startswith(self.selection_text):
                any_hints = True
        if not any_hints:
            self.selection_text = ""

    def handle_key(self, key, isMod):
        if self.closed:
            return True
        if not isMod and key.down:
            if len(key.key) == 1 and not key.alt.isSet and not key.app.isSet and not key.ctrl.isSet and not key.win.isSet:
                self.selection_text += key.key
                self.update_selection()
                return True
            elif key.key == 'backspace' and len(self.selection_text) >= 1:
                self.selection_text = self.selection_text[:-1]
                self.update_selection()
                return True
        return super(HintWindowMode, self).handle_key(key, isMod)

    def draw(self, overlay):
        if self.closed:
            return
        for item in self.item_list:
            if not item.hint.startswith(self.selection_text):
                continue

            rect = self.abs_to_overlay(item.rect)

            if item.is_hidden:
                overlay.draw_box(rect, self.bg_color)
                overlay.draw_border(rect, self.border_color, self.border_width)

                overlay.draw_text(
                    item.hint,
                    self.hint_color,
                    Rect((rect.left + 5, rect.top, rect.left + 60, rect.bottom)),
                    (0.5, 0.5)
                )
                overlay.draw_text(
                    item.title,
                    self.title_color,
                    Rect((rect.left + 65, rect.top, rect.right - 5, rect.bottom)),
                    (0.0, 0.5),
                    font=overlay.font_small
                )
            else:
                box_rect = Rect.centered_around(rect.center, self.box_size)
                overlay.draw_box(box_rect, self.bg_color)
                if item.window.floating:
                    overlay.draw_border(box_rect, self.floating_border, 3)
                overlay.draw_text(
                    item.hint,
                    self.hint_color,
                    box_rect,
                    (0.5, 0.5)
                )

@pylewm.commands.PyleCommand
def start_hint_window(hotkeys={}, hintkeys="asdfjkl;"):
    HintWindowMode(hintkeys, hotkeys)()