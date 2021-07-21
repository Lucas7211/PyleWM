import pylewm.filters
import pylewm.monitors
from pylewm.rects import Rect

from pylewm.winproxy.windowproxy import WindowProxy, WindowInfo, WindowProxyLock
from pylewm.window_classification import WindowState, classify_window

import time

class Window:
    InInitialPlacement = True
    
    def __init__(self, proxy : WindowProxy):
        self.proxy = proxy
        self.window_info = WindowInfo()
        self.state = WindowState.Unknown
        self.space = None
        self.closed = False

        self.wm_hidden = False
        self.wm_becoming_visible = False
        self.wm_visible_since = 0
        
        self.applied_filters = False

        self.update_info_from_proxy()
        self.layout_position = self.real_position

        self.classify()

    def classify(self):
        new_state, reason = classify_window(self)
        if new_state != self.state:
            self.state = new_state
            self.proxy.ignored = (self.state == WindowState.IgnorePermanent)

            if self.state == WindowState.Floating:
                self.make_floating()
            elif self.state == WindowState.Tiled:
                self.make_tiled()

    def make_floating(self):
        self.state = WindowState.Floating
        self.proxy.set_always_on_top(True)

        if self.space:
            self.space.remove_window(self)

    def make_tiled(self):
        self.state = WindowState.Tiled
        self.proxy.set_always_on_top(False)

    def is_ignored(self):
        return self.state == WindowState.IgnorePermanent or self.state == WindowState.IgnoreTemporary

    def is_tiled(self):
        return self.state == WindowState.Tiled

    def is_floating(self):
        return self.state == WindowState.Floating

    def is_interactable(self):
        if not self.window_info.visible:
            return False
        if self.window_info.cloaked:
            return False
        if self.window_info.is_minimized():
            return False
        return True

    def show(self):
        self.wm_hidden = False
        self.wm_becoming_visible = True
        self.wm_visible_since = time.time()
        self.proxy.show()

    def show_with_rect(self, new_rect):
        self.wm_hidden = False
        self.wm_becoming_visible = True
        self.proxy.show_with_rect(new_rect)

    def hide(self):
        self.wm_hidden = True
        self.wm_becoming_visible = False
        self.proxy.hide()

    def close(self):
        self.closed = True
        if self.space:
            self.space.remove_window(self)
        self.proxy.close()

    def minimize(self):
        self.proxy.minimize()

    def poke(self):
        self.proxy.poke()

    def wm_visible_duration(self):
        return time.time() - self.wm_visible_since

    def can_move(self):
        """ Whether this window can be moved within the layout or between spaces. """
        return self.is_tiled() and not self.window_info.is_hung

    def update(self):
        # Classify the window if we haven't classified it yet
        if self.state == WindowState.IgnorePermanent or self.closed:
            return

        # Update window info from the proxy if it's been changed
        if self.proxy.changed:
            self.update_info_from_proxy()

        # Try to classify again if temporarily ignored
        if self.state == WindowState.IgnoreTemporary or self.state == WindowState.Unknown:
            self.classify()
            if self.is_ignored():
                return

        # Make sure we've applied all filters
        if not self.applied_filters:
            self.apply_filters()

        # Don't do any window management if we've hidden the window ourselves
        if self.wm_hidden:
            return
        if Window.InInitialPlacement:
            return

        # Wait for the window to become visible
        if self.wm_becoming_visible:
            if self.window_info.visible:
                self.wm_becoming_visible = False
            else:
                return

        if self.state == WindowState.Tiled:
            if self.is_interactable():
                # Place in layout if not detected before
                if not self.space and not self.wm_hidden:
                    self.auto_place_into_space()
            else:
                # Remove from layout if no longer interactable
                if self.space and self.space.visible and self.wm_visible_duration() > 0.05:
                    self.space.remove_window(self)

    def apply_filters(self):
        self.applied_filters = True
        pylewm.filters.trigger_all_filters(self, post=False)

        # We place into a space before we trigger post filters
        if not self.space and self.state == WindowState.Tiled:
            self.auto_place_into_space(initial_space=True)

        if not Window.InInitialPlacement:
            pylewm.filters.trigger_all_filters(self, post=True)

    def auto_place_into_space(self, initial_space=False):
        space = None
        slot = None

        filter_monitor = pylewm.filters.get_monitor(self)
        if filter_monitor is not None and (Window.InInitialPlacement or initial_space):
            filter_monitor = min(filter_monitor, len(pylewm.monitors.Monitors)-1)
            space = pylewm.monitors.Monitors[filter_monitor].visible_space
        elif Window.InInitialPlacement or not initial_space:
            monitor = pylewm.monitors.get_covering_monitor(self.real_position)
            space = monitor.visible_space
            slot, force_drop = space.get_drop_slot(self.real_position.center, self.real_position)
        else:
            space = pylewm.focus.get_cursor_space()

        if Window.InInitialPlacement:
            space.initial_windows.append(self)
        else:
            space.add_window(self, at_slot=slot)

    def update_info_from_proxy(self):
        with WindowProxyLock:
            self.window_info.set(self.proxy.window_info)
            self.proxy.changed = False

    @property
    def real_position(self):
        return self.window_info.rect

    def set_layout(self, new_position : Rect):
        if new_position.equals(self.layout_position):
            return
        self.layout_position.assign(new_position)
        self.proxy.set_layout(new_position)

    @property
    def window_title(self):
        return self.window_info.window_title

    @property
    def window_class(self):
        return self.window_info.window_class

    def __str__(self):
        return f"{{ {self.window_title} | {self.window_class} @{self.proxy._hwnd} }}"

WindowsByProxy : dict[WindowProxy, Window] = dict()

def on_proxy_added(proxy):
    window = Window(proxy)
    WindowsByProxy[proxy] = window

def on_proxy_removed(proxy):
    if proxy not in WindowsByProxy:
        return

    window = WindowsByProxy[proxy]
    window.closed = True
    if window.space:
        window.space.remove_window(window)

    del WindowsByProxy[proxy]

def get_window(proxy):
    if proxy in WindowsByProxy:
        return WindowsByProxy[proxy]
    else:
        return None