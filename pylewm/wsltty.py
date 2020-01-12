import os
import pylewm.execution
from pylewm.commands import PyleCommand

# Function to open a WSL command in a new wsltty window
@PyleCommand
def open_wsltty(cmd=""):
    wsltty = [
        os.getenv("LOCALAPPDATA") + r'\wsltty\wsl.bat',
    ]

    if cmd:
        wsltty += ["/bin/bash", "-l", "-c", " ".join(cmd)]
    pylewm.execution.run(wsltty, as_admin=True).run()

# Turns a path from a windows path to the equivalent WSL path
def wsl_path(path):
    path = path.replace("\\", "/")
    path = path.replace(":/", "/")
    return "/mnt/" + path[0].lower() + path[1:]