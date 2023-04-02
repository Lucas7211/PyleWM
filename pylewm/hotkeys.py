import pylewm.commands
import sys, ctypes
from ctypes import windll, CFUNCTYPE, POINTER, c_int, c_uint, c_void_p, byref, c_ulong, pointer, addressof, create_string_buffer
import win32con, win32gui, atexit
import ctypes.wintypes as wintypes
import pylewm.winproxy.winfuncs as winfuncs

import traceback, threading
import copy
import time

class MouseState:
    LEFT_MOUSE_DOWN = False
    RIGHT_MOUSE_DOWN = False
    MOUSE_HOOKS = []

queue_command = None

class Mode:
    def __init__(self, hotkeys={}, captureAll=True, oneshot=False):
        self.hotkeys = []
        self.captureAll = captureAll
        self.oneshot = oneshot
        for key, bind in hotkeys.items():
            if hasattr(bind, "pylewm_callback"):
                bind = bind.pylewm_callback
            self.hotkeys.append((KeySpec.fromTuple(key), bind))

    def handle_key(self, key, isMod):
        if key.key == "esc":
            # Escape always escapes out of modes
            queue_command(escape_mode)
            return True
        for bnd in self.hotkeys:
            if bnd[0] == key:
                if self.oneshot:
                    queue_command(escape_mode)
                queue_command(bnd[1])
                return True
        if self.oneshot and key.down and not isMod:
            queue_command(escape_mode)
            return True
        if not isMod and self.captureAll:
            return True
        else:
            return None

    def end_mode(self):
        pass

    def __call__(self):
        with ModeLock:
            ModeStack.insert(0, self)

class KeyPrompt(Mode):
    def __init__(self, callback, escape_cancels=True):
        self.callback = callback
        self.escape_cancels = escape_cancels

    def handle_key(self, key, isMod):
        if not isMod:
            if key.down:
                prompt = self
                storeKey = copy.deepcopy(key)
                def handle():
                    if not self.escape_cancels or key.key != "esc":
                        prompt.callback(storeKey)
                    escape_mode()
                queue_command(handle)
            return True
        else:
            return False

def prompt_key(callback):
    KeyPrompt(callback)()

@pylewm.commands.PyleCommand
def escape_mode():
    """ Escape whatever hotkey mode we're currently in. """
    with ModeLock:
        if ModeStack:
            ModeStack[0].end_mode()
            ModeStack.pop(0)

@pylewm.commands.PyleCommand
def release_all_modifiers():
    """ Synthetically release all modifiers currently being held. """
    ActiveKey.alt.release()
    ActiveKey.win.release()
    ActiveKey.ctrl.release()
    ActiveKey.shift.release()
    ActiveKey.app.release()

@pylewm.commands.PyleCommand
def absorb_key():
    """ Absorb whatever key is being pressed. """
    pass

class ModPair:
    def __init__(self, left=False, right=False, either=False, any_state=False):
        self.left = left
        self.right = right
        self.either = either
        self.any_state = any_state
        
    def __eq__(self, other):
        if self.any_state or other.any_state:
            return True
        if self.either:
            return other.left or other.right or other.either
        if other.either:
            return self.left or self.right
        return self.left == other.left and self.right == other.right
        
    def __repr__(self):
        str = ""
        if self.either:
            str += "A"
        if self.left:
            str += "L"
        if self.right:
            str += "R"
        if self.any_state:
            str += "?"
        if not str:
            str = "-"
        return str
      
    @property
    def isSet(self):
        return self.left or self.right or self.either
        
    def update(self, matchKey, matchSet, leftKey, rightKey):
        isMod = 0
        if matchKey == leftKey and leftKey != 0:
            self.left = matchSet
            isMod = 1
        if matchKey == rightKey and rightKey != 0:
            self.right = matchSet
            isMod = 2
        self.either = False
        return isMod
    
    def release(self):
        self.left = False
        self.right = False
        self.either = False
        self.any_state = False

    def copy(self):
        other = ModPair()
        other.left = self.left
        other.right = self.right
        other.either = self.either
        other.any_state = self.any_state
        return other

class KeySpec:
    def __init__(self, key):
        self.alt = ModPair()
        self.win = ModPair()
        self.ctrl = ModPair()
        self.shift = ModPair()
        self.app = ModPair()
        self.key = key
        self.down = True

    def any_modifier(self) -> bool:
        return self.alt.isSet or self.win.isSet or self.ctrl.isSet or self.shift.isSet or self.app.isSet
      
    @staticmethod
    def fromTuple(key):
        spec = KeySpec('')
        if isinstance(key, str):
            spec.key = key.lower()
        else:
            for elem in key:
                if elem.lower() == "ralt":
                    spec.alt.right = True
                elif elem.lower() == "lalt":
                    spec.alt.left = True
                elif elem.lower() == "alt":
                    spec.alt.either = True
                elif elem.lower() == "rctrl":
                    spec.ctrl.right = True
                elif elem.lower() == "lctrl":
                    spec.ctrl.left = True
                elif elem.lower() == "ctrl":
                    spec.ctrl.either = True
                elif elem.lower() == "rshift":
                    spec.shift.right = True
                elif elem.lower() == "lshift":
                    spec.shift.left = True
                elif elem.lower() == "shift":
                    spec.shift.either = True
                elif elem.lower() == "rwin":
                    spec.win.right = True
                elif elem.lower() == "lwin":
                    spec.win.left = True
                elif elem.lower() == "win":
                    spec.win.either = True
                elif elem.lower() == "app":
                    spec.app.either = True
                elif elem.startswith('=') and elem != '=':
                    spec.key = elem[1:].lower()
                elif elem == 'any_mod':
                    spec.win.any_state = True
                    spec.ctrl.any_state = True
                    spec.alt.any_state = True
                    spec.shift.any_state = True
                    spec.app.any_state = True
                else:
                    spec.key = elem.lower()
        return spec

    def equals_combo(self, other):
        return self.alt == other.alt and self.win == other.win \
            and self.ctrl == other.ctrl and self.shift == other.shift \
            and self.key == other.key and self.app == other.app

    def copy(self):
        other = KeySpec(self.key)
        other.alt = self.alt.copy()
        other.win = self.win.copy()
        other.ctrl = self.ctrl.copy()
        other.shift = self.shift.copy()
        other.app = self.app.copy()
        other.down = self.down
        return other

    def __eq__(self, other):
        return self.equals_combo(other) and self.down == other.down
            
    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return repr(self.__dict__)
            
KeyBindings = {}
ModeStack = []
ModeLock = threading.RLock()
ActiveKey = KeySpec('')
HotkeyClearFunctions = []

def register(key, callback):
    registerSpec(KeySpec.fromTuple(key), callback)

def OnHotkeysClear(func):
    HotkeyClearFunctions.append(func)
    return func

def clear():
    global HotkeyClearFunctions

    release_all_modifiers().run()
    for func in HotkeyClearFunctions:
        func()
    
def registerSpec(keySpec, command):
    global KeyBindings
    if hasattr(command, "pylewm_callback"):
        command = command.pylewm_callback
    if keySpec.key not in KeyBindings:
        KeyBindings[keySpec.key] = []
    KeyBindings[keySpec.key].append((keySpec, command))

def handle_python(isKeyDown, keyCode, scanCode):
    absorbKey = False
        
    # Handle modifiers
    isMod = 0
    isMod |= ActiveKey.alt.update(keyCode, isKeyDown, win32con.VK_LMENU, win32con.VK_RMENU)
    isMod |= ActiveKey.shift.update(keyCode, isKeyDown, win32con.VK_LSHIFT, win32con.VK_RSHIFT)
    isMod |= ActiveKey.ctrl.update(keyCode, isKeyDown, win32con.VK_LCONTROL, win32con.VK_RCONTROL)
    isMod |= ActiveKey.win.update(keyCode, isKeyDown, win32con.VK_LWIN, win32con.VK_RWIN)
    isMod |= ActiveKey.app.update(keyCode, isKeyDown, win32con.VK_APPS, 0)

    # Update active key
    ActiveKey.key = VKToChr(keyCode, scanCode)
    ActiveKey.down = isKeyDown

    # Check modes
    if ModeStack:
        with ModeLock:
            if ModeStack:
                handle_type = ModeStack[0].handle_key(ActiveKey, isMod)
                if handle_type is not None:
                    return handle_type

    # Check keybinds
    if ActiveKey.key in KeyBindings:
        for bnd in KeyBindings[ActiveKey.key]:
            if bnd[0].equals_combo(ActiveKey):
                absorbKey = True
                if ActiveKey.down:
                    queue_command(bnd[1])
                elif hasattr(bnd[1], "release_event"):
                        queue_command(bnd[1].release_event)

    if keyCode == win32con.VK_F15:
        return True
    return absorbKey

# TODO: Complete this map
VK_MAP = {
    win32con.VK_ESCAPE: "esc",
    win32con.VK_TAB: "tab",
    win32con.VK_F1: "f1",
    win32con.VK_F2: "f2",
    win32con.VK_F3: "f3",
    win32con.VK_F4: "f4",
    win32con.VK_F5: "f5",
    win32con.VK_F6: "f6",
    win32con.VK_F7: "f7",
    win32con.VK_F8: "f8",
    win32con.VK_F9: "f9",
    win32con.VK_F10: "f10",
    win32con.VK_F11: "f11",
    win32con.VK_F12: "f12",
    win32con.VK_LCONTROL: "lctrl",
    win32con.VK_RCONTROL: "rctrl",
    win32con.VK_LMENU: "lalt",
    win32con.VK_RMENU: "ralt",
    win32con.VK_LSHIFT: "lshift",
    win32con.VK_RSHIFT: "rshift",
    win32con.VK_APPS: "app",
    win32con.VK_RETURN: "enter",
    win32con.VK_BACK: "backspace",
    win32con.VK_LEFT: "left",
    win32con.VK_RIGHT: "right",
    win32con.VK_UP: "up",
    win32con.VK_DOWN: "down",
}

KEY_MAP = { key:vk for vk,key in VK_MAP.items() }

KBState = (ctypes.c_byte * 256)()
def VKToChr(vk, sc):
    if vk in VK_MAP:
        return VK_MAP[vk]

    MAPVK_VK_TO_CHAR = 2
    charValue = windll.user32.MapVirtualKeyA(vk, MAPVK_VK_TO_CHAR)
    if charValue < 0:
        # if less then 0 then it was a deadkey
        return ""
    if charValue == 0:
        # Could not be translated
        return ""

    return chr(charValue).lower()

def wait_for_hotkeys():
    def handle_keyboard_windows(nCode, wParam, lParam):
        if nCode < 0:
            return winfuncs.CallNextHookEx(keyboardHook, nCode, wParam, lParam)

        isKeyDown = False
        isKeyUp = False
        if wParam == win32con.WM_KEYDOWN or wParam == win32con.WM_SYSKEYDOWN:
            isKeyDown = True
        elif wParam == win32con.WM_KEYUP or wParam == win32con.WM_SYSKEYUP:
            isKeyUp = True

        keyInfo = winfuncs.CastToKbDllHookStruct(lParam)
        
        shouldContinue = True
        if isKeyDown or isKeyUp:
            shouldContinue = not handle_python(isKeyDown, keyInfo.vkCode, keyInfo.scanCode)
        if shouldContinue:
            return winfuncs.CallNextHookEx(keyboardHook, nCode, wParam, lParam)
        return 1

    def handle_mouse_windows(nCode, wParam, lParam):
        if wParam == win32con.WM_LBUTTONDOWN:
            MouseState.LEFT_MOUSE_DOWN = True
        elif wParam == win32con.WM_LBUTTONUP:
            MouseState.LEFT_MOUSE_DOWN = False
        elif wParam == win32con.WM_RBUTTONDOWN:
            MouseState.RIGHT_MOUSE_DOWN = True
        elif wParam == win32con.WM_RBUTTONUP:
            MouseState.RIGHT_MOUSE_DOWN = False

        for proc in MouseState.MOUSE_HOOKS:
            if proc(wParam):
                return 1

        return winfuncs.CallNextHookEx(mouseHook, nCode, wParam, lParam)

    modulePtr = winfuncs.GetModuleHandleW(None)

    keyboardHandlePtr = winfuncs.HOOKPROC(handle_keyboard_windows)
    keyboardHook = winfuncs.SetWindowsHookExW(win32con.WH_KEYBOARD_LL, keyboardHandlePtr, modulePtr, 0)
    atexit.register(winfuncs.UnhookWindowsHookEx, keyboardHook)

    mouseHandlePtr = winfuncs.HOOKPROC(handle_mouse_windows)
    mouseHook = winfuncs.SetWindowsHookExW(win32con.WH_MOUSE_LL, mouseHandlePtr, modulePtr, 0)
    atexit.register(winfuncs.UnhookWindowsHookEx, mouseHook)

    message = winfuncs.w.MSG()
    while not pylewm.commands.stopped:
        result = winfuncs.GetMessageW(byref(message), None, 0, 0)
        if result == -1 or result == 0:
            break

        winfuncs.TranslateMessage(byref(message))
        winfuncs.DispatchMessageW(byref(message))