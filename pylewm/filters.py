import pylewm
import pylewm.selector
import pylewm.windows
import win32api, win32con, win32gui
from functools import partial

FiltersByFunction = {}
FunctionsByFilter = []

class Filter:
    @staticmethod
    def post(fun):
        filt = Filter(fun)
        filt.isPost = True
        return filt

    def __init__(self, fun):
        self.base = self
        self.fun = fun
        self.args = []
        self.kwargs = {}
        self.isPost = False

    def __call__(self, *args, **kwargs):
        inst = Filter(self.fun)
        inst.args = args
        inst.kwargs = kwargs
        inst.base = self
        return inst

    def trigger(self, hwnd, post=False):
        if post == self.isPost:
            self.fun(hwnd, *self.args, **self.kwargs)

    def __str__(self):
        return str(self.fun)

    def __repr__(self):
        return repr(self.fun)

@Filter
def Floating(hwnd):
    """ Start the window on the floating layer when spawned. """
    pass

@Filter
def Tiling(hwnd):
    """ Do not start the window as floating when spawned. """
    pass

@Filter
def Ignore(hwnd):
    """ Ignore the filtered window completely for window management. """
    pass

@Filter
def NoTitlebar(hwnd):
    """ Remove the titlebar from displaying on the window. """
    style = win32api.GetWindowLong(hwnd, win32con.GWL_STYLE)
    if style & win32con.WS_CAPTION:
        style = style & ~win32con.WS_CAPTION
        win32api.SetWindowLong(hwnd, win32con.GWL_STYLE, style)

@Filter
def Position(hwnd, *pos):
    """ Move the window to a specific position when spawned. """
    isRelative = all(isinstance(x, float) and 0 <= x <= 1 for x in pos)

    if not isRelative:
        # Absolute screen position
        print(f"SET TO ABSOLUTE {pos}")
        pylewm.windows.move(hwnd, pos)
    else:
        # Relative position on monitor
        monitorIndex = get_monitor(hwnd)
        if monitorIndex == -1 or monitorIndex >= len(pylewm.monitors.Monitors):
            monitor = pylewm.monitors.getMonitor(win32gui.GetWindowRect(hwnd))
        else:
            monitor = pylewm.monitors.Monitors[monitorIndex]

        monitor_width = monitor.rect[2] - monitor.rect[0]
        monitor_height = monitor.rect[3] - monitor.rect[1]

        newPos = [0,0]
        newPos[0] = int(pos[0] * float(monitor_width)) + monitor.rect[0]
        newPos[1] = int(pos[1] * float(monitor_height)) + monitor.rect[1]

        if len(pos) == 4:
            newPos += [0,0]
            newPos[2] = int(pos[2] * float(monitor_width)) + monitor.rect[0]
            newPos[3] = int(pos[3] * float(monitor_height)) + monitor.rect[1]

        print(f"SET TO RELATIVE {newPos}")

        pylewm.windows.move(hwnd, newPos)
        pylewm.queue(lambda: pylewm.windows.move(hwnd, newPos))

        print(f" HAVE POS {win32gui.GetWindowRect(hwnd)}")

@Filter
def Monitor(hwnd, monitor):
    """ Move the window to a specific monitor when spawned. """
    pass

@Filter.post
def NewDesktop(hwnd):
    """ The window gets a new desktop on its monitor when spawned. """
    pylewm.desktops.new_desktop_with_window(hwnd)

def trigger(hwnd, post=False):
    for f in FunctionsByFilter:
        if pylewm.selector.matches(hwnd, f[0]):
            print("MATCH -- "+repr(f))
            for flt in f[1:]:
                flt.trigger(hwnd, post=post)

def is_ignored(hwnd):
    if Ignore in FiltersByFunction:
        return any(pylewm.selector.matches(hwnd, filt[0]) for filt in FiltersByFunction[Ignore])
    return False

def is_floating(hwnd):
    if Floating in FiltersByFunction:
        return any(pylewm.selector.matches(hwnd, filt[0]) for filt in FiltersByFunction[Floating])
    return False

def is_tiling(hwnd):
    if Tiling in FiltersByFunction:
        return any(pylewm.selector.matches(hwnd, filt[0]) for filt in FiltersByFunction[Tiling])
    return False

def get_monitor(hwnd):
    if Monitor in FiltersByFunction:
        for filt in FiltersByFunction[Monitor]:
            if pylewm.selector.matches(hwnd, filt[0]):
                for f in filt[1:]:
                    if f.base is Monitor:
                        if len(f.args) >= 1:
                            return f.args[0]
                return -1
    return -1

@pylewm.pyleinit
def initFilters():
    for f in pylewm.config["Filters"]:
        FunctionsByFilter.append(f)
        for func in f[1:]:
            if func.base not in FiltersByFunction:
                FiltersByFunction[func.base] = []
            FiltersByFunction[func.base].append(f)

    print("-- FILTERS --")
    print(repr(FunctionsByFilter))
    print(repr(FiltersByFunction))
