from pylewm.layout import Layout
from pylewm.rects import Rect, Direction

from pylewm.layouts.sidebar import SidebarLayout

class ColumnsLayout(Layout):
    def __init__(self):
        Layout.__init__(self)
        self.columns = []
        self.windows = []
        self.need_reposition = False

    def get_window_column(self, window):
        for column_index, column in enumerate(self.columns):
            if window in column:
                return column_index, column.index(window)
        return -1, -1

    def get_column_window(self, slot):
        if slot[0] == -1 or slot[0] >= len(self.columns):
            return None
        column = self.columns[slot[0]]
        if slot[1] == -1 or slot[1] >= len(column):
            return None
        return column[slot[1]]

    def get_mru_index_in_column(self, column_index):
        for window in reversed(self.focus_mru):
            if window not in self.columns[column_index]:
                continue
            index = self.columns[column_index].index(window)
            return index
        return 0

    def get_last_focus_column(self):
        for window in reversed(self.focus_mru):
            for column_index, column in enumerate(self.columns):
                if window not in column:
                    continue
                slot_index = column.index(window)
                return column_index, slot_index
        return -1, -1

    def select_mru_span_window(self, column_index, pos_top, pos_bottom):
        candidates = []
        for window in self.columns[column_index]:
            if pos_top < window.rect.bottom and window.rect.top < pos_bottom:
                candidates.append(window)

        for window in reversed(self.focus_mru):
            if window in candidates:
                return window
            
        return None

    def add_window(self, window, at_slot=None, insert_direction=None):
        self.windows.append(window)

        #print(f"* Layout {window.window_title} {repr(at_slot)} {insert_direction}")
        if not self.columns:
            # First window goes into new column
            self.columns.append([window])
            #print("First Window")
        elif len(self.windows) == 2:
            # Second window always goes into a new column to the side
            if insert_direction == Direction.Right:
                #print("Second Window Left")
                self.columns.insert(0, [window])
            else:
                #print("Second Window Right")
                self.columns.append([window])
        else:
            insert_column = -1
            insert_slot = -1

            if at_slot and at_slot[0] != -1:
                # Insert before the slot we received
                insert_column, insert_slot = at_slot
                #print(f"Insert at Slot {insert_column}, {insert_slot}")
            elif self.focus:
                # Insert after our current focus window
                insert_column, insert_slot = self.get_window_column(self.focus)
                insert_slot += 1
                #print(f"Insert After Focus {insert_column}, {insert_slot}")
            elif insert_direction == Direction.Right:
                # Insert on a new leftmost column
                #print(f"Insert Leftmost {insert_column}, {insert_slot}")
                self.columns.insert(0, [])
                insert_column = 0
                insert_slot = 0
            elif insert_direction == Direction.Left:
                # Insert on a new rightmost column
                #print(f"Insert Rightmost {insert_column}, {insert_slot}")
                self.columns.append([])
                insert_column = len(self.columns) - 1
                insert_slot = 0
            else:
                # Insert into the previous column that had focus
                insert_column, insert_slot = self.get_last_focus_column()
                if insert_direction == Direction.Down or insert_direction == Direction.Next:
                    insert_slot = 0
                else:
                    insert_slot = -1
                #print(f"Insert Last Focus {insert_column}, {insert_slot}")

            if insert_slot == -1 or insert_slot >= len(self.columns[insert_column]):
                self.columns[insert_column].append(window)
            else:
                self.columns[insert_column].insert(insert_slot, window)

        self.need_reposition = True

    def remove_window(self, window):
        self.windows.remove(window)

        for column in self.columns:
            if window in column:
                column.remove(window)
                if len(column) == 0:
                    self.columns.remove(column)

        self.need_reposition = True

    def get_window_in_direction(self, from_window, direction):
        if not from_window:
            if not self.columns:
                return None, direction
            elif direction == Direction.Right:
                return self.columns[0][self.get_mru_index_in_column(0)], direction
            elif direction == Direction.Left:
                return self.columns[-1][self.get_mru_index_in_column(-1)], direction
            elif direction == Direction.Down or direction == Direction.Next:
                last_column, last_slot = self.get_last_focus_column()
                return self.columns[last_column][0], direction
            elif direction == Direction.Up or direction == Direction.Previous:
                last_column, last_slot = self.get_last_focus_column()
                return self.columns[last_column][-1], direction
            return None, direction

        window_column, window_slot = self.get_window_column(from_window)
        column_length = len(self.columns[window_column])

        if direction == Direction.Left:
            if window_column == 0:
                return None, direction

            target_window = self.select_mru_span_window(window_column-1, from_window.rect.top, from_window.rect.bottom)
            return target_window, direction
        elif direction == Direction.Right:
            if window_column == len(self.columns)-1:
                return None, direction

            target_window = self.select_mru_span_window(window_column+1, from_window.rect.top, from_window.rect.bottom)
            return target_window, direction
        elif direction == Direction.Next:
            new_slot = (window_slot + 1) % column_length
            return self.columns[window_column][new_slot], direction
        elif direction == Direction.Previous:
            new_slot = (window_slot - 1 + column_length) % column_length
            return self.columns[window_column][new_slot], direction
        elif direction == Direction.Down:
            if (window_slot+1) < column_length:
                return self.columns[window_column][window_slot+1], direction
            else:
                return None, direction
        elif direction == Direction.Up:
            if window_slot > 0:
                return self.columns[window_column][window_slot-1], direction
            else:
                return None, direction

        return None, direction

    def move_window_in_direction(self, window, direction):
        window_column, window_slot = self.get_window_column(window)
        column_length = len(self.columns[window_column])
        self.need_reposition = True

        if direction == Direction.Left:
            if window_column == 0:
                if column_length == 1:
                    return False, direction
                else:
                    self.columns[window_column].remove(window)
                    self.columns.insert(0, [window])
                    return True, direction

            target_window = self.select_mru_span_window(window_column-1, window.rect.top, window.rect.bottom)
            target_column, target_slot = self.get_window_column(target_window)
            if window.rect.center[1] >= target_window.rect.center[1]:
                target_slot += 1

            self.columns[target_column].insert(target_slot, window)

            self.columns[window_column].remove(window)
            if not self.columns[window_column]:
                del self.columns[window_column]

            return True, direction
        elif direction == Direction.Right:
            if window_column == len(self.columns)-1:
                if column_length == 1:
                    return False, direction
                else:
                    self.columns[window_column].remove(window)
                    self.columns.append([window])
                    return True, direction

            target_window = self.select_mru_span_window(window_column+1, window.rect.top, window.rect.bottom)
            target_column, target_slot = self.get_window_column(target_window)
            if window.rect.center[1] >= target_window.rect.center[1]:
                target_slot += 1
            self.columns[target_column].insert(target_slot, window)

            self.columns[window_column].remove(window)
            if not self.columns[window_column]:
                del self.columns[window_column]

            return True, direction
        elif direction == Direction.Next:
            new_slot = (window_slot + 1) % column_length
            other_window = self.columns[window_column][new_slot]

            self.columns[window_column][window_slot] = other_window
            self.columns[window_column][new_slot] = window
            return True, direction
        elif direction == Direction.Previous:
            new_slot = (window_slot - 1 + column_length) % column_length
            other_window = self.columns[window_column][new_slot]

            self.columns[window_column][window_slot] = other_window
            self.columns[window_column][new_slot] = window
            return True, direction
        elif direction == Direction.Down:
            if (window_slot+1) < column_length:
                new_slot = window_slot + 1
                other_window = self.columns[window_column][new_slot]

                self.columns[window_column][window_slot] = other_window
                self.columns[window_column][new_slot] = window
                return True, direction
            else:
                return None, direction
        elif direction == Direction.Up:
            if window_slot > 0:
                new_slot = window_slot - 1
                other_window = self.columns[window_column][new_slot]

                self.columns[window_column][window_slot] = other_window
                self.columns[window_column][new_slot] = window
                return True, direction
            else:
                return False, direction

        return False, direction

    def get_drop_slot(self, position, rect):
        column_count = len(self.columns)
        if column_count == 0:
            return None, False

        column_splits = self.get_column_splits()
        for column_index in range(0, column_count):
            if position[0] < column_splits[column_index]:
                continue
            if position[0] > column_splits[column_index+1]:
                continue

            slot_count = len(self.columns[column_index])
            slot_splits = self.get_slot_splits(column_index)
            for slot_index in range(0, slot_count):
                slot_start = slot_splits[slot_index]
                slot_end = slot_splits[slot_index+1]

                if position[1] < slot_start:
                    continue
                if position[1] > slot_end:
                    continue

                slot_center = (slot_start + slot_end) / 2

                if position[1] > slot_center:
                    return (column_index, slot_index+1), False
                else:
                    return (column_index, slot_index), False
        return None, False

    def get_focus_window_after_removing(self, window_before_remove):
        window_column, window_slot = self.get_window_column(window_before_remove)
        if window_slot > 0:
            return self.columns[window_column][window_slot-1]
        elif window_slot+1 < len(self.columns[window_column]):
            return self.columns[window_column][window_slot+1]
        elif window_column > 0:
            return self.columns[window_column-1][self.get_mru_index_in_column(window_column-1)]
        elif window_column+1 < len(self.columns):
            return self.columns[window_column+1][self.get_mru_index_in_column(window_column+1)]
        return None

    def get_column_splits(self):
        column_count = len(self.columns)
        column_width = int(float(self.rect.width) / float(column_count))
        column_splits = []
        for i in range(0, column_count):
            column_splits.append(self.rect.left + (column_width * i))
        column_splits.append(self.rect.right)
        return column_splits

    def get_slot_splits(self, column_index):
        slot_count = len(self.columns[column_index])
        slot_height = int(float(self.rect.height) / float(slot_count))
        slot_splits = []
        for i in range(0, slot_count):
            slot_splits.append(self.rect.top + (slot_height * i))
        slot_splits.append(self.rect.bottom)
        return slot_splits

    def update_layout(self):
        if not self.windows:
            return

        # Update all window positions
        if self.need_reposition:
            self.need_reposition = False
            columns = len(self.columns)
            column_splits = self.get_column_splits()

            for column_index, column in enumerate(self.columns):
                slot_splits = self.get_slot_splits(column_index)

                for slot_index, window in enumerate(column):
                    window.rect.coordinates = (
                        column_splits[column_index],
                        slot_splits[slot_index],
                        column_splits[column_index+1],
                        slot_splits[slot_index+1],
                    )

    def takeover_from_layout(self, old_layout):
        self.need_reposition = True

        if isinstance(old_layout, SidebarLayout):
            if not old_layout.main_window:
                return True

            new_windows = [old_layout.main_window]
            new_windows += old_layout.sidebar
            return self.takeover_from_windows(new_windows)
        return False

    def takeover_from_windows(self, window_list):
        self.windows = list(window_list)
        column_count = 1
        window_count = len(self.windows)

        if window_count >= 5:
            column_count = 3
        elif window_count >= 2:
            column_count = 2

        self.columns = []
        for i in range(0, column_count):
            self.columns.append([])

        windows_per_column = window_count / column_count
        for window_index, window in enumerate(self.windows):
            column_index = int(window_index / windows_per_column)
            self.columns[column_index].append(window)

        return True