import pylewm
import pylewm.modes.overlay_mode
import win32api, win32con, win32gui
from pylewm.rects import Rect
from fuzzywuzzy import fuzz

class ListOption():
    def __init__(self, name):
        self.name = name

    def confirm(self):
        pass

    def filter(self, text, filter_obj):
        name_lower = self.name.lower()
        score = 100

        contains_all = True
        for phrase in filter_obj.phrases:
            if phrase not in name_lower:
                score -= 100

        if name_lower.startswith(filter_obj.text_lower):
            score += 50

        score += fuzz.token_sort_ratio(text, self.name)
        if score < 25:
            return 0
        else:
            return score

class ListFilterObj():
    def __init__(self):
        pass

class ListMode(pylewm.modes.overlay_mode.OverlayMode):
    def __init__(self, hotkeys, options):
        self.all_options = options
        self.options = options
        self.selected_index = 0 
        self.has_selection = False

        self.filter_text = ""
        self.closed = False
        self.dirty = True

        self.displayed_count = 7
        self.context_pre = 3
        self.box_width = 1000
        self.row_height = 32

        self.bg_color = (0, 0, 0)
        self.text_color = (255, 255, 255)
        self.filter_color = (128, 255, 128)
        self.bg_selected_color = (0, 128, 255)

        self.overlay_monitor(pylewm.focus.get_focused_monitor())
        super(ListMode, self).__init__(hotkeys)

    def should_clear(self):
        return False

    def should_draw(self):
        if self.dirty:
            self.dirty = False
            return True
        return False

    def select_next(self):
        self.selected_index = min(self.selected_index+1, len(self.options)-1)
        self.has_selection = True
        self.dirty = True

    def select_prev(self):
        self.selected_index = max(self.selected_index-1, 0)
        self.has_selection = True
        self.dirty = True

    def confirm_selection(self):
        if self.selected_index != -1:
            self.options[self.selected_index].confirm()
        self.close()

    def close(self):
        self.closed = True
        pylewm.hotkeys.queue_command(pylewm.hotkeys.escape_mode)

    def get_filter_obj(self):
        obj = ListFilterObj()
        obj.phrases = [x.lower() for x in self.filter_text.split(" ")]
        obj.text_lower = self.filter_text.lower()
        return obj

    def handle_key(self, key, isMod):
        if not isMod and key.down and not self.closed:
            if len(key.key) == 1:
                if key.shift.isSet:
                    self.filter_text += key.key.upper()
                else:
                    self.filter_text += key.key
                self.update_filter()
                return True
            elif key.key == 'backspace' and len(self.filter_text) >= 1:
                self.filter_text = self.filter_text[:-1]
                self.update_filter()
                return True
            elif key.key == 'up':
                self.select_prev()
                return True
            elif key.key == 'down':
                self.select_next()
                return True
            elif key.key == 'enter':
                self.confirm_selection()
                return True

        return super(ListMode, self).handle_key(key, isMod)

    def update_filter(self):
        self.dirty = True
        filter_obj = self.get_filter_obj()

        selected_option = None
        if self.selected_index != -1:
            selected_option = self.options[self.selected_index]
        self.selected_index = -1

        self.options = []
        for opt in self.all_options:
            opt.score = opt.filter(self.filter_text, filter_obj)
            if opt.score > 0:
                self.options.append(opt)

        self.options.sort(key = lambda x: x.score, reverse=True)

        if self.has_selection:
            for i, opt in enumerate(self.options):
                if selected_option is opt:
                    self.selected_index = i

        if self.selected_index == -1 and len(self.options) > 0:
            self.selected_index = 0

    def draw(self, overlay):
        if self.closed:
            return
        box_left = (self.overlay_rect.width - self.box_width) / 2
        box = Rect((
            box_left,
            0,
            box_left + self.box_width,
            self.displayed_count * self.row_height + 10 + 40
        ))

        start_index = max(0, self.selected_index - self.context_pre)
        end_index = min(start_index + self.displayed_count, len(self.options))

        overlay.draw_box(box, self.bg_color)

        for position_index, option_index in enumerate(range(start_index, end_index)):
            if option_index == self.selected_index:
                overlay.draw_box(Rect((
                    box.left, box.top + self.row_height * position_index,
                    box.right, box.top + self.row_height * (position_index + 1) + 5
                )), self.bg_selected_color)

            overlay.draw_text(
                self.options[option_index].name,
                self.text_color,
                Rect.from_pos_size(
                    (box.left + 5, box.top + 5 + self.row_height * position_index),
                    (box.width - 10, self.row_height)
                ),
                (0.0, 0.5),
            )
    
        if self.filter_text:
            overlay.draw_text(
                self.filter_text,
                self.filter_color,
                Rect.from_pos_size(
                    (box.left, box.bottom - 40),
                    (box.width - 5, 35)),
                (1.0, 1.0)
            )
