from pylewm.sendkeys import sendKeysRaw
from pylewm import pylecommand
import os, ctypes
import subprocess

@pylecommand
def start_menu():
    """ Open the start menu. """
    sendKeysRaw("^{Esc}")
    
@pylecommand
def run(args):
    """ Run an arbitrary command. """
    if isinstance(args, str):
        args = [args]
    args = list(args)
    print(f"RUN {args}")
    # Drop down to user privileges
    args = ["runas", "/trustlevel:0x20000"] + args
    subprocess.call(args, shell=True)