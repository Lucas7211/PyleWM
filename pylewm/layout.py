from pylewm.rects import Rect, Direction
import math

class Layout:
    def __init__(self):
        self.windows = []
        self.rect = Rect()
        self.slots = []
    
    def set_windows(self, windows):
        self.windows = windows
        if len(self.windows) != len(self.slots):
            self.slots = [Rect() for i in range(0, len(self.windows))]

    def update_layout(self):
        pass

class SidebarLayout(Layout):
    def __init__(self):
        Layout.__init__(self)
        self.split = 0.5
        self.last_focus = None
        self.last_sidebar_focus = None

    def update_layout(self):
        self.update_focus()
        self.update_slots()

    @property
    def window_count(self):
        return len(self.windows)

    def update_focus(self):
        if self.focus and self.focus in self.windows:
            self.last_focus = self.focus
            focus_index = self.windows.index(self.focus)
            if focus_index >= 1:
                self.last_sidebar_focus = self.focus
        if self.last_focus not in self.windows:
            self.last_focus = None
        if (self.last_sidebar_focus not in self.windows
            or self.windows.index(self.last_sidebar_focus) < 1):
            self.last_sidebar_focus = None

    def update_slots(self):
        if self.window_count == 0:
            return
        if self.window_count == 1:
            self.slots[0].assign(self.rect)
            return

        horiz_split = int(float(self.rect.width) * self.split)
        vert_split = int(float(self.rect.height) / float(self.window_count - 1))

        self.slots[0].topleft = (self.rect.left, self.rect.top)
        self.slots[0].bottomright = (self.rect.left + horiz_split, self.rect.bottom)

        for window_index in range(1, self.window_count):
            vert_pos = vert_split * (window_index - 1)
            self.slots[window_index].topleft = (self.rect.left + horiz_split, self.rect.top + vert_pos)
            self.slots[window_index].bottomright = (self.rect.right, self.rect.top + vert_pos + vert_split)

    def get_focusable_slot(self):
        focus_index = 0
        if self.last_focus and self.last_focus in self.windows:
            focus_index = self.windows.index(self.last_focus)
        return focus_index

    def get_sidebar_focusable_slot(self):
        # Sidebar was focused
        sidebar_index = 1
        if self.last_sidebar_focus and self.last_sidebar_focus in self.windows:
            sidebar_index = self.windows.index(self.last_sidebar_focus)
            if sidebar_index < 1:
                sidebar_index = 1
        return sidebar_index

    def move_from_slot(self, slot, direction):
        # Take focus from external slot
        if slot == -1:
            if self.window_count == 0:
                return -1, direction
            elif self.window_count == 1:
                return 0, direction
            elif direction == Direction.Right:
                return 0, direction
            elif direction == Direction.Left:
                return self.get_sidebar_focusable_slot(), direction
            else:
                return self.get_focusable_slot(), direction

        # In-space navigation
        if direction == Direction.Next:
            new_slot = (slot+1) % self.window_count
            return new_slot, direction
        elif direction == Direction.Previous:
            new_slot = (slot-1 + self.window_count) % self.window_count
            return new_slot, direction

        if slot == 0:
            # Focus in main window
            if self.window_count > 1:
                if direction == Direction.Right:
                    return self.get_sidebar_focusable_slot(), direction

            # Escape in other direction
            return -1, direction 
        else:
            if direction == Direction.Left:
                # Focus back to main window
                return 0, direction

            if direction == Direction.Up:
                # Focus up in sidebar
                if slot > 1:
                    return (slot-1), direction

            if direction == Direction.Down:
                # Focus down in sidebar
                if slot < self.window_count - 1:
                    return (slot+1), direction

            # Didn't find any, escape in the specified direction
            return -1, direction 