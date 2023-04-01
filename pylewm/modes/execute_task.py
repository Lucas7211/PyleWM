import pylewm
import pylewm.commands
import pylewm.modes.list_mode
from pylewm.window import WindowsByProxy, WindowState

class TaskOption(pylewm.modes.list_mode.ListOption):
    def __init__(self, name, detail, function):
        self.name = name
        self.detail = detail
        self.function = function

    def confirm(self):
        pylewm.commands.Commands.queue(self.function)

@pylewm.commands.PyleCommand
def start_execute_task(hotkeys = {}):
    options = []

    for task_function in pylewm.commands.STATIC_TASKS:
        options.append(TaskOption(task_function.task_name, task_function.task_detail, task_function))

    for task_generator in pylewm.commands.TASK_GENERATORS:
        for task_function in task_generator:
            options.append(TaskOption(task_function.task_name, task_function.task_detail, task_function))

    mode = pylewm.modes.list_mode.ListMode(hotkeys, options)
    mode.bg_selected_color = (80, 160, 80)
    mode()