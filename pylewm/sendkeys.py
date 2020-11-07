from pylewm.hotkeys import KeySpec
from pylewm.commands import PyleCommand

import ctypes
import win32api, win32con

# TODO: Complete this map
vkMap = {
    'esc': win32con.VK_ESCAPE,
    'lctrl': win32con.VK_LCONTROL,
    'rctrl': win32con.VK_RCONTROL,
    'lshift': win32con.VK_LSHIFT,
    'rshift': win32con.VK_RSHIFT,
    'lalt': win32con.VK_LMENU,
    'ralt': win32con.VK_RMENU,
    'app': win32con.VK_APPS,
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

@PyleCommand.Threaded
def release_key(keySpec):
    vkCode = 0
    if keySpec.key in vkMap:
        vkCode = vkMap[keySpec.key]
    else:
        vkCode = ctypes.windll.user32.VkKeyScanA(ctypes.wintypes.WCHAR(chr(keySpec.key)))
    ctypes.windll.user32.keybd_event(vkCode, 0, win32con.KEYEVENTF_KEYUP, 0)

@PyleCommand.Threaded
def press_key(keySpec):
    vkCode = 0
    if keySpec.key in vkMap:
        vkCode = vkMap[keySpec.key]
    else:
        vkCode = ctypes.windll.user32.VkKeyScanA(ctypes.wintypes.WCHAR(chr(keySpec.key)))
    ctypes.windll.user32.keybd_event(vkCode, 0, 0, 0)

@PyleCommand.Threaded
def sendkey(keys):
    """ Generate a single keypress. """
    sendKeySpec(KeySpec.fromTuple(keys))

@PyleCommand.Threaded
def sendkeys(keys):
    """ Generate a list of keys to be pressed in sequence. """
    for key in keys:
        sendKeySpec(KeySpec.fromTuple(key))

@PyleCommand.Threaded
def send_left_click():
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0)