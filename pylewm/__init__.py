import sys, time, threading
from functools import partial
import traceback, os
import subprocess

import pylewm.hotkeys
from threading import RLock
QueueLock = RLock()

InitFunctions = []
TickFunctions = []
config = {}

def pylecommand(fun):
    out = lambda *args, **kwargs: partial(fun, *args, **kwargs)
    out.pylewm_callback = fun
    return out

def runpylecommand(fun, *args, **kwargs):
    if hasattr(fun, "pylewm_callback"):
        fun = fun.pylewm_callback
    fun(*args, **kwargs)

def getpylecommand(fun, *args, **kwargs):
    if hasattr(fun, "pylewm_callback"):
        return fun.pylewm_callback
    return fun
 
def pyleinit(fun):
    InitFunctions.append(fun)
    return fun
    
def pyletick(fun):
    TickFunctions.append(fun)
    return fun
  
stopped = False
queuedFunctions = []
def queue(fun):
    with QueueLock:
        global queuedFunctions
        queuedFunctions.append(fun)
    
def tick():
    run = None
    with QueueLock:
        global queuedFunctions
        run = list(queuedFunctions)
        queuedFunctions = []
    try:
        for fun in TickFunctions:
            fun()
        for fun in run:
            fun()
    except Exception as ex:
        traceback.print_exc()

def runThread():
    global stopped
    while not stopped:
        tick()
        time.sleep(0.05)
        
def start():
    import ctypes
    if not ctypes.windll.shell32.IsUserAnAdmin() and config.get("RunAsAdmin", True):
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
    threading.Thread(target=runThread).start()
    pylewm.hotkeys.queue = queue
    pylewm.hotkeys.waitForHotkeys()

def restart():
    subprocess.call([sys.executable, *sys.argv])
    quit()
    
def quit():
    global stopped
    stopped = True
    os._exit(0)
