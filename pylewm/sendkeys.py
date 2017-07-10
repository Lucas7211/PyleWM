from pylewm.hotkeys import KeySpec

from pylewm import pylecommand

import ctypes
import win32api
import win32com.client

def sendKeysRaw(winKeys):
    shell = win32com.client.Dispatch("WScript.Shell")
    shell.SendKeys(winKeys)

def sendKeySpec(keySpec):
    pass
    #ctypes.windll.user32.keybd_event(vk_mod, 0, 0, 0)
    #ctypes.windll.user32.keybd_event(vkCode, 0, 0, 0)

@pylecommand
def sendkey(keys):
    """ Generate a single keypress. """
    sendKeySpec(KeySpec.fromTuple(keys))

@pylecommand
def sendkeys(keys):
    """ Generate a list of keys to be pressed in sequence. """
    for key in keys:
        sendKeySpec(KeySpec.fromTuple(key))