from pylewm.sendkeys import sendKey
from pylewm.commands import PyleCommand

import os, ctypes
import subprocess

import win32com.shell.shell as win_shell

import win32process

@PyleCommand.Threaded
def start_menu():
    """ Open the start menu. """
    sendKey(('ctrl', 'esc'))
    
@PyleCommand.Threaded
def run(args, cwd=None, drop_admin=True):
    """ Run an arbitrary command. """
    if isinstance(args, str):
        args = [args]
    args = list(args)
    
    if cwd is None:
        cwd = os.getenv("USERPROFILE")
    
    if drop_admin and ctypes.windll.shell32.IsUserAnAdmin():
        # Drop privileges back to the normal user for execution
        USER = os.environ["USERDOMAIN"] + "\\" + os.environ["USERNAME"]
        args = ["runas", "/user:"+USER, "/savecred", "/env", " ".join(args)]
    
    subprocess.call(args, shell=True, cwd=cwd)