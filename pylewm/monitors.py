from pylewm import pyleinit, pylecommand
import win32gui, win32con, win32api

import pylewm.rects
import pylewm.focus

Monitors = []
DesktopArea = [0,0,0,0]

class Monitor:
    def __init__(self, info):
        self.info = info
        self.rect = info['Monitor']
        self.desktops = []

def getMonitor(forPos):
    if len(forPos) == 4:
        return pylewm.rects.getMostOverlapping(forPos, Monitors, lambda mon: mon.rect)
    elif len(forPos) == 2:
        for mon in Monitors:
            if mon.rect[0] <= forPos[0] and mon.rect[2] >= forPos[0] \
                    and mon.rect[1] <= forPos[1] and mon.rect[3] >= forPos[1]:
                return mon
    return None

def getMonitorInDirection(forPos, dir):
    forMonitor = getMonitor(forPos)

    return pylewm.rects.getClosestInDirection(dir, forMonitor.rect,
        Monitors, lambda mon: mon.rect, wrap=True,
        ignore=forMonitor)

@pyleinit
def initMonitors():
    for mhnd in win32api.EnumDisplayMonitors(None, None):
        info = win32api.GetMonitorInfo(mhnd[0])
        monitor = Monitor(info)
        DesktopArea[0] = min(DesktopArea[0], info['Monitor'][0])
        DesktopArea[1] = min(DesktopArea[1], info['Monitor'][1])
        DesktopArea[2] = max(DesktopArea[2], info['Monitor'][2])
        DesktopArea[3] = max(DesktopArea[3], info['Monitor'][3])
        Monitors.append(monitor)
    pylewm.rects.DesktopArea = DesktopArea
