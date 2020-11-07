from pylewm.sendkeys import sendKey
from pylewm.commands import PyleCommand
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

@PyleCommand.Threaded
def start_menu():
    """ Open the start menu. """
    sendKey(('ctrl', 'esc'))
    
@PyleCommand.Threaded
def run(args, cwd=None, as_admin=False, cmd_window=False):
    """ Run an arbitrary command. """
    if isinstance(args, str):
        args = [args]
    args = list(args)
    
    if cwd is None:
        cwd = os.getenv("USERPROFILE")
    
    if as_admin:
        subprocess.call(args, shell=True, cwd=cwd)
    else:
        # We have to do all this nonsense to spawn the process
        # as the logged in user, rather than as the administrator
        # that PyleWM is running as
        startup_info = STARTUPINFO()
        process_information = PROCESS_INFORMATION()
        
        shell_window = ctypes.windll.user32.GetShellWindow()
        thread_id, process_id = win32process.GetWindowThreadProcessId(shell_window)
        shell_handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION, False, process_id)
        shell_token = win32security.OpenProcessToken(shell_handle, win32con.TOKEN_DUPLICATE)
        
        spawn_token = win32security.DuplicateTokenEx(shell_token, win32security.SecurityImpersonation,
                    win32con.TOKEN_QUERY | win32con.TOKEN_ASSIGN_PRIMARY | win32con.TOKEN_DUPLICATE
                    | win32con.TOKEN_ADJUST_DEFAULT | 0x0100,
                    win32security.TokenPrimary, None)

        escaped_commandline = ""
        for arg in args:
            escaped_commandline += '"'
            escaped_commandline += arg
            escaped_commandline += '" '

        success = ctypes.windll.advapi32.CreateProcessWithTokenW(int(spawn_token), 0, args[0], escaped_commandline,
                    win32con.CREATE_NO_WINDOW if not cmd_window else win32con.CREATE_NEW_CONSOLE, None, os.getcwd(),
                    ctypes.pointer(startup_info), ctypes.pointer(process_information))

        if not success:
            error = ctypes.get_last_error()
            raise pywintypes.error(
                error, 'CreateProcessWithTokenW',
                win32api.FormatMessageW(error))


@PyleCommand.Threaded
def command_prompt(cwd=None, as_admin=False):
    if as_admin:
        run(["start", "cmd.exe"], cwd=cwd, as_admin=True).run()
    else:
        run(["cmd.exe"], cwd=cwd, cmd_window=True).run()

@PyleCommand.Threaded
def file_explorer(cwd=None):
    cmd = ["explorer.exe"]
    if cwd:
        cmd.append(cwd)
    run(cmd, as_admin=True).run()

@PyleCommand.Threaded
def this_pc(cwd=None):
    cmd = ["explorer.exe", "/n,", "/e,", "/select,", "C:\\"]
    run(cmd, as_admin=True).run()

@PyleCommand.Threaded
def open_config(cwd=None):
    file_explorer(pylewm.config.get_config_dir()).run()

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