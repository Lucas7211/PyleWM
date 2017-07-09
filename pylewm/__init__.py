import sys, time, threading
from functools import partial

import pylewm.hotkeys

def pylecommand(fun):
    out = lambda *args: partial(fun, *args)
    out.pylewm_callback = fun
    return out
  
stopped = False
queuedFunctions = []
def queue(fun):
    global queuedFunctions
    queuedFunctions.append(fun)
    
def tick():
    global queuedFunctions
    run = list(queuedFunctions)
    queuedFunctions = []
    for fun in run:
        fun()

def runThread():
    global stopped
    while not stopped:
        tick()
        time.sleep(0.05)
        
def start():
    threading.Thread(target=runThread).start()
    hotkeys.waitForHotkeys()
    
def quit():
    global stopped
    stopped = True
    sys.exit()