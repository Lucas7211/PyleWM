from pylewm.hotkeys import KeySpec

from pylewm import pylecommand

import win32api
import win32com.client

def sendKeysRaw(winKeys):
    shell = win32com.client.Dispatch("WScript.Shell")
    shell.SendKeys(winKeys)

def sendKeySpec(keySpec):
    shell = win32com.client.Dispatch("WScript.Shell")
    keyStr = keySpec.key
    if keySpec.ctrl.isSet:
        keyStr = "^" + keyStr
    if keySpec.alt.isSet:
        keyStr = "%" + keyStr
    if keySpec.shift.isSet:
        keyStr = "+" + keyStr
    shell.SendKeys(keyStr)

@pylecommand
def sendkey(keys):
    """ Generate a single keypress. """
    sendKeySpec(KeySpec.fromTuple(keys))

@pylecommand
def sendkeys(keys):
    """ Generate a list of keys to be pressed in sequence. """
    for key in keys:
        sendKeySpec(KeySpec.fromTuple(key))