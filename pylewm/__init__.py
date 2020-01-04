import sys, time, threading
from functools import partial
import traceback, os
import subprocess

import pylewm.hotkeys
import pylewm.commands
import pylewm.monitors
import pylewm.execution
import pylewm.windows
import pylewm.window
import pylewm.window_classification
import pylewm.space
import pylewm.spaces

from pylewm.commands import PyleCommand, InitFunctions, CommandQueue

from threading import RLock, Event

global_queue = CommandQueue()
  
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
    pylewm.hotkeys.queue_command = global_queue.queue_command
    pylewm.hotkeys.wait_for_hotkeys()

def stop_threads():
    pylewm.commands.stopped = True
    global_queue.queue_event.set()

@PyleCommand
def restart():
    stop_threads()
    subprocess.call([sys.executable, *sys.argv])
    os._exit(0)
    
@PyleCommand
def quit():
    stop_threads()
    os._exit(0)