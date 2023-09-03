from pylewm.hotkeys import KeySpec, KEY_MAP, ActiveKey
from pylewm.commands import PyleCommand
import pylewm.winproxy.winfuncs as winfuncs

import ctypes
import win32api, win32con
import time

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
    if keySpec.key in KEY_MAP:
        vkCode = KEY_MAP[keySpec.key]
    else:
        vkCode = ctypes.windll.user32.VkKeyScanA(ctypes.wintypes.WCHAR(keySpec.key))
    ctypes.windll.user32.keybd_event(vkCode, 0, win32con.KEYEVENTF_KEYUP, 0)

@PyleCommand
def press_key(keySpec):
    vkCode = 0
    if keySpec.key in KEY_MAP:
        vkCode = KEY_MAP[keySpec.key]
    else:
        vkCode = ctypes.windll.user32.VkKeyScanA(ctypes.wintypes.WCHAR(keySpec.key))
    ctypes.windll.user32.keybd_event(vkCode, 0, 0, 0)

@PyleCommand
def sendkey(key):
    """ Generate a single keypress. """
    sendKeySpec(KeySpec.fromTuple(key))

@PyleCommand
def sendkeys(keys):
    """ Generate a list of keys to be pressed in sequence. """
    for key in keys:
        sendKeySpec(KeySpec.fromTuple(key))

@PyleCommand.Threaded
def sendsequence(keys):
    """ Generate a list of keys to be pressed in sequence. """
    prev_modifiers = ActiveKey.copy()
    releaseModifiers(prev_modifiers)

    input_array = (winfuncs.INPUT * (len(keys) * 2))()

    spec = ""
    in_spec = False

    key_count = 0

    def add_vk_press(vk):
        nonlocal key_count
        input_array[key_count].type = winfuncs.INPUT_KEYBOARD
        input_array[key_count].DUMMYUNIONNAME.ki = winfuncs.KEYBDINPUT(
            wVk=vk,
            wScan=0,
            dwFlags=0,
            time=0,
            dwExtraInfo=0,
        )
        key_count += 1

    def add_vk_release(vk):
        nonlocal key_count
        input_array[key_count].type = winfuncs.INPUT_KEYBOARD
        input_array[key_count].DUMMYUNIONNAME.ki = winfuncs.KEYBDINPUT(
            wVk=vk,
            wScan=0,
            dwFlags=winfuncs.KEYEVENTF_KEYUP,
            time=0,
            dwExtraInfo=0,
        )
        key_count += 1

    def add_vk(vk):
        add_vk_press(vk)
        add_vk_release(vk)

    def add_keySpec(keySpec):
        nonlocal key_count
        modifiers = (
            (keySpec.alt, win32con.VK_LMENU, win32con.VK_RMENU),
            (keySpec.shift, win32con.VK_LSHIFT, win32con.VK_RSHIFT),
            (keySpec.ctrl, win32con.VK_LCONTROL, win32con.VK_RCONTROL),
            (keySpec.win, win32con.VK_LWIN, win32con.VK_RWIN),
            (keySpec.app, win32con.VK_APPS, 0),
        )

        for mod in modifiers:
            if mod[0].left or mod[0].either:
                add_vk_press(mod[1])
            elif mod[0].right:
                add_vk_press(mod[2])

        vkCode = 0
        if keySpec.key in KEY_MAP:
            vkCode = KEY_MAP[keySpec.key]
        else:
            vkCode = ctypes.windll.user32.VkKeyScanA(ctypes.wintypes.WCHAR(keySpec.key))
        add_vk(vkCode)

        for mod in reversed(modifiers):
            if mod[0].left or mod[0].either:
                add_vk_release(mod[1])
            elif mod[0].right:
                add_vk_release(mod[2])

    def add_char(char):
        nonlocal key_count
        input_array[key_count].type = winfuncs.INPUT_KEYBOARD
        input_array[key_count].DUMMYUNIONNAME.ki = winfuncs.KEYBDINPUT(
            wVk=0,
            wScan=ord(char),
            dwFlags=winfuncs.KEYEVENTF_UNICODE,
            time=0,
            dwExtraInfo=0,
        )
        key_count += 1

        input_array[key_count].type = winfuncs.INPUT_KEYBOARD
        input_array[key_count].DUMMYUNIONNAME.ki = winfuncs.KEYBDINPUT(
            wVk=0,
            wScan=ord(char),
            dwFlags=winfuncs.KEYEVENTF_UNICODE | winfuncs.KEYEVENTF_KEYUP,
            time=0,
            dwExtraInfo=0,
        )
        key_count += 1

    for key in keys:
        if in_spec:
            if key == "<":
                add_char("<")
                in_spec = False
                spec = ""
            elif key == ">":
                in_spec = False

                if spec == "block":
                    winfuncs.SendInput(key_count, input_array, winfuncs.c.sizeof(winfuncs.INPUT))
                    time.sleep(0.5)
                    sendtext("{").run()
                    time.sleep(0.1)
                    ctypes.windll.user32.keybd_event(win32con.VK_RETURN, 0, 0, 0)
                    ctypes.windll.user32.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
                    key_count = 0
                elif spec == "finish":
                    winfuncs.SendInput(key_count, input_array, winfuncs.c.sizeof(winfuncs.INPUT))
                    time.sleep(0.5)
                    ctypes.windll.user32.keybd_event(win32con.VK_RETURN, 0, 0, 0)
                    ctypes.windll.user32.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
                    key_count = 0
                else:
                    keySpec = KeySpec.fromTuple(spec.split("+"))
                    add_keySpec(keySpec)

                spec = ""
            else:
                spec += key
        else:
            if key == '\n':
                add_vk(win32con.VK_RETURN)
            elif key == '\t':
                add_vk(win32con.VK_TAB)
            if key == '<':
                in_spec = True
            else:
                add_char(key)

    if key_count != 0:
        winfuncs.SendInput(key_count, input_array, winfuncs.c.sizeof(winfuncs.INPUT))
    pressModifiers(prev_modifiers)

@PyleCommand
def sendtext(text):
    """ Send keyboard events to type a string of text. """
    input_array = (winfuncs.INPUT * (len(text) * 2))()
    for i, char in enumerate(text):
        input_array[i*2].type = winfuncs.INPUT_KEYBOARD
        input_array[i*2].DUMMYUNIONNAME.ki = winfuncs.KEYBDINPUT(
            wVk=0,
            wScan=ord(char),
            dwFlags=winfuncs.KEYEVENTF_UNICODE,
            time=0,
            dwExtraInfo=0,
        )

        input_array[i*2+1].type = winfuncs.INPUT_KEYBOARD
        input_array[i*2+1].DUMMYUNIONNAME.ki = winfuncs.KEYBDINPUT(
            wVk=0,
            wScan=ord(char),
            dwFlags=winfuncs.KEYEVENTF_UNICODE | winfuncs.KEYEVENTF_KEYUP,
            time=0,
            dwExtraInfo=0,
        )

    winfuncs.SendInput(len(input_array), input_array, winfuncs.c.sizeof(winfuncs.INPUT))

@PyleCommand
def send_left_click():
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0)