from pylewm.sendkeys import sendKeysRaw
from pylewm import pylecommand

@pylecommand
def start_menu():
    """ Open the start menu. """
    sendKeysRaw("^{Esc}")