from pylewm.layout import Layout
from pylewm.rects import Rect, Direction

class SidebarLayout(Layout):
    def __init__(self, flipped=False):
        Layout.__init__(self)
        self.split = 0.5
        self.flipped = flipped

        self.main_window = None
        self.sidebar = []

    def get_sidebar_mru(self):
        for window in reversed(self.focus_mru):
            if window == self.main_window:
                continue
            return window
        return None

    def add_window(self, window, at_slot=None, insert_direction=None):
        if not self.main_window:
            self.main_window = window
        elif at_slot is not None:
            if at_slot == 0:
                if self.main_window:
                    self.sidebar.insert(0, self.main_window)
                self.main_window = window
            else:
                self.sidebar.insert(at_slot-1, window)
        elif ((not self.flipped and insert_direction in Direction.ANY_Right)
                or (self.flipped and insert_direction in Direction.ANY_Left)):
            if self.main_window:
                self.sidebar.insert(0, self.main_window)
            self.main_window = window
        elif insert_direction in Direction.ANY_Down:
            self.sidebar.insert(0, window)
        elif self.focus:
            if self.focus == self.main_window:
                self.sidebar.insert(0, window)
            else:
                self.sidebar.insert(self.sidebar.index(self.focus) + 1, window)
        else:
            self.sidebar.append(window)

    def remove_window(self, window):
        if window == self.main_window:
            if self.sidebar:
                self.main_window = self.sidebar[0]
                del self.sidebar[0]
            else:
                self.main_window = None
        else:
            self.sidebar.remove(window)

    def get_horizontal_positions(self):
        horiz_split = int(float(self.rect.width) * self.split)
        if self.flipped:
            return (
                self.rect.left + horiz_split,
                self.rect.right,
                self.rect.left,
                self.rect.left + horiz_split,
            )
        else:
            return (
                self.rect.left,
                self.rect.left + horiz_split,
                self.rect.left + horiz_split,
                self.rect.right
            )

    def update_layout(self):
        if not self.main_window:
            return

        h_main_start, h_main_end, h_sidebar_start, h_sidebar_end = self.get_horizontal_positions()
        new_rect = Rect()

        # Update the position of the main window
        if not self.sidebar:
            if self.pending_drop_slot is not None:
                if self.pending_drop_slot == 0:
                    # Pending drop on the main window
                    new_rect.coordinates = (
                        h_sidebar_start,
                        self.rect.top,
                        h_sidebar_end,
                        self.rect.bottom,
                    )
                    self.main_window.set_layout(new_rect)
                else:
                    # Pending drop on the sidebar
                    new_rect.coordinates = (
                        h_main_start,
                        self.rect.top,
                        h_main_end,
                        self.rect.bottom,
                    )
                    self.main_window.set_layout(new_rect)
            else:
                # Full sreen main window
                self.main_window.layout_position.assign(self.rect)
        else:
            if self.pending_drop_slot is not None and self.pending_drop_slot == 0:
                # Pending drop on main window
                new_rect.coordinates = (
                    h_main_start + 25,
                    self.rect.top + 25,
                    h_main_end - 25,
                    self.rect.bottom - 25,
                )
                self.main_window.set_layout(new_rect)
            else:
                # Perfectly normal main window
                new_rect.coordinates = (
                    h_main_start,
                    self.rect.top,
                    h_main_end,
                    self.rect.bottom,
                )
                self.main_window.set_layout(new_rect)

            # Update the position of the sidebar windows
            slot_count = len(self.sidebar)

            if self.pending_drop_slot is not None and self.pending_drop_slot != 0:
                # Add an empty slot for the pending dropped window
                slot_count += 1

            slot_height = int(float(self.rect.height) / float(slot_count))
            slot_splits = []
            for i in range(0, slot_count):
                slot_splits.append(self.rect.top + (slot_height * i))
            slot_splits.append(self.rect.bottom)

            for slot_index, window in enumerate(self.sidebar):
                slot_position = slot_index

                # Offset for the pending empty space
                if self.pending_drop_slot is not None and self.pending_drop_slot != 0 and slot_index >= self.pending_drop_slot-1:
                    slot_position += 1

                new_rect.coordinates = (
                    h_sidebar_start,
                    slot_splits[slot_position],
                    h_sidebar_end,
                    slot_splits[slot_position+1],
                )
                window.set_layout(new_rect)

    def get_window_in_direction(self, from_window, direction):
        # No windows, no focus
        if not self.main_window:
            return None, direction

        # Take focus from an external layout
        if not from_window:
            if ((not self.flipped and direction in Direction.ANY_Right)
                 or (self.flipped and direction in Direction.ANY_Left)):
                return self.main_window, direction
            if ((not self.flipped and direction in Direction.ANY_Left)
                 or (self.flipped and direction in Direction.ANY_Right)):
                if self.sidebar:
                    return self.get_sidebar_mru(), direction
                else:
                    return self.main_window, direction
            elif direction in Direction.ANY_Up:
                return (self.main_window if self.focus_mru[-1] == self.main_window else self.sidebar[-1]), direction
            elif direction in Direction.ANY_Down:
                return (self.main_window if self.focus_mru[-1] == self.main_window else self.sidebar[0]), direction
            return self.main_window, direction

        if from_window == self.main_window:
            # Go to sidebar from main windew
            if ((not self.flipped and direction in Direction.ANY_Right)
                 or (self.flipped and direction in Direction.ANY_Left)):
                return self.get_sidebar_mru(), direction
            elif direction == Direction.Previous:
                if self.sidebar:
                    return self.sidebar[-1], direction
                else:
                    return self.main_window, direction
            elif direction == Direction.Next:
                if self.sidebar:
                    return self.sidebar[0], direction
                else:
                    return self.main_window, direction
        else:
            sidebar_index = self.sidebar.index(from_window)

            if ((not self.flipped and direction in Direction.ANY_Left)
                 or (self.flipped and direction in Direction.ANY_Right)):
                # Go to main window from sidebar
                return self.main_window, direction
            elif direction == Direction.Previous:
                if sidebar_index == 0:
                    return self.main_window, direction
                else:
                    return self.sidebar[sidebar_index-1], direction
            elif direction == Direction.Up:
                if sidebar_index == 0:
                    return None, direction
                else:
                    return self.sidebar[sidebar_index-1], direction
            elif direction == Direction.Next:
                if sidebar_index == len(self.sidebar)-1:
                    return self.main_window, direction
                else:
                    return self.sidebar[sidebar_index+1], direction
            elif direction == Direction.Down:
                if sidebar_index == len(self.sidebar)-1:
                    return None, direction
                else:
                    return self.sidebar[sidebar_index+1], direction

        return None, direction

    def move_window_in_direction(self, window, direction):
        target_window, escape_direction = self.get_window_in_direction(window, direction)
        if target_window == window:
            return True, direction
        if not target_window:
            return False, direction

        if target_window == self.main_window:
            sidebar_index = self.sidebar.index(window)
            self.main_window = window
            self.sidebar[sidebar_index] = target_window
        elif window == self.main_window:
            sidebar_index = self.sidebar.index(target_window)
            self.main_window = target_window
            self.sidebar[sidebar_index] = window
        else:
            window_index = self.sidebar.index(window)
            target_index = self.sidebar.index(target_window)

            self.sidebar[window_index] = target_window
            self.sidebar[target_index] = window

        # Update the mru stack to include the window we swapped
        # with, this makes moving back and forth more natural
        self.focus_mru.remove(target_window)
        self.focus_mru.remove(window)
        self.focus_mru.append(target_window)
        self.focus_mru.append(window)

        return True, direction

    def get_drop_slot(self, position, rect):
        h_main_start, h_main_end, h_sidebar_start, h_sidebar_end = self.get_horizontal_positions()

        horiz_split_pos = h_sidebar_end if self.flipped else h_sidebar_start
        force_drop = abs(horiz_split_pos - position[0]) < 100

        if not self.main_window:
            return 0, (position[1] < self.rect.top + 100)

        if ((self.flipped and position[0] < horiz_split_pos)
            or ((not self.flipped and position[0] > horiz_split_pos))):
            sidebar_windows = len(self.sidebar) + 1

            vert_split = int(float(self.rect.height) / float(sidebar_windows))
            drop_index = int((position[1] - self.rect.top) / vert_split)

            return (drop_index+1), force_drop
        else:
            return 0, force_drop

    def get_focus_window_after_removing(self, window_before_remove):
        if window_before_remove == self.main_window:
            if self.sidebar:
                return self.sidebar[0]
            else:
                return None
        else:
            sidebar_index = self.sidebar.index(window_before_remove)
            if sidebar_index == 0:
                if len(self.sidebar) >= 2:
                    return self.sidebar[1]
                else:
                    return self.main_window
            else:
                return self.sidebar[sidebar_index-1]

    def takeover_from_layout(self, other_layout):
        if isinstance(other_layout, SidebarLayout):
            self.main_window = other_layout.main_window
            self.sidebar = other_layout.sidebar
            return True
        return False

    def takeover_from_windows(self, window_list):
        if window_list:
            self.main_window = window_list[-1]
            self.sidebar = []

            for window in window_list[:-1]:
                drop_slot, force_drop = self.get_drop_slot(window.rect.center, window.rect)
                if drop_slot == 0:
                    drop_slot = 1
                self.add_window(window, at_slot=drop_slot)

        return True