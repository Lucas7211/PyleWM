from pylewm import pylecommand, queue
import win32gui
import traceback

def set(window, num=10):
    if num == 10:
        queue(lambda: set(window, num-1))
        return
    try:
        win32gui.SetForegroundWindow(window)
        return True
    except:
        # Try it a few more times. Maybe windows will let us do it later.
        if num > 0:
            queue(lambda: set(window, num-1))
        else:
            print("Error: Could not switch focus to window: "+win32gui.GetWindowText(window))
            print("Is HKCU\Control Panel\Desktop\ForegroundLockTimeout set to 0?")