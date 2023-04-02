import pylewm.commands
import pylewm.focus
import multiprocessing
import atexit

class HeaderState:
    Process : multiprocessing.Process = None
    CommandQueue : multiprocessing.Queue = None
    OutputQueue : multiprocessing.Queue = None

def header_process(CommandQueue, OutputQueue):
    import pylewm.header_renderer
    pylewm.header_renderer.CommandQueue = CommandQueue
    pylewm.header_renderer.OutputQueue = OutputQueue
    pylewm.header_renderer.run()

def kill_header_process():
    if HeaderState.Process and HeaderState.Process.is_alive():
        HeaderState.Process.kill()

def init_header_process():
    if HeaderState.Process:
        return

    HeaderState.CommandQueue = multiprocessing.Queue()
    HeaderState.OutputQueue = multiprocessing.Queue()
    HeaderState.Process = multiprocessing.Process(
        target=header_process,
        args=(HeaderState.CommandQueue, HeaderState.OutputQueue)
    )
    HeaderState.Process.start()
    atexit.register(kill_header_process)

class WindowHeader:
    def __init__(self, id, target_hwnd):
        self.header_id = id
        self.target_hwnd = target_hwnd

        init_header_process()

        HeaderState.CommandQueue.put(
            ["create",
                self.header_id,
                self.target_hwnd,
                []
            ]
        )

        self.closed = False

    def update(self, target_hwnd, entries, state):
        self.target_hwnd = target_hwnd
        HeaderState.CommandQueue.put(
            ["update", self.header_id, target_hwnd, entries, state]
        )

    def close(self):
        self.closed = True

        HeaderState.CommandQueue.put(
            ["close", self.header_id]
        )