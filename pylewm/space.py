from pylewm.layouts.sidebar import SidebarLayout
from pylewm.layouts.columns import ColumnsLayout
from pylewm.layouts.autogrid import AutoGridLayout
import traceback
import threading

class Space:
    Layouts = [
        lambda: AutoGridLayout(),
        lambda: SidebarLayout(),
    ]

    def __init__(self, monitor, rect):
        self.windows = []
        self.rect = rect.copy()
        self.visible = False
        self.focus = None
        self.last_focus = None
        self.monitor = monitor
        self.temporary = False
        self.pending_drop_slot = None
        self.focus_mru = []

        self.layout_index = 0
        self.layout = None
        self.switch_layout(0)

    def get_last_focus(self):
        if self.focus_mru:
            return self.focus_mru[-1]
        return None

    def show(self):
        self.visible = True
        for window in self.windows:
            window.show()

    def hide(self):
        self.visible = False
        for window in self.windows:
            window.hide()

    def update_focus(self, focus_window):
        # Update standard focus tracking
        if self.visible:
            if focus_window in self.windows:
                self.focus = focus_window
                if self.focus != self.last_focus:
                    self.last_focus = self.focus
            else:
                self.focus = None
        else:
            self.focus = None

        if self.last_focus and self.last_focus.closed:
            self.last_focus = None
        if self.last_focus and self.last_focus not in self.windows:
            self.last_focus = None

        # Update the focus MRU stack
        if self.focus and (not self.focus_mru or self.focus != self.focus_mru[-1]):
            if self.focus in self.focus_mru:
                self.focus_mru.remove(self.focus)
            self.focus_mru.append(self.focus)

    def update_layout(self, focus_window):
        self.update_focus(focus_window)

        self.layout.focus_mru = self.focus_mru
        self.layout.focus = self.focus
        self.layout.rect.assign(self.rect)
        self.layout.update_layout()

    def add_window(self, window, at_slot=None, direction=None):
        assert not window.space

        window.space = self
        self.windows.append(window)

        self.layout.add_window(window, at_slot, direction)
        self.focus_mru.insert(0, window)

    def remove_window(self, window):
        assert window.space == self

        lost_index = self.windows.index(window)
        self.windows.remove(window)
        self.focus_mru.remove(window)
        window.space = None

        if self.focus is window:
            self.focus = self.layout.get_focus_window_after_removing(window)

        if self.last_focus is window:
            self.last_focus = self.layout.get_focus_window_after_removing(window)

        self.layout.remove_window(window)

    def set_pending_drop_slot(self, slot):
        self.pending_drop_slot = slot
        self.layout.set_pending_drop_slot(slot)

    def get_window_in_direction(self, from_window, direction):
        return self.layout.get_window_in_direction(from_window, direction)

    def move_window_in_direction(self, window, direction):
        return self.layout.move_window_in_direction(window, direction)

    def get_drop_slot(self, position, rect):
        return self.layout.get_drop_slot(position, rect)

    def get_focus_window_after_removing(self, window_before_remove):
        return self.layout.get_focus_window_after_removing(window_before_remove)

    def takeover_from_windows(self, window_list):
        self.windows = list(window_list)
        self.focus_mru = list(window_list)

        for window in window_list:
            window.space = self

        return self.layout.takeover_from_windows(window_list)

    def switch_layout(self, movement):
        self.layout_index = (self.layout_index + movement + len(Space.Layouts)) % len(Space.Layouts)

        old_layout = self.layout
        self.layout = Space.Layouts[self.layout_index]()
        self.layout.focus_mru = self.focus_mru
        self.layout.rect.assign(self.rect)

        handled = False
        if old_layout:
            handled = self.layout.takeover_from_layout(old_layout)
            if not handled:
                handled = self.layout.takeover_from_windows(self.focus_mru)

        if not handled:
            for window in self.focus_mru:
                drop_slot, force_drop = self.layout.get_drop_slot(window.rect.center, window.rect)
                self.layout.add_window(window, at_slot=drop_slot)