import sys, time, threading
from functools import partial
import traceback, os
import subprocess
import argparse
import faulthandler

import pystray
from PIL import Image

import threading
import atexit

from pylewm.commands import PyleCommand, InitFunctions, CommandQueue, queue_pyle_command, run_pyle_command, Commands

import pylewm.winproxy.winupdate
import pylewm.windows
import pylewm.hotkeys
import pylewm.commands

tray_icon = None

def key_process_thread():
    pylewm.hotkeys.queue_command = queue_pyle_command
    pylewm.hotkeys.wait_for_hotkeys()

def command_thread():
    Commands.run_with_update(
        updatefunc = pylewm.windows.window_update
    )

def winproxy_thread():
    pylewm.winproxy.winupdate.ProxyCommands.run_with_update(
        updatefunc = pylewm.winproxy.winupdate.proxy_update
    )

def find_pythonw_executable():
    dir, name = os.path.split(sys.executable)

    # Switch from python.exe to pythonw.exe if we can
    if name.lower() == "python.exe":
        pythonw_path = os.path.join(dir, "pythonw.exe")
        if os.path.isfile(pythonw_path):
            return pythonw_path

    return sys.executable

def init_registry_vars():
    import winreg
    reg_conn = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)

    # Allow stealing focus from programs
    focus_key = winreg.OpenKey(reg_conn, r"Control Panel\Desktop", access=winreg.KEY_WRITE)
    winreg.SetValueEx(focus_key, "ForegroundLockTimeout", 0, winreg.REG_DWORD, 0)

    winreg.CloseKey(focus_key)
    winreg.CloseKey(reg_conn)

def start():
    import ctypes
    if not ctypes.windll.shell32.IsUserAnAdmin():
        script_name = sys.argv[0]
        if not script_name.endswith(".py"):
            script_name = "-m pylewm"
        argument_str = " ".join((script_name, *sys.argv[1:]))
        ctypes.windll.shell32.ShellExecuteW(None, "runas", find_pythonw_executable(), argument_str, None, 1)
        sys.exit()
        return
    else:
        # Set up registry variables for running PyleWM correctly
        init_registry_vars()

    faulthandler.enable()
    pylewm.config.apply()

    for fun in InitFunctions:
        fun()

    threading.Thread(target=key_process_thread, daemon=True).start()
    threading.Thread(target=command_thread, daemon=True).start()
    threading.Thread(target=winproxy_thread, daemon=True).start()

    atexit.register(pylewm.winproxy.winupdate.proxy_cleanup)

    global tray_icon
    tray_icon = pystray.Icon('PyleWM')
    png_path = os.path.join(os.path.dirname(__file__), "PyleWM.png")
    tray_icon.icon = Image.open(png_path)
    tray_icon.title = "PyleWM"
    tray_icon.menu = pystray.Menu(
        pystray.MenuItem("Open Config Directory", lambda: run_pyle_command(pylewm.execution.open_config)),
        pystray.MenuItem("Restart", lambda: run_pyle_command(restart)),
        pystray.MenuItem("Quit", lambda: run_pyle_command(quit)),
    )
    tray_icon.run()

def stop_threads():
    pylewm.commands.stopped = True
    Commands.queue_event.set()
    pylewm.winproxy.winupdate.ProxyCommands.queue_event.set()
    tray_icon.stop()

@PyleCommand
def restart():
    stop_threads()
    pylewm.winproxy.winupdate.proxy_cleanup()

    os.execl(sys.executable, sys.executable, *sys.argv)
    sys.exit()
    
@PyleCommand
def quit():
    stop_threads()
    sys.exit()