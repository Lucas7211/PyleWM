
import os
import pylewm.execution
import pylewm.hotkeys
import pylewm.sendkeys
from pylewm.commands import PyleCommand

class AltMode(pylewm.hotkeys.Mode):
    def __init__(self):
        pylewm.hotkeys.Mode.__init__(self)
        self.exit_pressed = False

    def handle_key(self, key, isMod):
        if key.key == self.exit_key.lower():
            if key.down:
                self.exit_pressed = True
            elif self.exit_pressed:
                pylewm.hotkeys.queue_command(pylewm.hotkeys.escape_mode)
            return True
        if key.key == self.mod_key:
            if key.down:
                pylewm.hotkeys.queue_command(pylewm.sendkeys.press_key(pylewm.hotkeys.KeySpec('lalt')))
            else:
                pylewm.hotkeys.queue_command(pylewm.sendkeys.release_key(pylewm.hotkeys.KeySpec('lalt')))
            return True
        return True

@PyleCommand
def alt_mode(mod_key = 'rctrl', exit_key = 'F5'):
    mode = AltMode()
    mode.exit_key = exit_key
    mode.mod_key = mod_key
    mode()
