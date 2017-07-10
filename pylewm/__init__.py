import sys, time, threading
from functools import partial

import pylewm.hotkeys

InitFunctions = []
TickFunctions = []

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
    global queuedFunctions
    queuedFunctions.append(fun)
    
def tick():
    pylewm.hotkeys.WMLock.acquire()
    global queuedFunctions
    run = list(queuedFunctions)
    queuedFunctions = []
    for fun in run:
        fun()
    for fun in TickFunctions:
        fun()
    pylewm.hotkeys.WMLock.release()

def runThread():
    global stopped
    while not stopped:
        tick()
        time.sleep(0.05)
        
def start():
    for fun in InitFunctions:
        fun()
    threading.Thread(target=runThread).start()
    hotkeys.waitForHotkeys()
    
def quit():
    global stopped
    stopped = True
    sys.exit()