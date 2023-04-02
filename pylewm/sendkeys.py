from pylewm.hotkeys import KeySpec, KEY_MAP, ActiveKey
from pylewm.commands import PyleCommand
import pylewm.winproxy.winfuncs as winfuncs

import ctypes
import win32api, win32con

def sendKey(key):
    sendKeySpec(KeySpec.fromTuple(key))

def pressModifiers(keySpec):
    modifiers = (
        (keySpec.alt, win32con.VK_LMENU, win32con.VK_RMENU),
        (keySpec.shift, win32con.VK_LSHIFT, win32con.VK_RSHIFT),
        (keySpec.ctrl, win32con.VK_LCONTROL, win32con.VK_RCONTROL),
        (keySpec.win, win32con.VK_LWIN, win32con.VK_RWIN),
        (keySpec.app, win32con.VK_APPS, 0),
    )

    for mod in modifiers:
        if mod[0].left or mod[0].either:
            ctypes.windll.user32.keybd_event(mod[1], 0, 0, 0)
        elif mod[0].right:
            ctypes.windll.user32.keybd_event(mod[2], 0, 0, 0)

def releaseModifiers(keySpec):
    modifiers = (
        (keySpec.alt, win32con.VK_LMENU, win32con.VK_RMENU),
        (keySpec.shift, win32con.VK_LSHIFT, win32con.VK_RSHIFT),
        (keySpec.ctrl, win32con.VK_LCONTROL, win32con.VK_RCONTROL),
        (keySpec.win, win32con.VK_LWIN, win32con.VK_RWIN),
        (keySpec.app, win32con.VK_APPS, 0),
    )

    for mod in reversed(modifiers):
        if mod[0].left or mod[0].either:
            ctypes.windll.user32.keybd_event(mod[1], 0, win32con.KEYEVENTF_KEYUP, 0)
        elif mod[0].right:
            ctypes.windll.user32.keybd_event(mod[2], 0, win32con.KEYEVENTF_KEYUP, 0)

def sendKeySpec(keySpec):
    vkCode = 0
    if keySpec.key in KEY_MAP:
        vkCode = KEY_MAP[keySpec.key]
    else:
        vkCode = ctypes.windll.user32.VkKeyScanA(ctypes.wintypes.WCHAR(keySpec.key))

    prev_modifiers = ActiveKey.copy()
    
    releaseModifiers(prev_modifiers)
    pressModifiers(keySpec)
    ctypes.windll.user32.keybd_event(vkCode, 0, 0, 0)
    ctypes.windll.user32.keybd_event(vkCode, 0, win32con.KEYEVENTF_KEYUP, 0)
    releaseModifiers(keySpec)
    pressModifiers(prev_modifiers)

@PyleCommand
def release_key(keySpec):
    vkCode = 0
    if keySpec.key in vkMap:
        vkCode = vkMap[keySpec.key]
    else:
        vkCode = ctypes.windll.user32.VkKeyScanA(ctypes.wintypes.WCHAR(keySpec.key))
    ctypes.windll.user32.keybd_event(vkCode, 0, win32con.KEYEVENTF_KEYUP, 0)

@PyleCommand
def press_key(keySpec):
    vkCode = 0
    if keySpec.key in vkMap:
        vkCode = vkMap[keySpec.key]
    else:
        vkCode = ctypes.windll.user32.VkKeyScanA(ctypes.wintypes.WCHAR(keySpec.key))
    ctypes.windll.user32.keybd_event(vkCode, 0, 0, 0)

@PyleCommand
def sendkey(keys):
    """ Generate a single keypress. """
    sendKeySpec(KeySpec.fromTuple(keys))

@PyleCommand
def sendkeys(keys):
    """ Generate a list of keys to be pressed in sequence. """
    for key in keys:
        sendKeySpec(KeySpec.fromTuple(key))

@PyleCommand
def sendtext(text):
    """ Send keyboard events to type a string of text. """
    for char in text:
        input = winfuncs.INPUT()
        input.type = winfuncs.INPUT_KEYBOARD
        input.DUMMYUNIONNAME.ki = winfuncs.KEYBDINPUT(
            wVk=0,
            wScan=ord(char),
            dwFlags=winfuncs.KEYEVENTF_UNICODE,
            time=0,
            dwExtraInfo=0,
        )
        winfuncs.SendInput(1, winfuncs.c.byref(input), winfuncs.c.sizeof(winfuncs.INPUT))

        input = winfuncs.INPUT()
        input.type = winfuncs.INPUT_KEYBOARD
        input.DUMMYUNIONNAME.ki = winfuncs.KEYBDINPUT(
            wVk=0,
            wScan=ord(char),
            dwFlags=winfuncs.KEYEVENTF_UNICODE | winfuncs.KEYEVENTF_KEYUP,
            time=0,
            dwExtraInfo=0,
        )
        winfuncs.SendInput(1, winfuncs.c.byref(input), winfuncs.c.sizeof(winfuncs.INPUT))

@PyleCommand
def send_left_click():
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0)