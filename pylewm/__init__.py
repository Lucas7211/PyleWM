import sys, time, threading
from functools import partial
import traceback, os
import subprocess

import pystray
from PIL import Image

import pylewm.hotkeys
import pylewm.commands
import pylewm.monitors
import pylewm.execution
import pylewm.windows
import pylewm.window
import pylewm.window_classification
import pylewm.space
import pylewm.spaces

from pylewm.commands import PyleCommand, InitFunctions, CommandQueue, run_pyle_command

import threading

global_queue = CommandQueue()
tray_icon = None

def key_process_thread():
    pylewm.hotkeys.queue_command = global_queue.queue_command
    pylewm.hotkeys.wait_for_hotkeys()

def start():
    import ctypes
    if not ctypes.windll.shell32.IsUserAnAdmin() and False:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
        return
    else:
        # Get the credentials for the user right now so we can spawn stuff later
        #  Apparently we can't spawn stuff as a user without getting their password,
        #  even if we're elevated. Windows.
        print("Prompting for user credentials, since windows won't let us spawn as user without them even when we're admin:")
        args = ["runas", "/user:"+os.environ["USERDOMAIN"]+"\\"+os.environ["USERNAME"], "/savecred", "cmd.exe /c echo Credentials Saved..."]
        subprocess.call(args, shell=True)

    for fun in InitFunctions:
        fun()

    threading.Thread(target=key_process_thread, daemon=True).start()

    global tray_icon
    tray_icon = pystray.Icon('PyleWM')
    tray_icon.icon = Image.open("PyleWM.png")
    tray_icon.title = "PyleWM"
    tray_icon.menu = pystray.Menu(
        pystray.MenuItem("Quit", lambda: run_pyle_command(quit))
    )
    tray_icon.run()

def stop_threads():
    pylewm.commands.stopped = True
    global_queue.queue_event.set()
    tray_icon.stop()

@PyleCommand
def restart():
    pylewm.windows.reset_all()
    stop_threads()

    os.execl(sys.executable, sys.executable, *sys.argv)
    sys.exit()
    
@PyleCommand
def quit():
    pylewm.windows.reset_all()
    stop_threads()
    sys.exit()