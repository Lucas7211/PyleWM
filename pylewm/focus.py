from pylewm import pylecommand, queue
import pythoncom
import win32gui, win32com.client
import traceback

ComInitialized = False

def set(window, num=10):
    try:
        global ComInitialized
        if not ComInitialized:
            pythoncom.CoInitialize()
            ComInitialized = True

        # Send a bogus alt key to ourselves so we are 
        # marked as having received keyboard input, which
        # makes windows determine we have the power to change
        # window focus. Somehow.
        shell = win32com.client.Dispatch("WScript.Shell")
        shell.SendKeys('%')

        win32gui.SetForegroundWindow(window)
        return True
    except Exception as ex:
        # Try it a few more times. Maybe windows will let us do it later.
        if num > 0:
            queue(lambda: set(window, num-1))
        else:
            print("Error: Could not switch focus to window: "+win32gui.GetWindowText(window))
            print("Is HKCU\Control Panel\Desktop\ForegroundLockTimeout set to 0?")
            traceback.print_exc()
            traceback.print_stack()
