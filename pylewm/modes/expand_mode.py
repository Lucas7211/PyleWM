import pylewm
import pylewm.hotkeys
import pylewm.sendkeys
import pylewm.focus
import pylewm.modes.overlay_mode
from pylewm.rects import Rect

class ExpandMode(pylewm.modes.overlay_mode.OverlayMode):
    def __init__(self, hotkeys, expansions):
        self.text = ""
        self.closed = False
        self.dirty = True
        self.expansions = expansions

        self.bg_color = (0, 0, 0)
        self.text_color = (255, 255, 255)

        focused_monitor = pylewm.focus.get_focused_monitor()
        self.base_rect = focused_monitor.rect.copy()

        focused_window = pylewm.focus.FocusWindow
        if focused_window:
            self.base_rect = focused_window.real_position.copy()

        self.box_size = (min(1000, self.base_rect.width-50), 32)
        self.box_rect = Rect.centered_around(self.base_rect.center, self.box_size)
        self.overlay_static(self.box_rect)

        super(ExpandMode, self).__init__(hotkeys)

    def should_clear(self):
        return False

    def should_draw(self):
        if self.dirty:
            self.dirty = False
            return True
        return False

    def confirm_selection(self):
        self.close()
        
        args = self.text.split()
        if args:
            match = None
            if args[0] in self.expansions:
                match = self.expansions[args[0]]
            else:
                for key, value in self.expansions.items():
                    if key.startswith(args[0]):
                        match = value

            if match:
                match = match.format(*args[1:])
                pylewm.hotkeys.queue_command(pylewm.sendkeys.sendsequence(match))

    def close(self):
        self.closed = True
        pylewm.hotkeys.queue_command(pylewm.hotkeys.escape_mode)

    def handle_key(self, key, isMod):
        if not isMod and key.down and not self.closed:
            if len(key.key) == 1:
                self.text += pylewm.hotkeys.get_char_from_key(key)
                self.dirty = True
                return True
            elif key.key == 'backspace' and len(self.text) >= 1:
                self.text = self.text[:-1]
                self.dirty = True
                return True
            elif key.key == 'enter':
                self.confirm_selection()
                return True

        return super(ExpandMode, self).handle_key(key, isMod)

    def draw(self, overlay):
        if self.closed:
            return

        overlay.draw_box(Rect((0, 0, self.box_size[0], self.box_size[1])), self.bg_color)
        if self.text:
            overlay.draw_text(
                self.text,
                self.text_color,
                Rect.from_pos_size(
                    (10, 0),
                    (self.box_size[0] - 25, self.box_size[1])),
                (0.0, 0.5)
            )


@pylewm.commands.PyleCommand
def start_expand_mode(expansions={}, hotkeys = {}):
    mode = ExpandMode(hotkeys, expansions)
    mode()