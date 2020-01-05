from pylewm.rects import Rect
from pylewm.commands import PyleInit, PyleCommand
from pylewm.space import Space
from pylewm.layout import Direction

import ctypes
import win32api, win32con

Monitors = []
DesktopArea = Rect()

class Monitor:
    def __init__(self, info):
        self.info = info
        self.rect = Rect(info['Monitor'])

        self.spaces = [Space(self, self.rect), Space(self, self.rect)]
        self.last_used_space = None

        self.temp_spaces = []
        self.last_used_temp_space = None

        self.visible_space = self.spaces[0]
        self.visible_space.visible = True

    def switch_to_space(self, new_space):
        if new_space == self.visible_space:
            return

        self.visible_space.hide()

        if self.visible_space.temporary and len(self.visible_space.windows) == 0:
            # Delete hidden temporary spaces with no windows
            self.remove_temp_space(self.visible_space)

        self.visible_space = new_space
        new_space.show()

        if new_space.temporary:
            # Record which temporary space we were viewing last
            self.last_used_temp_space = new_space
        else:
            # Record which primary space we were viewing last
            self.last_used_space = new_space

    def new_temp_space(self):
        temp_space = Space(self, self.rect)
        temp_space.temporary = True
        self.temp_spaces.append(temp_space)
        return temp_space

    def remove_temp_space(self, temp_space):
        self.temp_spaces.remove(temp_space)
        if self.last_used_temp_space == temp_space:
            if len(self.temp_spaces) != 0:
                self.last_used_temp_space = self.temp_spaces[0]
            else:
                self.last_used_temp_space = None

    def get_last_used_temp_space(self):
        if self.last_used_temp_space:
            return self.last_used_temp_space
        elif len(self.temp_spaces) != 0:
            return self.temp_spaces[0]
        else:
            return None

    def get_adjacent_temp_space(self, temp_space, direction):
        assert temp_space in self.temp_spaces
        old_index = self.temp_spaces.index(temp_space)
        new_index = (old_index + direction + len(self.temp_spaces)) % len(self.temp_spaces)

        # There is always an empty temporary space at the end of the list of
        # temporary spaces. But only if you're going forward
        if old_index == len(self.temp_spaces) - 1 and direction > 0:
            if len(temp_space.windows) > 0:
                return self.new_temp_space()

        return self.temp_spaces[new_index]
    
def get_default_monitor():
    return Monitors[0]

def get_monitor_at(position):
    for monitor in Monitors:
        if monitor.rect.contains(position):
            return monitor
    return None

def get_covering_monitor(rect):
    monitor = rect.get_most_overlapping(Monitors, lambda mon: mon.rect)
    if monitor:
        return monitor
    return Monitors[0]

def get_monitor_in_direction(from_monitor, direction):
    return from_monitor.rect.get_closest_in_direction(
        direction,
        [m for m in Monitors if m != from_monitor],
        lambda m: m.rect,
        DesktopArea
    )

@PyleInit
def initMonitors():
    for mhnd in win32api.EnumDisplayMonitors(None, None):
        info = win32api.GetMonitorInfo(mhnd[0])
        monitor = Monitor(info)
        DesktopArea.extend_to_cover(monitor.rect)
        Monitors.append(monitor)

    # Sort monitors by position so their order stays the same
    Monitors.sort(key=lambda x: x.rect.left)

    for i, monitor in enumerate(Monitors):
        print(f"Monitor {i}: {monitor.rect}")