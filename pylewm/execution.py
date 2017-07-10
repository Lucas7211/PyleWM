from pylewm.sendkeys import sendKeysRaw
from pylewm import pylecommand
import os

@pylecommand
def start_menu():
    """ Open the start menu. """
    sendKeysRaw("^{Esc}")
    
@pylecommand
def run(exe):
    """ Run an arbitrary command. """
    print(f"RUN {exe}")
    os.system(exe)