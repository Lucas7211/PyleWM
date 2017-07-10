from pylewm import pyleinit, pylecommand
import win32gui, win32con, win32api

Monitors = []
DesktopArea = [0,0,0,0]

@pyleinit
def initMonitors():
    for mhnd in win32api.EnumDisplayMonitors(None, None):
        monitor = win32api.GetMonitorInfo(mhnd[0])
        DesktopArea[0] = min(DesktopArea[0], monitor['Monitor'][0])
        DesktopArea[1] = min(DesktopArea[1], monitor['Monitor'][1])
        DesktopArea[2] = max(DesktopArea[2], monitor['Monitor'][2])
        DesktopArea[3] = max(DesktopArea[3], monitor['Monitor'][3])
        Monitors.append(monitor)