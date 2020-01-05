import pylewm.commands
import pylewm.window
import pythoncom
import win32gui, win32com.client
import win32api
import traceback
import ctypes

FocusQueue = pylewm.commands.CommandQueue()

FocusSpace = None
FocusWindow = None
LastFocusWindow = None

def set_focus(window):
    hwnd = window.handle
    rect = window.rect.copy()
    FocusQueue.queue_command(lambda: focus_window_handle(hwnd, rect))

def set_focus_monitor(monitor):
    hwnd = ctypes.windll.user32.GetShellWindow()
    rect = monitor.rect.copy()
    FocusQueue.queue_command(lambda: focus_window_handle(hwnd, rect))

ComInitialized = False
def focus_window_handle(hwnd, rect=None, num=10):
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
        shell.SendKeys('^')

        win32gui.SetForegroundWindow(hwnd)

        if rect:
            try:
                win32api.SetCursorPos((rect.left + 20, rect.top + 10))
            except:
                pass # Not allowed, probably an administrator window has focus or something
                #traceback.print_exc()

        return True
    except Exception as ex:
        # Try it a few more times. Maybe windows will let us do it later.
        if num > 0:
            FocusQueue.queue_command(lambda: focus_window_handle(hwnd, rect, num-1))
        else:
            print("Error: Could not switch focus to window: "+win32gui.GetWindowText(hwnd))
            print("Is HKCU\Control Panel\Desktop\ForegroundLockTimeout set to 0?")
            traceback.print_exc()
            traceback.print_stack()
