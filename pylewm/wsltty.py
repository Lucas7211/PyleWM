import pylewm.execution
from pylewm.commands import PyleCommand

# Function to open a WSL command in a new wsltty window
@PyleCommand
def open_wsltty(cmd=""):
    wsltty = [
        r'%LOCALAPPDATA%\wsltty\wsl.bat',
    ]

    if cmd:
        wsltty += [*cmd]
    pylewm.execution.run(wsltty, drop_admin=False).run()

# Turns a path from a windows path to the equivalent WSL path
def wsl_path(path):
    path = path.replace("\\", "/")
    path = path.replace(":/", "/")
    return "/mnt/" + path[0].lower() + path[1:]