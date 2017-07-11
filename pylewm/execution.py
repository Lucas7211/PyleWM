from pylewm.sendkeys import sendKey
from pylewm import pylecommand
import os, ctypes
import subprocess

@pylecommand
def start_menu():
    """ Open the start menu. """
    sendKey(('ctrl', 'esc'))
    
@pylecommand
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
    
    print(f"RUN {args} AT cwd={cwd}")
    subprocess.call(args, shell=True, cwd=cwd)