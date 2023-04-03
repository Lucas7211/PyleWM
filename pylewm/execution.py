from pylewm.sendkeys import sendKey
from pylewm.commands import PyleCommand, PyleTask
import pylewm.config

import os
import ctypes
import ctypes.wintypes as wintypes
import win32con
import win32process
import win32security
import win32api
import subprocess
import pywintypes
import shutil

SpawnAsUserSecurityToken = None

@PyleCommand
def start_menu():
    """ Open the start menu. """
    sendKey(('ctrl', 'esc'))

@PyleCommand
def run(args, cwd=None, as_admin=False, cmd_window=False):
    """ Run an arbitrary command. """
    if isinstance(args, str):
        args = [args]
    args = list(args)
    
    if cwd is None:
        cwd = os.getenv("USERPROFILE")

    escaped_commandline = ""
    for arg in args:
        escaped_commandline += '"'
        escaped_commandline += arg
        escaped_commandline += '" '

    # Try to lookup where the exe is from PATH
    executable = args[0]
    if not os.path.isfile(executable):
        executable = shutil.which(executable)

    startup_info = STARTUPINFO()
    startup_info.dwFlags = 0x4 # STARTF_USEPOSITION
    startup_info.dwX = -19797
    startup_info.dwY = -19797
    process_information = PROCESS_INFORMATION()
    
    if as_admin:
        success = ctypes.windll.kernel32.CreateProcessW(executable, escaped_commandline, 0, 0, False,
                    win32con.CREATE_NO_WINDOW if not cmd_window else win32con.CREATE_NEW_CONSOLE, None, cwd,
                    ctypes.pointer(startup_info), ctypes.pointer(process_information))
    else:
        # We have to do all this nonsense to spawn the process
        # as the logged in user, rather than as the administrator
        # that PyleWM is running as
        global SpawnAsUserSecurityToken
        if SpawnAsUserSecurityToken is None:
            shell_window = ctypes.windll.user32.GetShellWindow()
            thread_id, process_id = win32process.GetWindowThreadProcessId(shell_window)
            shell_handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION, False, process_id)
            shell_token = win32security.OpenProcessToken(shell_handle, win32con.TOKEN_DUPLICATE)
            
            SpawnAsUserSecurityToken = win32security.DuplicateTokenEx(shell_token, win32security.SecurityImpersonation,
                        win32con.TOKEN_QUERY | win32con.TOKEN_ASSIGN_PRIMARY | win32con.TOKEN_DUPLICATE
                        | win32con.TOKEN_ADJUST_DEFAULT | 0x0100,
                        win32security.TokenPrimary, None)

        success = ctypes.windll.advapi32.CreateProcessWithTokenW(int(SpawnAsUserSecurityToken), 0, executable, escaped_commandline,
                    win32con.CREATE_NO_WINDOW if not cmd_window else win32con.CREATE_NEW_CONSOLE, None, cwd,
                    ctypes.pointer(startup_info), ctypes.pointer(process_information))

        if not success:
            error = ctypes.get_last_error()
            raise pywintypes.error(
                error, 'CreateProcessWithTokenW',
                win32api.FormatMessageW(error))

@PyleCommand
def run_shell(args, cwd=None):
    """ Run an arbitrary command. """
    if isinstance(args, str):
        args = [args]
    args = list(args)
    
    if cwd is None:
        cwd = os.getenv("USERPROFILE")

    subprocess.call(
        args, shell=True, cwd=cwd,
        creationflags=subprocess.DETACHED_PROCESS|subprocess.CREATE_NEW_PROCESS_GROUP
    )

@PyleCommand
def command_prompt(cwd=None, as_admin=False):
    if as_admin:
        run(["start", "cmd.exe"], cwd=cwd, as_admin=True).run()
    else:
        run(["cmd.exe"], cwd=cwd, cmd_window=True).run()

@PyleCommand
def file_explorer(cwd=None):
    cmd = ["explorer.exe"]
    if cwd:
        cmd.append(cwd)
    run_shell(cmd).run()

@PyleCommand
def this_pc(cwd=None):
    cmd = ["explorer.exe", "/n,", "/e,", "/select,", "C:\\"]
    run_shell(cmd).run()

@PyleCommand
def open_config(cwd=None):
    file_explorer(pylewm.config.get_config_dir()).run()

@PyleCommand
def start_screenclip(mode="Rectangle"):
    pylewm.hotkeys.clear()
    run_shell(["start", f"ms-screenclip:?clippingMode={mode}"]).run()

@PyleCommand
def start_snippingtool(mode="Rectangle"):
    pylewm.hotkeys.clear()
    subprocess.call(
        ["SnippingTool", "/clip"], shell=True,
        creationflags=subprocess.DETACHED_PROCESS|subprocess.CREATE_NEW_PROCESS_GROUP
    )

@PyleTask(name="Toggle Taskbar Visibility")
@PyleCommand
def toggle_taskbar_visibility():
    """ Toggle whether the taskbar is visible or not """
    pylewm.config.HideTaskbar = not pylewm.config.HideTaskbar

@PyleCommand
def toggle_taskbar_and_open_start_menu():
    """ Toggle whether the taskbar is visible or not, and open the start menu when becoming visible """
    if pylewm.config.HideTaskbar:
        start_menu().run()
    pylewm.config.HideTaskbar = not pylewm.config.HideTaskbar

@PyleTask(name="Lock the Screen")
@PyleCommand
def toggle_taskbar_visibility():
    """ Lock the computer and show the windows lock screen """
    ctypes.windll.user32.LockWorkStation()
    

class STARTUPINFO(ctypes.Structure):
    _fields_ = (
        ('cb',              wintypes.DWORD),
        ('lpReserved',      wintypes.LPWSTR),
        ('lpDesktop',       wintypes.LPWSTR),
        ('lpTitle',         wintypes.LPWSTR),
        ('dwX',             wintypes.DWORD),
        ('dwY',             wintypes.DWORD),
        ('dwXSize',         wintypes.DWORD),
        ('dwYSize',         wintypes.DWORD),
        ('dwXCountChars',   wintypes.DWORD),
        ('dwYCountChars',   wintypes.DWORD),
        ('dwFillAttribute', wintypes.DWORD),
        ('dwFlags',         wintypes.DWORD),
        ('wShowWindow',     wintypes.WORD),
        ('cbReserved2',     wintypes.WORD),
        ('lpReserved2',     wintypes.LPBYTE),
        ('hStdInput',       wintypes.HANDLE),
        ('hStdOutput',      wintypes.HANDLE),
        ('hStdError',       wintypes.HANDLE),
    )

class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = (
        ('hProcess',    wintypes.HANDLE),
        ('hThread',     wintypes.HANDLE),
        ('dwProcessId', wintypes.DWORD),
        ('dwThreadId',  wintypes.DWORD)
    )