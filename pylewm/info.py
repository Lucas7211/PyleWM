from pylewm.commands import PyleCommand, PyleTask
import pylewm.window
import pylewm.window_update
import pylewm.winproxy.windowproxy
import pylewm.winproxy.winupdate

import pylewm.winproxy.winfuncs as winfuncs

@PyleTask(name="Show Window Info")
@PyleCommand.Threaded
def show_performance_info():
    state = f"""
Window Update Durations:
{pylewm.window_update.LastInteractiveUpdateDuration*1000 :.2f} ms
{pylewm.window_update.LastBackgroundUpdateDuration*1000 :.2f} ms
----
{pylewm.window_update.LastTotalUpdateDuration*1000 :.2f} ms

Proxy Update Durations:
{pylewm.winproxy.winupdate.LastInteractiveUpdateDuration*1000 :.2f} ms
{pylewm.winproxy.winupdate.LastBackgroundUpdateDuration*1000 :.2f} ms
----
{pylewm.winproxy.winupdate.LastTotalUpdateDuration*1000 :.2f} ms

Interactive Proxies: {pylewm.winproxy.windowproxy.InteractiveWindowProxies}

Interactive Windows:
"""

    for window in pylewm.window.InteractiveWindows:
        state += f"""
{window} | Visible: {window.window_info.visible} | State: {window.state} | Backgroundable: {window.is_background_update()} | Space: {window.space}
"""
    winfuncs.ShowMessageBox("PyleWM: Performance Info", state)