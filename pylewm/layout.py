from pylewm.rects import Rect, Direction
import math

class Layout:
    def __init__(self):
        self.windows = []
        self.rect = Rect()
        self.pending_drop_slot = None
        self.focus = None
        self.focus_mru = []

    def get_last_focus(self):
        if self.focus_mru:
            return self.focus_mru[-1]
        return None

    def update_layout(self):
        pass

    def add_window(self, window, at_slot=None, insert_direction=None):
        pass

    def remove_window(self, window):
        pass

    def get_window_in_direction(self, from_window, direction):
        return None, direction

    def move_window_in_direction(self, window, direction):
        return False, direction

    def get_drop_slot(self, position, rect):
        return None, False

    def get_focus_window_after_removing(self, window_before_remove):
        return None

    def takeover_from_layout(self, other_layout):
        return False

    def takeover_from_windows(self, window_list):
        return False

    def set_pending_drop_slot(self, pending_slot):
        self.pending_drop_slot = pending_slot