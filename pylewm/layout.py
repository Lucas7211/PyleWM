from pylewm.rects import Rect
import math

class Layout:
    def __init__(self):
        self.window_count = 0

    def get_window_rect(self, rect, window_index):
        return Rect()

class SidebarLayout:
    def __init__(self):
        self.split = 0.5

    def get_window_rect(self, rect, window_index):
        if self.window_count == 1:
            return rect.copy()

        horiz_split = int(float(rect.width) * self.split)
        if window_index == 0:
            return Rect([rect.left, rect.top, rect.left + horiz_split, rect.bottom])

        vert_split = int(float(rect.height) / float(self.window_count - 1))
        vert_pos = vert_split * (window_index - 1)
        return Rect([rect.left + horiz_split, rect.top + vert_pos, rect.right, rect.top + vert_pos + vert_split])