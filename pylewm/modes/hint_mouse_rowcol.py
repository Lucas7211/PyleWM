import pylewm.modes.overlay_mode
import pylewm
from pylewm.rects import Rect
import win32gui, win32api, win32con

class HintRow:
    pass

class HintColumn:
    pass

class HintMouseMode(pylewm.modes.overlay_mode.OverlayMode):
    def __init__(self, hintkeys, hotkeys, clickmode):
        super(HintMouseMode, self).__init__(hotkeys)

        self.window = pylewm.focus.FocusWindow
        self.cover_area = self.window.rect
        self.clickmode = clickmode

        self.hintkeys = hintkeys
        self.overlay_window(self.window)

        self.line_color = (128, 128, 255)
        self.hint_color = (255, 255, 0)
        self.border_width = 1
        self.closed = False

        self.selection_text = ""
        self.x_granularity = 20
        self.y_granularity = 20
        self.shift_size = 3

        self.row_spacing = 100

        self.start_row_mode()

    def start_row_mode(self):
        self.row_mode = True
        self.rows = []
        y = 0
        while y < self.cover_area.height:
            row = HintRow()
            row.rect = Rect((
                0, y, self.cover_area.width, y + self.y_granularity
            ))
            self.rows.append(row)
            y += self.y_granularity

        self.create_hints(self.rows)

    def start_column_mode(self):
        self.selection_text = ""
        self.row_mode = False

        self.columns = []
        x = 0
        while x < self.cover_area.height:
            column = HintColumn()
            column.rect = Rect((
                x, self.selected_row.rect.top,
                x + self.x_granularity, self.selected_row.rect.bottom
            ))
            self.columns.append(column)
            x += self.x_granularity

        self.create_hints(self.columns)

    def close(self):
        self.closed = True
        pylewm.hotkeys.queue_command(pylewm.hotkeys.escape_mode)

    def update_selection(self):
        if self.row_mode:
            for row in self.rows:
                if row.hint == self.selection_text:
                    self.selected_row = row
                    self.start_column_mode()
                    break
        else:
            for column in self.columns:
                if column.hint == self.selection_text:
                    self.selected_column = column
                    self.confirm_selection()
                    break

    def confirm_selection(self):
        pos = self.selected_column.rect.center
        try:
            win32api.SetCursorPos((
                int(self.cover_area.left + pos[0]),
                int(self.cover_area.top + pos[1]),
            ))
        except:
            pass # Not allowed, probably an administrator window has focus or something

        position = win32gui.ScreenToClient(self.window.handle, win32api.GetCursorPos())
        if self.clickmode == 'left':
            pylewm.commands.delay_pyle_command(0.1, lambda: win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, position[0], position[1], 0, 0))
            pylewm.commands.delay_pyle_command(0.15, lambda: win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, position[0], position[1], 0, 0))
        elif self.clickmode == 'double':
            pylewm.commands.delay_pyle_command(0.1, lambda: win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, position[0], position[1], 0, 0))
            pylewm.commands.delay_pyle_command(0.15, lambda: win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, position[0], position[1], 0, 0))
            pylewm.commands.delay_pyle_command(0.2, lambda: win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, position[0], position[1], 0, 0))
            pylewm.commands.delay_pyle_command(0.25, lambda: win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, position[0], position[1], 0, 0))
        elif self.clickmode == 'right':
            pylewm.commands.delay_pyle_command(0.1, lambda: win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, position[0], position[1], 0, 0))
            pylewm.commands.delay_pyle_command(0.15, lambda: win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, position[0], position[1], 0, 0))
        elif self.clickmode == 'middle':
            pylewm.commands.delay_pyle_command(0.1, lambda: win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEDOWN, position[0], position[1], 0, 0))
            pylewm.commands.delay_pyle_command(0.15, lambda: win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEUP, position[0], position[1], 0, 0))

        self.close()


    def shift(self, shift_x, shift_y):
        if self.row_mode:
            for row in self.rows:
                row.rect = row.rect.shifted((0, shift_y))
        else:
            for column in self.columns:
                column.rect = row.rect.shifted((shift_x, shift_y))

    def handle_key(self, key, isMod):
        if not isMod and key.down and not self.closed:
            if key.key == '+':
                if self.row_mode:
                    self.shift(0, self.shift_size)
                else:
                    self.shift(self.shift_size, 0)
                return True
            elif key.key == '-':
                if self.row_mode:
                    self.shift(0, -self.shift_size)
                else:
                    self.shift(-self.shift_size, 0)
                return True
            elif key.key == 'left':
                self.shift(-self.shift_size, 0)
                return True
            elif key.key == 'right':
                self.shift(self.shift_size, 0)
                return True
            elif key.key == 'up':
                self.shift(0, -self.shift_size)
                return True
            elif key.key == 'down':
                self.shift(0, self.shift_size)
                return True
            elif len(key.key) == 1:
                self.selection_text += key.key
                self.update_selection()
                return True
            elif key.key == 'backspace' and len(self.selection_text) >= 1:
                self.selection_text = self.selection_text[:-1]
                self.update_selection()
                return True

        return super(HintMouseMode, self).handle_key(key, isMod)

    def create_hints(self, item_list):
        depth = 1
        key_count = len(self.hintkeys)

        depth_count = float(len(item_list))
        while depth_count > key_count:
            depth += 1
            depth_count /= float(key_count)

        for i, item in enumerate(item_list):
            item.hint = ""
            n = i
            for d in range(0, depth):
                item.hint += self.hintkeys[n % key_count]
                n = int(n / key_count)

    def draw(self, overlay):
        if self.closed:
            return

        if self.row_mode:
            for i, row in enumerate(self.rows):
                if not row.hint.startswith(self.selection_text):
                    continue
                overlay.draw_box(Rect((
                    row.rect.left,
                    row.rect.center[1] - 1,
                    row.rect.right,
                    row.rect.center[1] + 1,
                )), self.line_color)

                x = 0
                if i % 2 != 0:
                    x += self.row_spacing / 2
                while x < self.cover_area.width:
                    overlay.draw_text(row.hint, self.hint_color,
                        row.rect.padded(5, -5).shifted((x, -2)),
                        (0.0, 0.5), font=overlay.font_small, background_box=(0,0,0))

                    x += self.row_spacing
        else:
            for i, column in enumerate(self.columns):
                if not column.hint.startswith(self.selection_text):
                    continue

                center_pos = column.rect.center

                offset = 0
                shift = 0
                length = 40

                if i % 2 == 0:
                    if center_pos[1] < 50:
                        offset = 0
                        length = 80
                        shift = 100
                    else:
                        offset = -40
                        shift = -50
                else:
                    if center_pos[1] > self.cover_area.height - 50:
                        offset = -80
                        length = 80
                        shift = -100
                    else:
                        offset = 0
                        shift = 50

                overlay.draw_box(Rect.from_pos_size(
                    (center_pos[0] - 3, center_pos[1] + offset),
                    (6, length)
                ), self.line_color)
                overlay.draw_text(column.hint, self.hint_color,
                    column.rect.shifted((0, shift)).padded(-20, -20),
                    (0.5, 0.5), font=overlay.font_small, background_box=(0,0,0))

                overlay.draw_box(Rect.from_pos_size(
                    (center_pos[0] - 5, center_pos[1] - 5),
                    (10, 10)
                ), self.hint_color)

@pylewm.commands.PyleCommand
def start_hint_mouse(hotkeys={}, hintkeys="asdfjkl;", clickmode="left"):
    if not pylewm.focus.FocusWindow:
        return
    HintMouseMode(hintkeys, hotkeys, clickmode)()