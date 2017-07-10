from pylewm import pylecommand, queue
import win32gui

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
            print("COULD NOT SET FOREGROUND TO "+win32gui.GetWindowText(window))