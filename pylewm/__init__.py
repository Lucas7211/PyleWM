import sys, time, threading
from functools import partial
import traceback, os

import pylewm.hotkeys
from threading import RLock
QueueLock = RLock()

InitFunctions = []
TickFunctions = []
config = {}

def pylecommand(fun):
    out = lambda *args: partial(fun, *args)
    out.pylewm_callback = fun
    return out
 
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
    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
        return
    for fun in InitFunctions:
        fun()
    threading.Thread(target=runThread).start()
    pylewm.hotkeys.queue = queue
    pylewm.hotkeys.waitForHotkeys()
    
def quit():
    global stopped
    stopped = True
    os._exit(0)