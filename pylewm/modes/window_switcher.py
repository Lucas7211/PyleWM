import math
import pylewm.modes.overlay_mode
import pylewm.modes.hint_helpers
import pylewm.colors
import pylewm
import pylewm.space
import pylewm.focus
import pylewm.spaces
import pylewm.monitors
from pylewm.rects import Rect
from pylewm.window import WindowsByProxy, WindowState, Window
from pylewm.modes.overlay_mode import OverlayWindow

import win32gui, win32api, win32con

class SwitchItem:
    def __lt__(self, other):
        if self.is_window and not other.is_window:
            return True
        if not self.is_window and other.is_window:
            return False
        return self.sort_order < other.sort_order

class WindowSwitcherMode(pylewm.modes.overlay_mode.OverlayMode):
    def __init__(self, hintkeys, hotkeys, persistent):
        super(WindowSwitcherMode, self).__init__(hotkeys)
        self.hintkeys = hintkeys
        self.persistent = persistent
        self.overlay_global()

        self.row_bg_color = (0x40, 0x40, 0x40)
        
        self.space_bg_color = (0x0, 0x0, 0x0)
        self.space_empty_bg_color = (0x10, 0x10, 0x10)
        self.space_empty_visible_bg_color = (0x05, 0x10, 0x15)
        self.space_empty_focused_bg_color = (0x10, 0x0, 0x10)
        self.space_border_color = (0x46, 0x46, 0x46)
        self.space_visible_border_color = (0x88, 0x88, 0x88)
        self.space_border_width = 4
        self.space_margin = 50

        self.window_border_color = self.space_border_color
        self.window_visible_border_color = self.space_visible_border_color
        self.window_focused_border_color = (0xff, 0x00, 0xff)
        self.window_border_width = 4

        self.hint_size = (200, 50)
        self.hint_color = (0xff, 0xff, 0x00)
        self.hint_space_color = (0xa0, 0xa0, 0xa0)

        self.title_color = (0x96, 0x96, 0x96)
        self.title_focused_color = (0xff, 0x00, 0xff)

        self.selection_text = ""

        self.dirty = True
        self.closed = False
        self.captureAll = False
        self.last_focus = pylewm.focus.FocusWindow
        self.last_space = pylewm.focus.get_focused_space()
        self.refresh_hints()

    def refresh_hints(self):
        self.item_list = []
        self.items_by_window = {}
        self.items_by_space = {}
        for proxy, window in WindowsByProxy.items():
            if window.closed:
                continue
            if window.state == WindowState.IgnorePermanent:
                continue
            if window.is_dropdown:
                continue
            if window.is_taskbar:
                continue
            if window.window_info.cloaked:
                continue
            if window.window_title == "":
                continue
            if window.real_position.height == 0 or window.real_position.width == 0:
                continue
            if window.window_info.is_minimized():
                continue
            if not window.space:
                continue

            item = SwitchItem()
            item.is_window = True
            item.window = window
            item.rect = window.real_position
            item.is_hidden = False
            item.click_rect = None
            item.sort_order = window.serial_counter

            self.item_list.append(item)
            self.items_by_window[window] = item

        # Add hints for empty spaces as well
        for monitor in pylewm.monitors.Monitors:
            for space in monitor.spaces:
                if len(space.windows) == 0:
                    item = SwitchItem()
                    item.is_window = False
                    item.space = space
                    item.rect = space.rect
                    item.is_hidden = False
                    item.click_rect = None
                    item.sort_order = 0

                    self.item_list.append(item)
                    self.items_by_space[space] = item

        self.item_list.sort()
        pylewm.modes.hint_helpers.create_hints(self.item_list, self.hintkeys)

    def should_clear(self):
        return True

    def should_draw(self):
        if self.dirty or self.last_focus != pylewm.focus.FocusWindow or self.last_space != pylewm.focus.get_focused_space():
            self.last_focus = pylewm.focus.FocusWindow
            self.last_space = pylewm.focus.get_focused_space()
            self.dirty = False
            if self.selection_text == "":
                self.refresh_hints()
            return True
        return False

    def confirm_selection(self, item):
        def command():
            if item.is_window:
                pylewm.focus.set_focus(item.window)
            else:
                pylewm.spaces.goto_space(item.space)
                pylewm.focus.set_focus_space(item.space)
        pylewm.hotkeys.queue_command(command)
        if not self.persistent:
            self.close()
        else:
            self.selection_text = ""
            self.refresh_hints()
            self.update_selection()

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

    def clicked(self, pos):
        for item in self.item_list:
            if not item.click_rect:
                continue
            if item.click_rect.contains(pos):
                def command():
                    if item.is_window:
                        pylewm.focus.set_focus_no_mouse(item.window)
                    else:
                        item.space.monitor.switch_to_space(item.space)
                    if not self.persistent:
                        self.close()
                    else:
                        self.selection_text = ""
                        self.refresh_hints()
                        self.update_selection()
                pylewm.hotkeys.queue_command(command)
                break
        return False

    def handle_key(self, key, isMod):
        if self.closed:
            return True
        if not isMod and key.down and not key.any_modifier():
            if len(key.key) == 1:
                self.selection_text += key.key
                self.update_selection()
                return True
            elif key.key == 'backspace' and len(self.selection_text) >= 1:
                self.selection_text = self.selection_text[:-1]
                self.update_selection()
                return True
        return super(WindowSwitcherMode, self).handle_key(key, isMod)

    def close(self):
        self.closed = True
        pylewm.hotkeys.queue_command(pylewm.hotkeys.escape_mode)

    def end_mode(self):
        super(WindowSwitcherMode, self).end_mode()

    def draw(self, overlay : OverlayWindow):
        if self.closed:
            return

        for monitor in pylewm.monitors.Monitors:
            self.draw_spaces(
                overlay,
                self.abs_to_overlay(
                    monitor.rect.make_from_relative_position(
                        (0.0, 0.05, 1.0, 0.5)
                    )),
                monitor.spaces
            )

            if monitor.temp_spaces:
                row_count = min(math.ceil(len(monitor.temp_spaces) / 4), 3)
                spaces_per_row = math.ceil(len(monitor.temp_spaces) / row_count)
                row_size = 0.35 / row_count
                row_width = min(0.9, len(monitor.temp_spaces) * 0.4)

                for i in range(0, row_count):
                    self.draw_spaces(
                        overlay,
                        self.abs_to_overlay(
                            monitor.rect.make_from_relative_position(
                                ((1-row_width)/2, 0.55+row_size*i, (1+row_width)/2, 0.55+row_size*(i+1))
                            ).shifted((0, i*self.space_margin))),
                        monitor.temp_spaces[(spaces_per_row*i):min(spaces_per_row*(i+1), len(monitor.temp_spaces))]
                    )

    def draw_spaces(self, overlay : OverlayWindow, rect : Rect, spaces : list[pylewm.space.Space]):
        space_count = len(spaces)
        if space_count == 0:
            return

        aspect = spaces[0].rect.width / spaces[0].rect.height
        box_height = rect.height
        box_width = box_height * aspect

        margin = self.space_margin
        needed_width = box_width*space_count + margin*(space_count-1)
        if needed_width > rect.width:
            factor = rect.width / (needed_width + 40)
            box_width *= factor
            box_height *= factor
            margin *= factor

        needed_width = box_width*space_count + margin*(space_count-1)
        offset_left = rect.left + (rect.width - needed_width) / 2
        offset_top = rect.top + (rect.height - box_height) / 2

        overlay.draw_box(rect.padded(0, (rect.height - box_height) / 2 - 20), self.row_bg_color)

        for space_index, space in enumerate(spaces):
            space_box = Rect.from_pos_size(
                (offset_left + space_index*box_width + space_index*margin, offset_top),
                (box_width, box_height)
            )

            border_color = self.space_border_color
            bg_color = self.space_bg_color
            if len(space.windows) == 0:
                if self.last_space == space:
                    border_color = self.space_empty_focused_bg_color
                    bg_color = self.space_empty_focused_bg_color
                elif space.visible:
                    border_color = self.space_empty_visible_bg_color
                    bg_color = self.space_empty_visible_bg_color
                else:
                    border_color = self.space_empty_bg_color
                    bg_color = self.space_empty_bg_color
            elif space.visible:
                border_color = self.space_visible_border_color

            overlay.draw_box(space_box, bg_color)
            overlay.draw_border(space_box, border_color, self.space_border_width)

            if space in self.items_by_space:
                item = self.items_by_space[space]
                if item.hint.startswith(self.selection_text):
                    item.click_rect = space_box.copy()
                    hint_rect = Rect.centered_around(space_box.center, self.hint_size)
                    overlay.draw_text(
                        item.hint,
                        self.hint_space_color,
                        hint_rect,
                        (0.5, 0.5),
                    )

            for window in space.windows:
                window_box = window.layout_position.for_relative_parent(space.rect, space_box)
                window_color = self.window_border_color
                title_color = self.title_color

                if window == self.last_focus:
                    window_color = self.window_focused_border_color
                    title_color = self.title_focused_color
                elif space.visible:
                    window_color = self.window_visible_border_color

                font = overlay.font_small
                if len(space.windows) == 1:
                    font = overlay.font

                title_box = Rect.from_pos_size(
                    (window_box.left, window_box.top),
                    (window_box.width, 35),
                )

                window_class_color = pylewm.colors.get_random_color_for_str_hsv(window.window_class)
                if window_class_color:
                    color_rgb = pylewm.colors.hsv_to_rgb(window_class_color)
                    title_color = pylewm.colors.get_text_color_for_background(color_rgb)
                    overlay.draw_box(title_box, color_rgb)

                overlay.draw_border(window_box, window_color, self.window_border_width)
                overlay.draw_text(
                    window.window_title,
                    title_color,
                    title_box.padded(15, 0),
                    (0.0, 0.5),
                    font,
                )

                if window in self.items_by_window:
                    item = self.items_by_window[window]
                    item.click_rect = window_box.copy()

                    if item.hint.startswith(self.selection_text):
                        hint_rect = Rect.centered_around(window_box.center, self.hint_size)
                        overlay.draw_text(
                            item.hint,
                            self.hint_color,
                            hint_rect,
                            (0.5, 0.5),
                        )
                
                if window.tab_group and len(window.tab_group.windows) >= 2:
                    tab_count = len(window.tab_group.windows)
                    btn_width = int(min(100, 0.8 * title_box.width / max(tab_count, 4)))
                    btn_height = int(min(btn_width * (window_box.height / window_box.width),
                                    window_box.bottom - title_box.bottom - self.window_border_width))
                    btn_spacing = int(min(btn_width * 0.1, 10))

                    pos = title_box.center[0] - (btn_width*tab_count)/2
                    for i, tab in enumerate(window.tab_group.windows):
                        tab_box = Rect.from_pos_size((pos+btn_spacing/2+btn_width*i, window_box.bottom-btn_height-self.window_border_width), (btn_width-btn_spacing, btn_height))
                        color_hsv = pylewm.colors.get_random_color_for_str_hsv(tab.window_class)
                        if tab != window:
                            color_hsv[1] *= 0.4
                            color_hsv[2] *= 0.4
                        color_rgb = pylewm.colors.hsv_to_rgb(color_hsv)
                        overlay.draw_box(tab_box, color_rgb)


@pylewm.commands.PyleCommand
def start_window_switcher(hotkeys={}, hintkeys="asdfjkl;", persistent=False):
    WindowSwitcherMode(hintkeys, hotkeys, persistent)()