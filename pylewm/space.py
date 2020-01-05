from pylewm.layout import SidebarLayout
import traceback

class Space:
    def __init__(self, monitor, rect):
        self.windows = []
        self.rect = rect.copy()
        self.layout = SidebarLayout()
        self.visible = False
        self.focus = None
        self.last_focus = None
        self.monitor = monitor
        self.temporary = False
        self.pending_drop_slot = -1

    def show(self):
        self.visible = True
        for window in self.windows:
            window.show()

    def hide(self):
        self.visible = False
        for window in self.windows:
            window.hide()

    def update_focus(self, focus_window):
        if self.visible:
            if focus_window in self.windows:
                self.focus = focus_window
                if self.focus != self.last_focus:
                    #print(f"UPDATE LAST FOCUS {self.focus.window_title}")
                    self.last_focus = self.focus
            else:
                self.focus = None
        else:
            self.focus = None

        if self.last_focus and self.last_focus.closed:
            self.last_focus = None
        if self.last_focus and self.last_focus not in self.windows:
            self.last_focus = None

    def get_last_focused_slot(self):
        if self.focus and self.focus in self.windows:
            return self.windows.index(self.focus)
        if self.last_focus and self.last_focus in self.windows:
            return self.windows.index(self.last_focus)
        if self.windows:
            return 0
        return -1

    def update_layout(self, focus_window):
        self.update_focus(focus_window)

        self.layout.pending_drop_slot = self.pending_drop_slot
        self.layout.set_windows(self.windows)
        self.layout.focus = self.focus
        self.layout.rect.assign(self.rect)
        self.layout.update_layout()

        for i, window in enumerate(self.windows):
            window.rect.assign(self.layout.slots[i])

    def move_from_slot(self, slot, direction):
        return self.layout.move_from_slot(slot, direction)

    def swap_slots(self, from_slot, to_slot):
        from_window = self.windows[from_slot]
        to_window = self.windows[to_slot]

        self.windows[to_slot] = from_window
        self.windows[from_slot] = to_window
        self.layout.on_slots_swapped(from_slot, to_slot)

    def insert_slot(self, at_slot, direction, window):
        self.add_window(window)
        self.windows.remove(window)

        insert_position = self.layout.get_insert_slot(at_slot, direction)
        self.windows.insert(insert_position, window)

    def drop_into_slot(self, window, slot):
        self.add_window(window)
        self.windows.remove(window)
        self.windows.insert(slot, window)

    def add_window(self, window):
        assert not window.space

        window.space = self
        self.windows.append(window)

    def remove_window(self, window):
        assert window.space == self

        self.windows.remove(window)
        window.space = None

        if self.focus is window:
            if self.windows:
                self.focus = self.windows[0]
            else:
                self.focus = None

        if self.last_focus is window:
            if self.windows:
                self.last_focus = self.windows[0]
            else:
                self.last_focus = None

    def set_pending_drop_slot(self, slot):
        self.pending_drop_slot = slot

    def get_drop_slot(self, position, rect):
        return self.layout.get_drop_slot(position, rect)