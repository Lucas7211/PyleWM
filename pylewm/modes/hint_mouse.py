import pylewm.modes.overlay_mode
import pylewm.modes.hint_helpers
import pylewm
from pylewm.rects import Rect
import win32gui, win32api, win32con

class HintRegion:
    pass

class HintPoint:
    pass

class HintMouseMode(pylewm.modes.overlay_mode.OverlayMode):
    def __init__(self, hintkeys, hotkeys, clickmode):
        self.window = pylewm.focus.FocusWindow
        self.cover_area = self.window.rect

        self.clickmode = clickmode
        self.hintkeys = hintkeys

        self.overlay_window(self.window)

        self.line_color = (128, 128, 255)
        self.hint_color = (255, 255, 0)
        self.center_color = (255, 0, 128)
        self.closed = False

        self.selection_text = ""

        if self.cover_area.width <= 1300:
            self.region_width = 100
            self.region_height = 50
        else:
            self.region_width = 120
            self.region_height = 70

        self.point_offsets = [
            (-60, -35, 20),
            (-42, -25, 20),
            (-17, -15, 20),
            (-0, -45, 20),
            (20, -25, 20),
            (40, 5, 20),
            (60, -17, 20),

            (-58, 16, -20),
            (-40, 0, -20),
            (-20, 20, -20),
            (0, 31, -20),
            (19, 17, -20),
            (50, 27, -20),
        ]

        self.shift_size = 5

        self.start_region_mode()
        super(HintMouseMode, self).__init__(hotkeys)

    def start_region_mode(self):
        self.region_mode = True
        self.regions = []

        y = 0
        while y < self.cover_area.height:
            x = 0
            while x < self.cover_area.width:
                region = HintRegion()
                region.rect = Rect((
                    x, y,
                    min(x + self.region_width, self.cover_area.width),
                    min(y + self.region_height, self.cover_area.height)
                ))
                self.regions.append(region)
                x += self.region_width
            y += self.region_height

        pylewm.modes.hint_helpers.create_hints(self.regions, self.hintkeys)

    def start_points_mode(self, region):
        self.selected_region = region
        self.selection_text = ""
        self.region_mode = False

        pos = self.selected_region.rect.center
        self.points = []
        for offset in self.point_offsets:
            point = HintPoint()
            point.position = [
                pos[0] + offset[0],
                pos[1] + offset[1]
            ]
            point.hidden = point.position[1] < 0 or point.position[1] > self.cover_area.height

            point.offset = offset[2]
            if point.offset >= 0:
                if point.position[1] - point.offset < 5:
                    point.offset = -10
            else:
                if point.position[1] - point.offset > self.cover_area.height - 5:
                    point.offset = 10

            self.points.append(point)

        pylewm.modes.hint_helpers.create_hints(self.points, self.hintkeys)

    def close(self):
        self.closed = True
        pylewm.hotkeys.queue_command(pylewm.hotkeys.escape_mode)

    def update_selection(self):
        if self.region_mode:
            any_hints = False
            for region in self.regions:
                if region.hint == self.selection_text:
                    self.start_points_mode(region)
                    break
                elif region.hint.startswith(self.selection_text):
                    any_hints = True
            if not any_hints:
                self.selection_text = ""
        else:
            any_hints = False
            for point in self.points:
                if point.hint == self.selection_text:
                    self.confirm_selection(point.position)
                    break
                elif point.hint.startswith(self.selection_text):
                    any_hints = True
            if not any_hints:
                self.selection_text = ""

    def confirm_selection(self, pos):
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
        if not self.region_mode:
            self.selected_region.rect = self.selected_region.rect.shifted((shift_x, shift_y))
            for point in self.points:
                point.position[0] += shift_x
                point.position[1] += shift_y

    def handle_key(self, key, isMod):
        if self.closed:
            return None
        if not isMod and key.down:
            if key.key == '+':
                self.shift(0, self.shift_size)
                return True
            elif key.key == '-':
                self.shift(0, -self.shift_size)
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
            elif key.key == 'enter':
                if not self.region_mode:
                    self.confirm_selection(self.selected_region.rect.center)
                return True
            elif len(key.key) == 1 and not key.alt.isSet and not key.app.isSet and not key.ctrl.isSet and not key.win.isSet:
                self.selection_text += key.key
                self.update_selection()
                return True
            elif key.key == 'backspace' and len(self.selection_text) >= 1:
                self.selection_text = self.selection_text[:-1]
                self.update_selection()
                return True

        return super(HintMouseMode, self).handle_key(key, isMod)


    def draw(self, overlay):
        if self.closed:
            return

        if self.region_mode:
            for i, region in enumerate(self.regions):
                if not region.hint.startswith(self.selection_text):
                    continue

                overlay.draw_text(region.hint, self.hint_color,
                    region.rect.shifted((0, -2)),
                    (0.5, 0.5), font=overlay.font_small, background_box=(0,0,0))
        else:
            overlay.draw_box(Rect.centered_around(self.selected_region.rect.center, (10, 10)), self.center_color)
            #overlay.draw_border(self.selected_region.rect, self.center_color, 1)

            for i, point in enumerate(self.points):
                if not point.hint.startswith(self.selection_text):
                    continue
                if point.hidden:
                    continue
                overlay.draw_box(Rect.from_pos_size(
                    (point.position[0] - 2, point.position[1] - max(point.offset, 0)),
                    (4, abs(point.offset))
                ), self.line_color)

                overlay.draw_text(point.hint, self.hint_color,
                    Rect.centered_around(
                        (point.position[0], point.position[1] - point.offset), (50, 50)
                    ), (0.5, 0.5), font=overlay.font_small, background_box=(0,0,0))

                overlay.draw_box(Rect.centered_around(point.position, (6, 6)), self.hint_color)

@pylewm.commands.PyleCommand
def start_hint_mouse(hotkeys={}, hintkeys="asdfjkl;", clickmode="left"):
    if not pylewm.focus.FocusWindow:
        return
    HintMouseMode(hintkeys, hotkeys, clickmode)()