from pylewm.sendkeys import sendKey
from pylewm.commands import PyleCommand

import os, ctypes
import subprocess

@PyleCommand.Threaded
def start_menu():
    """ Open the start menu. """
    sendKey(('ctrl', 'esc'))
    
@PyleCommand
def run(args, cwd=None):
    """ Run an arbitrary command. """
    if isinstance(args, str):
        args = [args]
    args = list(args)
    
    if cwd is None:
        cwd = os.getenv("USERPROFILE")
    
    if ctypes.windll.shell32.IsUserAnAdmin():
        # Drop privileges back to the normal user for execution
        USER = os.environ["USERDOMAIN"] + "\\" + os.environ["USERNAME"]
        args = ["runas", "/user:"+USER, "/savecred"] + args
    
    subprocess.call(args, shell=True, cwd=cwd)