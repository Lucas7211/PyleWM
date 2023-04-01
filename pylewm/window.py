import pylewm.filters
import pylewm.monitors
import pylewm.focus
from pylewm.rects import Rect

from pylewm.hotkeys import MouseState
from pylewm.winproxy.windowproxy import WindowProxy, WindowInfo, WindowProxyLock
from pylewm.window_classification import WindowState, classify_window

import time

class Window:
    InInitialPlacement = True
    DraggingWindow = None
    Taskbars : list['Window'] = []
    WindowCounter = 0
    
    def __init__(self, proxy : WindowProxy):
        self.proxy = proxy
        self.window_info = WindowInfo()
        self.state = WindowState.Unknown
        self.space = None
        self.closed = False
        self.can_drop_tiled = False
        self.force_always_top = False
        self.is_dropdown = False
        self.is_zoomed = False
        self.is_taskbar = False

        self.serial_counter = Window.WindowCounter
        Window.WindowCounter += 1

        self.wm_hidden = False
        self.wm_becoming_visible = False
        self.wm_visible_since = 0
        self.trigger_relayout = False
        
        self.applied_filters = False

        self.update_info_from_proxy()
        self.layout_position = self.real_position.copy()
        self.layout_margin = None
        self.floating_rect = self.real_position.copy()

        self.dragging = False
        self.ignore_drag_until = 0.0
        self.drag_ticks_with_movement = 0
        self.drag_ticks_since_start = 0
        self.drag_ticks_since_last_movement = 0
        self.drag_last_pos = self.real_position.copy()

        self.drop_space = None
        self.drop_slot = None
        self.drop_ticks_inside_slot = 0

        self.classify()

        if self.window_class.lower() == "shell_traywnd":
            self.is_taskbar = True
            Window.Taskbars.append(self)

    def classify(self):
        new_state, reason = classify_window(self)
        if new_state != self.state:
            self.state = new_state
            self.proxy.permanent_ignore = (self.state == WindowState.IgnorePermanent)
            self.proxy.temporary_ignore = (self.state == WindowState.IgnoreTemporary)

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
        self.layout_position = Rect()
        self.proxy.set_always_on_top(self.force_always_top)
        self.can_drop_tiled = True

        if self.window_info.is_maximized():
            self.remove_maximized()

    def ensure_tiled_for_move(self):
        if self.window_info.is_hung:
            return
        if self.state == WindowState.IgnorePermanent:
            return
        if self.is_taskbar:
            return
        if not self.is_tiled():
            self.make_tiled()
            self.auto_place_into_space()
            if self.space and self.space.layout:
                self.space.layout.update_layout()
        if self.is_zoomed:
            self.is_zoomed = False

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
        self.stop_drag()

    def close(self):
        self.closed = True
        if self.space:
            self.space.remove_window(self)
        self.proxy.close()

    def minimize(self):
        self.proxy.minimize()

    def restore(self):
        self.proxy.restore()

    def remove_maximized(self):
        self.proxy.remove_maximized()

    def poke(self):
        self.proxy.poke()

    def wm_visible_duration(self):
        return time.time() - self.wm_visible_since

    def can_move(self):
        """ Whether this window can be moved within the layout or between spaces. """
        return self.is_tiled() and not self.window_info.is_hung

    def is_hung(self):
        return self.window_info.is_hung

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
        elif self.is_ignored():
            return

        # Make sure we've applied all filters
        if not self.applied_filters:
            self.apply_filters()

            # Newly created windows might trigger a new window function
            global NextWindowFunctions
            WindowFunctions = NextWindowFunctions
            NextWindowFunctions = []
            for fun in WindowFunctions:
                fun(self)

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

        # Update what we're doing with dragging
        self.update_drag()

        if self.state == WindowState.Tiled:
            if self.is_interactable():
                # Place in layout if not detected before
                if not self.space and not self.wm_hidden and not Window.InInitialPlacement:
                    self.auto_place_into_space(initial_space=True)

                # Switch to floating mode if the window has been moved by the user
                if self.window_info.is_maximized() or (self.dragging and (self.drag_ticks_with_movement > 2 or (MouseState.LEFT_MOUSE_DOWN and Window.DraggingWindow is self))):
                    self.make_floating()

                # Might need to restore layout if some of the styles have changed
                if self.trigger_relayout:
                    if not self.dragging:
                        self.restore_layout()
                    self.trigger_relayout = False
            else:
                # Remove from layout if no longer interactable
                if self.space and self.space.visible and self.wm_visible_duration() > 0.05:
                    prev_space = self.space
                    self.space.remove_window(self)
                    if pylewm.focus.FocusWindow == self:
                        pylewm.focus.set_focus_space(prev_space)

        elif self.state == WindowState.Floating:
            # Drop into a tiling layout if we can
            if self.dragging or self.drop_space:
                self.update_float_drop()


    def apply_filters(self):
        self.applied_filters = True
        pylewm.filters.trigger_all_filters(self, post=False)

        # We place into a space before we trigger post filters
        if not Window.InInitialPlacement:
            if not self.space and self.state == WindowState.Tiled:
                self.auto_place_into_space(initial_space=True)

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
        prev_border_style = self.window_info.get_border_styles()
        prev_force_visible = self.window_info.is_force_visible

        with WindowProxyLock:
            self.window_info.set(self.proxy.window_info)
            self.proxy.changed = False

        if prev_border_style != self.window_info.get_border_styles() or prev_force_visible != self.window_info.is_force_visible:
            self.trigger_relayout = True

    def stop_drag(self):
        if self.dragging:
            if Window.DraggingWindow is self:
                Window.DraggingWindow = None
            self.dragging = False

    def update_drag(self):
        if not self.is_interactable():
            if self.dragging:
                self.stop_drag()
            return

        new_rect = self.real_position
        if self.ignore_drag_until > time.time():
            self.drag_last_pos.assign(new_rect)
            self.dragging = False
            self.remove_drop_space()
            return

        # Some rudimentary tracking for when windows are being dragged
        if not new_rect.equals(self.drag_last_pos):
            if self.dragging:
                self.drag_ticks_since_last_movement = 0
                self.drag_ticks_since_start += 1
                self.drag_ticks_with_movement += 1
            else:
                self.dragging = True

                if Window.DraggingWindow is None and MouseState.LEFT_MOUSE_DOWN:
                    Window.DraggingWindow = self

                self.drag_ticks_since_last_movement = 0
                self.drag_ticks_since_start = 1
                self.drag_ticks_with_movement = 1
        else:
            if self.dragging:
                self.drag_ticks_since_start += 1
                self.drag_ticks_since_last_movement += 1

                if Window.DraggingWindow is None and MouseState.LEFT_MOUSE_DOWN:
                    Window.DraggingWindow = self

                if not MouseState.LEFT_MOUSE_DOWN or Window.DraggingWindow is not self:
                    self.dragging = False
                    if Window.DraggingWindow is self:
                        Window.DraggingWindow = None

                    if self.is_tiled():
                        self.restore_layout()

        self.drag_last_pos.assign(new_rect)
        if self.is_floating():
            self.floating_rect.assign(new_rect)

    def update_float_drop(self):
        if not self.can_drop_tiled:
            return
        if not pylewm.config.AllowDroppingIntoLayout:
            return
        if self.dragging and self.drag_ticks_with_movement > 5:
            hover_space = pylewm.focus.get_cursor_space()
            hover_slot = None
            if hover_space:
                hover_slot, force_drop = hover_space.get_drop_slot(pylewm.focus.get_cursor_position(), self.real_position)

                # Only allow forced drops when drag&dropping
                if not force_drop:
                    hover_slot = None
            
            if hover_slot is not None:
                self.set_drop_space(hover_space, hover_slot)
            else:
                self.remove_drop_space()
        elif not self.dragging and self.drop_space and self.drop_slot is not None and self.drop_ticks_inside_slot >= 3:
            self.ignore_drag_until = time.time() + 0.2
            self.make_tiled()
            self.drop_space.add_window(self, at_slot=self.drop_slot)
            self.remove_drop_space()
        else:
            self.remove_drop_space()

    def set_drop_space(self, new_space, new_slot):
        if self.drop_space == new_space and self.drop_slot == new_slot:
            if self.drop_ticks_inside_slot == 2:
                self.drop_space.set_pending_drop_slot(self.drop_slot)
            self.drop_ticks_inside_slot += 1
        else:
            if self.drop_space:
                self.drop_space.set_pending_drop_slot(None)
            self.drop_space = new_space
            self.drop_slot = new_slot
            self.drop_ticks_inside_slot = 0

    def remove_drop_space(self):
        if self.drop_space:
            self.drop_space.set_pending_drop_slot(None)
        self.drop_ticks_inside_slot = 0
        self.drop_space = None
        self.drop_slot = None

    def remove_titlebar(self):
        self.proxy.remove_titlebar()

    def on_removed(self):
        self.remove_drop_space()
        self.stop_drag()

    @property
    def real_position(self):
        return self.window_info.rect

    def set_layout(self, new_position : Rect, apply_margin = True, edges_flush=None):
        if new_position.equals(self.layout_position):
            return
        if self.is_zoomed:
            return
        self.layout_position.assign(new_position)
        self.ignore_drag_until = time.time() + 0.2

        if apply_margin:
            self.proxy.set_layout(new_position, self.layout_margin, edges_flush)
        else:
            self.proxy.set_layout(new_position, False)

    def restore_layout(self):
        self.proxy.restore_layout()
        self.ignore_drag_until = time.time() + 0.2

    def refresh_layout(self):
        self.layout_position = Rect()
        if self.space:
            self.space.refresh_layout()

    def move_floating_to(self, new_rect : Rect):
        if new_rect.equals(self.real_position):
            return
        self.proxy.move_floating_to(new_rect)

    @property
    def window_title(self):
        return self.window_info.window_title

    @property
    def window_class(self):
        return self.window_info.window_class

    def __str__(self):
        return f"{{ {self.window_title} | {self.window_class} @{self.proxy._hwnd} }}"

WindowsByProxy : dict[WindowProxy, Window] = dict()
NextWindowFunctions = []

def execute_on_next_window(fun):
    global NextWindowFunctions
    NextWindowFunctions.append(fun)

def on_proxy_added(proxy):
    window = Window(proxy)
    WindowsByProxy[proxy] = window
    window.update()

def on_proxy_removed(proxy):
    if proxy not in WindowsByProxy:
        return

    window = WindowsByProxy[proxy]
    window.closed = True
    if window.space:
        window.space.remove_window(window)
    window.on_removed()

    del WindowsByProxy[proxy]

def get_window(proxy):
    if proxy in WindowsByProxy:
        return WindowsByProxy[proxy]
    else:
        return None

def get_windows_at_position(position):
    windows = []
    for proxy, window in WindowsByProxy.items():
        if window.closed:
            continue
        if window.state == WindowState.IgnorePermanent:
            continue
        if window.window_info.cloaked:
            continue
        if window.window_title == "":
            continue
        if window.real_position.height == 0 or window.real_position.width == 0:
            continue
        if window.real_position.contains(position):
            windows.append(window)
    return windows