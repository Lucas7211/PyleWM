import pylewm.focus
import pylewm.execution
import pylewm.window
from pylewm.commands import PyleCommand, PyleTask
import pylewm.winproxy.winfuncs
import time

PendingTabGroup : 'TabGroup' = None
PendingTabTime = 0.0

class TabGroup:
    NextTabGroupId = 0

    def __init__(self):
        TabGroup.NextTabGroupId += 1
        self.group_id = TabGroup.NextTabGroupId

        self.windows : list[pylewm.window.Window] = []
        self.visible_window : pylewm.window.Window = None

    def destroy(self):
        for window in self.windows:
            window.tab_group = None
            if not window.closed:
                window.show()

    def add_window(self, window : 'pylewm.window.Window'):
        self.windows.append(window)
        window.tab_group = self

        if window.window_info.visible or window.wm_becoming_visible:
            self.switch_to_tab(window)
        else:
            window.hide()
        
    def remove_window(self, window : 'pylewm.window.Window'):
        index = self.windows.index(window)
        self.windows.remove(window)
        window.tab_group = None

        if len(self.windows) == 0:
            # Tab group is fully dead
            self.destroy()
        elif len(self.windows) == 1:
            # Removed the last window from the tab group, kill the tab group but keep the window
            if window == self.visible_window:
                self.switch_to_tab(self.windows[0])
                pylewm.focus.set_focus_no_mouse(self.visible_window)
            self.destroy()
        elif window == self.visible_window:
            self.switch_to_tab(self.windows[min(index, len(self.windows)-1)])
            if pylewm.focus.FocusWindow == window:
                pylewm.focus.set_focus_no_mouse(self.visible_window)

    def switch_to_tab(self, window : 'pylewm.window.Window', focus=True):
        if window == self.visible_window:
            return
        window.show()
        if self.visible_window:
            self.visible_window.hide()
            if self.visible_window.space:
                if not window.is_tiled():
                    window.make_tiled()
                self.visible_window.space.replace_window(self.visible_window, window)
            elif window.is_tiled():
                window.make_floating()
                window.move_floating_to(self.visible_window.real_position)
        self.visible_window = window

def update_tabgroups():
    global PendingTabGroup
    global PendingTabTime
    if (
        PendingTabGroup
            and (not pylewm.focus.FocusWindow or pylewm.focus.FocusWindow.tab_group != PendingTabGroup)
            and time.time() > PendingTabTime + 1.0
    ):
        print(f"lose tab from no focus {time.time()}")
        PendingTabGroup = None

def has_focused_tab_group():
    window = pylewm.focus.FocusWindow
    if not window:
        return False
    if not window.tab_group:
        return False
    return True

@PyleCommand
def make_next_window_tabbed():
    ''' The next window that is opened will be become tabbed with the currently focused window '''
    global PendingTabGroup
    global PendingTabTime

    window = pylewm.focus.FocusWindow
    if not window:
        return

    if not window.tab_group:
        tab_group = TabGroup()
        tab_group.add_window(window)

    PendingTabGroup = window.tab_group
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

    tab_group.remove_window(window)

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
    pass

@PyleCommand
def move_tab_previous():
    pass

@PyleCommand
def duplicate_window_into_tab():
    """ Spawn a new instance of the focused program and add it to a tab group """
    window = pylewm.focus.FocusWindow
    if not window:
        return False

    make_next_window_tabbed().run()
    print(f"duplicate into tab {time.time()}")

    hwnd = window.proxy._hwnd
    def duplicate_window():
        executable = pylewm.winproxy.winfuncs.GetExecutableOfWindow(hwnd)
        if executable:
            pylewm.execution.run(executable).run()
    pylewm.commands.AsyncCommandThreadPool.submit(duplicate_window)