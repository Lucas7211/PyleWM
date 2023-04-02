import pylewm.focus
import pylewm.execution
import pylewm.window
import pylewm.headers
import pylewm.colors
import pylewm.commands
from pylewm.commands import PyleCommand, PyleTask
import pylewm.winproxy.winfuncs
import time

PendingTabGroup : 'TabGroup' = None
PendingTabTime = 0.0

class TabGroup:
    NextTabGroupId = 0
    TabGroups = {}

    def __init__(self):
        TabGroup.NextTabGroupId += 1
        self.group_id = TabGroup.NextTabGroupId
        self.header : pylewm.headers.WindowHeader = None
        self.valid = True

        self.windows : list[pylewm.window.Window] = []
        self.visible_window : pylewm.window.Window = None
        TabGroup.TabGroups[self.group_id] = self

    def create_header(self):
        self.header = pylewm.headers.WindowHeader(self.group_id, self.visible_window.proxy._hwnd)
        self.update_header()

    def update_header(self):
        if not self.header:
            return

        state = {
            "pending": (PendingTabGroup == self),
        }
        entries = []
        for window in self.windows:
            bg_color = pylewm.colors.get_random_color_for_str_hsv(window.window_class)

            if window != self.visible_window:
                bg_color[1] *= 0.4
                bg_color[2] *= 0.4

            bg_color = pylewm.colors.hsv_to_rgb(bg_color)
            text_color = pylewm.colors.get_text_color_for_background(bg_color)

            entries.append({
                "title": window.window_title,
                "bg_color": bg_color,
                "text_color": text_color,
                "visible": window == self.visible_window,
            })

        self.header.update(self.visible_window.proxy._hwnd, entries, state)

    def handle_response(self, cmd):
        action = cmd[0]

        if action == "click":
            button = cmd[1]
            entry_index = cmd[2]

            if button == 0:
                if entry_index < len(self.windows):
                    self.switch_to_tab(self.windows[entry_index])
                    pylewm.focus.set_focus_no_mouse(self.visible_window)
            elif button == 1:
                if entry_index < len(self.windows):
                    self.windows[entry_index].close()
            elif button == 2:
                if entry_index < len(self.windows):
                    window = self.windows[entry_index]
                    self.remove_window(window, change_focus=False)
                    window.show()

    def destroy(self):
        if not self.valid:
            return

        for window in self.windows:
            window.set_tab_group(None)
            if not window.closed:
                window.show()

        if self.header:
            self.header.close()
            self.header = None

        global PendingTabGroup
        if PendingTabGroup == self:
            PendingTabGroup = None

        self.valid = False
        del TabGroup.TabGroups[self.group_id]

    def add_window(self, window : 'pylewm.window.Window', hide_previous=True):
        if window.tab_group:
            assert window.tab_group != self

            # Steal the windows from the tab group we're merging
            new_windows = window.tab_group.windows
            window.tab_group.windows = []
            window.tab_group.destroy()

            for new_window in new_windows:
                self.windows.append(new_window)
                new_window.set_tab_group(self)
        else:
            self.windows.append(window)
            window.set_tab_group(self)

        if window.window_info.visible or window.wm_becoming_visible:
            self.switch_to_tab(window, hide_previous=hide_previous)
        else:
            window.hide()

        if not self.header:
            self.create_header()
        
    def remove_window(self, window : 'pylewm.window.Window', change_focus=True):
        index = self.windows.index(window)
        self.windows.remove(window)
        window.set_tab_group(None)

        if len(self.windows) == 0:
            # Tab group is fully dead
            self.destroy()
        elif len(self.windows) == 1:
            # Removed the last window from the tab group, kill the tab group but keep the window
            if window == self.visible_window:
                self.switch_to_tab(self.windows[0], hide_previous=False)
                if pylewm.focus.was_just_focused(window) and change_focus:
                    pylewm.focus.set_focus_no_mouse(self.visible_window)
            self.destroy()
        else:
            if window == self.visible_window:
                self.switch_to_tab(self.windows[min(index, len(self.windows)-1)], hide_previous=False)
                if pylewm.focus.was_just_focused(window) and change_focus:
                    pylewm.focus.set_focus_no_mouse(self.visible_window)
            self.update_header()

    def switch_to_tab(self, window : 'pylewm.window.Window', hide_previous=True):
        if window == self.visible_window:
            return
        window.show()
        if self.visible_window:
            if hide_previous:
                self.visible_window.delayed_hide()
            if self.visible_window.space:
                if not window.is_tiled():
                    window.make_tiled()
                self.visible_window.space.replace_window(self.visible_window, window)
            elif window.is_tiled():
                window.make_floating()
                window.move_floating_to(self.visible_window.real_position)
        self.visible_window = window
        self.update_header()

HiddenTabWindow = None
HiddenTabWindowSince = None

def update_tabgroups():
    # If we change focus after pending a tab group, remove the pending tab group
    global PendingTabGroup
    global PendingTabTime
    if (
        PendingTabGroup
            and (not pylewm.focus.FocusWindow 
                 or (
                    pylewm.focus.FocusWindow.tab_group != PendingTabGroup
                    and not pylewm.focus.FocusWindow.is_ignored()
                    and not pylewm.focus.FocusWindow.is_pending_placement()
                 )
            )
    ):
        group = PendingTabGroup
        if len(group.windows) == 1:
            group.destroy()
        else:
            PendingTabGroup = None
            group.update_header()

    # Handle queued commands from the header bars
    queue = pylewm.headers.HeaderState.OutputQueue
    if queue:
        while queue.qsize() != 0:
            cmd = None
            try:
                cmd = queue.get(block=False)
            except:
                pass
            if cmd:
                id = cmd[0]
                if id in TabGroup.TabGroups:
                    TabGroup.TabGroups[id].handle_response(cmd[1:])
    
    # If a window is focused that is hidden by a tab group, switch that tab group to it
    global HiddenTabWindow
    global HiddenTabWindowSince
    
    window = pylewm.focus.FocusWindow
    have_hidden_tab = False
    if window and window.wm_hidden and window.tab_group and window.wm_visible_duration() > 0.05:
        if not window.tab_group.visible_window.wm_hidden:
            if window == HiddenTabWindow:
                if (time.time() - HiddenTabWindowSince) > 0.25:
                    window.tab_group.switch_to_tab(window)
            else:
                HiddenTabWindow = window
                HiddenTabWindowSince = time.time()
            have_hidden_tab = True

    if not have_hidden_tab:
        HiddenTabWindow = None

def has_focused_tab_group():
    window = pylewm.focus.FocusWindow
    if not window:
        return False
    if not window.tab_group:
        return False
    return True

def add_pending_tabbed_window(window):
    tab_group = pylewm.tabs.PendingTabGroup
    pylewm.tabs.PendingTabGroup = None

    previous_window = tab_group.visible_window
    tab_group.add_window(window)

@PyleCommand
def make_next_window_tabbed(toggle=True):
    ''' The next window that is opened will be become tabbed with the currently focused window '''
    global PendingTabGroup
    global PendingTabTime

    if toggle and PendingTabGroup:
        if len(PendingTabGroup.windows) == 1:
            PendingTabGroup.destroy()
        else:
            group = PendingTabGroup
            PendingTabGroup = None
            group.update_header()
        return

    window = pylewm.focus.FocusWindow
    if not window:
        return

    if not window.tab_group:
        tab_group = TabGroup()
        tab_group.add_window(window)

    PendingTabGroup = window.tab_group
    PendingTabGroup.update_header()
    PendingTabTime = time.time()

@PyleCommand
def next_tab():
    window = pylewm.focus.FocusWindow
    if not window:
        return

    tab_group = window.tab_group
    if not tab_group:
        return

    index = tab_group.windows.index(window)
    new_index = (index+1) % len(tab_group.windows)

    if index != new_index:
        window = tab_group.windows[new_index]
        tab_group.switch_to_tab(window)
        pylewm.focus.set_focus(window)

@PyleCommand
def previous_tab():
    window = pylewm.focus.FocusWindow
    if not window:
        return

    tab_group = window.tab_group
    if not tab_group:
        return

    index = tab_group.windows.index(window)
    new_index = (index-1) % len(tab_group.windows)

    if index != new_index:
        window = tab_group.windows[new_index]
        tab_group.switch_to_tab(window)
        pylewm.focus.set_focus(window)

@PyleTask(name="Detach Window from Tab Group", condition=has_focused_tab_group)
@PyleCommand
def detach_window_from_tab_group():
    window = pylewm.focus.FocusWindow
    if not window:
        return

    tab_group = window.tab_group
    if not tab_group:
        return

    tab_group.remove_window(window, change_focus=False)

@PyleTask(name="Split Entire Tab Group", condition=has_focused_tab_group)
@PyleCommand
def split_tab_group():
    window = pylewm.focus.FocusWindow
    if not window:
        return

    tab_group = window.tab_group
    if not tab_group:
        return

    tab_group.destroy()

@PyleCommand
def move_tab_next():
    window = pylewm.focus.FocusWindow
    if not window:
        return

    tab_group = window.tab_group
    if not tab_group:
        return

    index = tab_group.windows.index(window)
    new_index = (index+1) % len(tab_group.windows)
    
    if index != new_index:
        tab_group.windows[index] = tab_group.windows[new_index]
        tab_group.windows[new_index] = window
        tab_group.update_header()

@PyleCommand
def move_tab_previous():
    window = pylewm.focus.FocusWindow
    if not window:
        return

    tab_group = window.tab_group
    if not tab_group:
        return

    index = tab_group.windows.index(window)
    new_index = (index-1) % len(tab_group.windows)
    
    if index != new_index:
        tab_group.windows[index] = tab_group.windows[new_index]
        tab_group.windows[new_index] = window
        tab_group.update_header()

@PyleCommand
def duplicate_window_into_tab():
    """ Spawn a new instance of the focused program and add it to a tab group """
    window = pylewm.focus.FocusWindow
    if not window:
        return False

    make_next_window_tabbed(toggle=False).run()

    hwnd = window.proxy._hwnd
    def duplicate_window():
        executable = pylewm.winproxy.winfuncs.GetExecutableOfWindow(hwnd)
        if executable:
            pylewm.execution.run(executable).run()
    pylewm.commands.AsyncCommandThreadPool.submit(duplicate_window)