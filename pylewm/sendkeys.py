from pylewm.hotkeys import KeySpec

from pylewm import pylecommand

import ctypes
import win32api, win32con

# TODO: Complete this map
vkMap = {
    'esc': win32con.VK_ESCAPE,
}

def sendKey(key):
    sendKeySpec(KeySpec.fromTuple(key))

def sendKeySpec(keySpec):
    vkCode = 0
    if keySpec.key in vkMap:
        vkCode = vkMap[keySpec.key]
    else:
        vkCode = ctypes.windll.user32.VkKeyScanA(ctypes.wintypes.WCHAR(chr(keySpec.key)))
        
    modifiers = (
        (keySpec.alt, win32con.VK_LMENU, win32con.VK_RMENU),
        (keySpec.shift, win32con.VK_LSHIFT, win32con.VK_RSHIFT),
        (keySpec.ctrl, win32con.VK_LCONTROL, win32con.VK_RCONTROL),
        (keySpec.win, win32con.VK_LWIN, win32con.VK_RWIN),
    )
    
    for mod in modifiers:
        if mod[0].left or mod[0].either:
            ctypes.windll.user32.keybd_event(mod[1], 0, 0, 0)
        elif mod[0].right:
            ctypes.windll.user32.keybd_event(mod[2], 0, 0, 0)
    ctypes.windll.user32.keybd_event(vkCode, 0, 0, 0)
    ctypes.windll.user32.keybd_event(vkCode, 0, win32con.KEYEVENTF_KEYUP, 0)
    for mod in reversed(modifiers):
        if mod[0].left or mod[0].either:
            ctypes.windll.user32.keybd_event(mod[1], 0, win32con.KEYEVENTF_KEYUP, 0)
        elif mod[0].right:
            ctypes.windll.user32.keybd_event(mod[2], 0, win32con.KEYEVENTF_KEYUP, 0)

@pylecommand
def sendkey(keys):
    """ Generate a single keypress. """
    sendKeySpec(KeySpec.fromTuple(keys))

@pylecommand
def sendkeys(keys):
    """ Generate a list of keys to be pressed in sequence. """
    for key in keys:
        sendKeySpec(KeySpec.fromTuple(key))