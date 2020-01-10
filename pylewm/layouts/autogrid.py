from pylewm.layout import Layout
from pylewm.rects import Rect, Direction

from pylewm.layouts.sidebar import SidebarLayout

import math

class AutoGridLayout(Layout):
    def __init__(self):
        Layout.__init__(self)
        self.columns = []
        self.windows = []
        self.need_reposition = False

    def get_wanted_grid_dimensions(self, window_count):
        columns = math.ceil(math.sqrt(float(window_count)))
        rows = int(math.ceil(window_count / columns))
        return columns, rows

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
        self.need_reposition = True

        wanted_columns, wanted_rows = self.get_wanted_grid_dimensions(len(self.windows))

        if at_slot and at_slot[0] != -1:
            insert_column, insert_slot = at_slot
            if insert_slot == -1 or insert_slot >= len(self.columns[insert_column]):
                self.columns[insert_column].append(window)
            else:
                self.columns[insert_column].insert(insert_slot, window)
        elif len(self.columns) < wanted_columns:
            # If we don't have enough columns, add the window as a new column
            if insert_direction == Direction.Right:
                self.columns.insert(0, [window])
            else:
                self.columns.append([window])
        else:
            # Find the first column that has fewer windows than the amount of rows we want
            candidate_columns = []
            for column_index, column in enumerate(self.columns):
                if len(column) < wanted_rows:
                    candidate_columns.append(column_index)

            insert_column = -1

            # Put it in the candidate column that has focus if we can
            if self.focus:
                focus_column, focus_slot = self.get_window_column(self.focus)
                if focus_column in candidate_columns:
                    insert_column = focus_column

            # Prefer leftmost column if coming in from the left
            if insert_column == -1 and insert_direction == Direction.Right:
                candidate_columns.sort(key = lambda col_index: col_index, reverse=False)
                insert_column = candidate_columns[0]

            # Prefer rightmost column if coming in from the right
            if insert_column == -1 and insert_direction == Direction.Left:
                candidate_columns.sort(key = lambda col_index: col_index, reverse=True)
                insert_column = candidate_columns[0]

            # Put it in the shortest current column
            if insert_column == -1:
                candidate_columns.sort(key = lambda col_index: len(self.columns[col_index]), reverse=True)
                insert_column = candidate_columns[0]

            # Final fallback, should only happen if inserting additional windows from a direction
            if insert_column == -1:
                if insert_direction == Direction.Right:
                    insert_column = 0
                else:
                    insert_column = len(self.columns)-1

            if insert_direction == Direction.Down or insert_direction == Direction.Next:
                self.columns[insert_column].insert(0, window)
            else:
                self.columns[insert_column].append(window)

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

    def move_window_to_column(self, window, to_column_index):
        wanted_columns, wanted_rows = self.get_wanted_grid_dimensions(len(self.windows))
        from_column_index, from_slot_index = self.get_window_column(window)
        target_window = self.select_mru_span_window(to_column_index, window.rect.top, window.rect.bottom)
        target_column, target_slot = self.get_window_column(target_window)

        if (len(self.columns[target_column]) < len(self.columns[from_column_index])
            or len(self.columns) > wanted_columns):
            # Move the window from the larger column to the smaller column
            if window.rect.center[1] >= target_window.rect.center[1]:
                target_slot += 1
            self.columns[target_column].insert(target_slot, window)
            self.columns[from_column_index].remove(window)
            if not self.columns[from_column_index]:
                del self.columns[from_column_index]
        else:
            # Swap columns with the target window
            self.columns[target_column][target_slot] = window
            self.columns[from_column_index][from_slot_index] = target_window

    def move_window_in_direction(self, window, direction):
        window_column, window_slot = self.get_window_column(window)
        column_length = len(self.columns[window_column])
        wanted_columns, wanted_rows = self.get_wanted_grid_dimensions(len(self.windows))
        self.need_reposition = True

        if direction == Direction.Left:
            if window_column == 0:
                if len(self.columns) >= wanted_columns:
                    return False, direction
                else:
                    self.columns[window_column].remove(window)
                    self.columns.insert(0, [window])
                    return True, direction
            self.move_window_to_column(window, window_column-1)
            return True, direction
        elif direction == Direction.Right:
            if window_column == len(self.columns)-1:
                if len(self.columns) >= wanted_columns:
                    return False, direction
                else:
                    self.columns[window_column].remove(window)
                    self.columns.append([window])
                    return True, direction
            self.move_window_to_column(window, window_column+1)
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

    def get_drop_slot(self, position, rect, fake_window_count=-1):
        window_count = len(self.windows) + 1
        if fake_window_count != -1:
            window_count = fake_window_count

        wanted_columns, wanted_rows = self.get_wanted_grid_dimensions(window_count)
        if len(self.columns) < wanted_columns:
            # Never insert into an existing column if we want more columns to begin with
            return None, False

        column_count = len(self.columns)
        if column_count == 0:
            return None, False

        column_splits = self.get_column_splits()
        for column_index in range(0, column_count):
            # Check if the position is within this column
            if position[0] < column_splits[column_index]:
                continue
            if position[0] > column_splits[column_index+1]:
                continue

            # Only allow insertion into this column if the column is short of wanted height
            if len(self.columns[column_index]) >= wanted_rows:
                continue

            # If the column is empty always drop into it
            slot_count = len(self.columns[column_index])
            if slot_count == 0:
                return (column_index, 0), False

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
            return self.columns[window_column-1][0]
        elif window_column+1 < len(self.columns):
            return self.columns[window_column+1][0]
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
        if not window_list:
            return True

        window_count = len(window_list)
        column_count, row_count = self.get_wanted_grid_dimensions(window_count)

        # Create empty columns to fill with windows
        self.columns = []
        for i in range(0, column_count):
            self.columns.append([])

        # Put windows in the most appropriate positions
        for window in window_list:
            drop_slot, force_drop = self.get_drop_slot(window.rect.center, window.rect, fake_window_count=window_count)
            self.add_window(window, at_slot=drop_slot)

        # Remove columns that didn't get any windows
        for i in range(0, column_count):
            if not self.columns[i]:
                del self.columns[i]

        return True