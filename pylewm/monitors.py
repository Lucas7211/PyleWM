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
        self.temp_spaces = []

        self.visible_space = self.spaces[0]
        self.visible_space.visible = True
    
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