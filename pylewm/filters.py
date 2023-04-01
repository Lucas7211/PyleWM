import pylewm.selector
import pylewm.config
from pylewm.commands import PyleInit, run_pyle_command

FunctionsByFilter = []
FiltersByFunction = {}

Filters = {}

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

    def trigger(self, window, post=False):
        if post == self.isPost:
            self.fun(window, *self.args, **self.kwargs)

    def __str__(self):
        return str(self.fun)

    def __repr__(self):
        return repr(self.fun)

@Filter
def Floating(window):
    """ Start the window on the floating layer when spawned. """
    pass

@Filter
def Tiling(window):
    """ Do not start the window as floating when spawned. """
    pass

@Filter
def Ignore(window):
    """ Ignore the filtered window completely for window management. """
    pass

@Filter.post
def NoTitlebar(window):
    """ Remove the titlebar from displaying on the window. """
    window.remove_titlebar()

@Filter
def Monitor(window, monitor):
    """ Move the window to a specific monitor when spawned. """
    pass

@Filter
def KeepStartMonitor(window):
    """ Move the window to a specific monitor when spawned. """
    pass

@Filter
def IgnoreBorders(window):
    """ Don't take into account window borders for this window's positioning. """
    window.layout_margin = 0

@Filter
def ForceBorders(window, border_size):
    """ Force this window to have borders of a particular size in positioning. """
    window.layout_margin = border_size

@Filter.post
def TemporarySpace(window):
    """ The window gets a new desktop on its monitor when spawned. """
    pylewm.spaces.move_window_to_new_temporary_space(window)

@Filter.post
def AutoPoke(window):
    window.poke()

@Filter
def AlwaysOnTop(window):
    window.force_always_top = True

def trigger_all_filters(window, post=False):
    for f in FunctionsByFilter:
        if pylewm.selector.matches(window, f[0]):
            for flt in f[1:]:
                flt.trigger(window, post=post)

def is_ignored(window):
    if Ignore in FiltersByFunction:
        return any(pylewm.selector.matches(window, filt[0]) for filt in FiltersByFunction[Ignore])
    return False

def is_floating(window):
    if Floating in FiltersByFunction:
        return any(pylewm.selector.matches(window, filt[0]) for filt in FiltersByFunction[Floating])
    return False

def is_tiling(window):
    if Tiling in FiltersByFunction:
        return any(pylewm.selector.matches(window, filt[0]) for filt in FiltersByFunction[Tiling])
    return False

def get_monitor(window):
    if Monitor in FiltersByFunction:
        for filt in FiltersByFunction[Monitor]:
            if pylewm.selector.matches(window, filt[0]):
                for f in filt[1:]:
                    if f.base is Monitor:
                        if len(f.args) >= 1:
                            return f.args[0]
                return None
    if KeepStartMonitor in FiltersByFunction:
        for filt in FiltersByFunction[KeepStartMonitor]:
            if pylewm.selector.matches(window, filt[0]):
                return pylewm.monitors.get_covering_monitor(window.real_position).monitor_index
    return None

@PyleInit
def init_filters():
    for f in Filters:
        FunctionsByFilter.append(f)
        for func in f[1:]:
            if func.base not in FiltersByFunction:
                FiltersByFunction[func.base] = []
            FiltersByFunction[func.base].append(f)