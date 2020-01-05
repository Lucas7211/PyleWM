from functools import partial
from concurrent.futures import ThreadPoolExecutor

import traceback
import threading
import time

InitFunctions = []
stopped = False

ThreadPool = ThreadPoolExecutor(max_workers=64)

def delay_pyle_command(timer, fun):
    def timed_cmd():
        time.sleep(timer)
        fun()
    ThreadPool.submit(timed_cmd)

def queue_pyle_command(fun):
    ThreadPool.submit(fun)

class PyleCommand:
    @staticmethod
    def Threaded(func):
        cmd = PyleCommand(func)
        cmd.threaded = True
        return cmd
    
    def __init__(self, func):
        self.func = func
        self.threaded = False

    def __call__(self, *args, **kwargs):
        cmd = PyleCommand(
            partial(self.func, *args, **kwargs)
        )
        cmd.threaded = self.threaded
        return cmd

    def execute_on_thread(self):
        try:
            self.func()
        except Exception as ex:
            traceback.print_exc()

    def run(self):
        if self.threaded:
            ThreadPool.submit(self.execute_on_thread)
        else:
            self.func()

def run_pyle_command(fun):
    if isinstance(fun, PyleCommand):
        fun.run()
    else:
        fun()

def PyleInit(fun):
    InitFunctions.append(fun)
    return fun

def PyleThread(timer):
    def TickDecorator(func):
        def TickThread():
            global stopped
            while not stopped:
                func()
                time.sleep(timer)
        def ThreadInit():
            threading.Thread(target=TickThread, daemon=True).start()
        InitFunctions.append(ThreadInit)
    return TickDecorator

class CommandQueue:
    def __init__(self):
        self.queuedFunctions = []
        self.queue_lock = threading.RLock()
        self.queue_event = threading.Event()
        self.stopped = False

        threading.Thread(target=self.process_commands_thread, daemon=True).start()
    
    def stop(self):
        self.stopped = True
        self.queue_event.set()

    def queue_command(self, fun):
        with self.queue_lock:
            self.queuedFunctions.append(fun)
            self.queue_event.set()
        
    def process_commands_thread(self):
        global stopped
        while not stopped and not self.stopped:
            self.queue_event.wait()

            run = None
            with self.queue_lock:
                run = list(self.queuedFunctions)
                self.queuedFunctions = []
                self.queue_event.clear()

            try:
                for cmd in run:
                    run_pyle_command(cmd)
            except Exception as ex:
                traceback.print_exc()
