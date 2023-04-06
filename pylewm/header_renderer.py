import multiprocessing
import pylewm.winproxy.winfuncs as winfuncs
from pylewm.rects import Rect
import ctypes as c
import ctypes.wintypes as w

import win32con
import time
import threading
import faulthandler

CommandQueue : multiprocessing.Queue = None
OutputQueue : multiprocessing.Queue = None

class RenderState:
    TitleFont = None
    Running = False
    Headers : dict[int, 'RenderHeaderWindow'] = {}
    ClassPtr = None
    WndProc = None

def window_proc(hwnd, message, wParam, lParam):
    for id, header in RenderState.Headers.items():
        if header.hwnd == hwnd:
            return header.handle_message(message, wParam, lParam)
    return winfuncs.DefWindowProcW(hwnd, message, wParam, lParam)

def create_class():
    if RenderState.ClassPtr:
        return RenderState.ClassPtr

    module_handle = winfuncs.GetModuleHandleW(None)
    RenderState.WndProc = winfuncs.WNDPROC(window_proc)

    classdesc = winfuncs.WNDCLASSEX()
    classdesc.cbSize = c.sizeof(winfuncs.WNDCLASSEX)
    classdesc.style = winfuncs.CS_HREDRAW | winfuncs.CS_VREDRAW
    classdesc.lpfnWndProc = RenderState.WndProc
    classdesc.cbClsExtra = 0
    classdesc.cbWndExtra = 0
    classdesc.hInstance = module_handle
    classdesc.hIcon = 0
    classdesc.hCursor = 0
    classdesc.hBrush = 0
    classdesc.lpszMenuName = 0
    classdesc.lpszClassName = "PyleWM_Header"
    classdesc.hIconSm = 0
    
    RenderState.ClassPtr = c.windll.user32.RegisterClassExW(c.byref(classdesc))

class RenderHeaderWindow:
    def __init__(self, header_id, target_hwnd, entries):
        self.target_hwnd = target_hwnd
        self.entries = entries
        self.state = {}
        self.header_id = header_id
        self.repaint = True
        self.last_paint = 0
        self.set_timestamp = 0
        self.create_timestamp = time.time() 
        self.hwnd_change_timestamp = 0
        self.closed = False
        self.visible = True
        self.applied_position = []

        module_handle = winfuncs.GetModuleHandleW(None)

        self.window_class = "PyleWM_Header"
        self.window_title = "PyleWM_Header"
        self.target_position = winfuncs.w.RECT()
        create_class()
        
        self.hwnd = winfuncs.CreateWindowExW(
            winfuncs.WS_EX_NOACTIVATE,
            self.window_class, self.window_title,
            0,
            0, 0, 0, 0,
            0, 0,
            module_handle, None)

        winfuncs.SetWindowLongA(self.hwnd, winfuncs.GWL_STYLE, 0)
        winfuncs.ShowWindow(self.hwnd, winfuncs.SW_SHOW)
        winfuncs.UpdateWindow(self.hwnd)
        winfuncs.SetWindowPos(self.hwnd, winfuncs.HWND_TOPMOST, 0, 0, 0, 0, winfuncs.SWP_NOACTIVATE | winfuncs.SWP_NOMOVE | winfuncs.SWP_NOSIZE | winfuncs.SWP_ASYNCWINDOWPOS | winfuncs.SWP_NOREDRAW)

        RenderState.Headers[header_id] = self

    def set(self, target_hwnd, entries, state):
        if target_hwnd != self.target_hwnd:
            self.target_hwnd = target_hwnd
            self.hwnd_change_timestamp = time.time()
        self.entries = entries
        self.state = state
        self.set_timestamp = time.time()
        self.update()
        self.repaint = True
        winfuncs.InvalidateRect(self.hwnd, None, False)

    def to_colorref(self, color):
        return int(color[0])|int(color[1])<<8|int(color[2])<<16

    def paint(self):
        self.repaint = False
        self.last_paint = time.time()

        if not RenderState.TitleFont:
            RenderState.TitleFont = c.windll.gdi32.CreateFontW(
                16, 0, 0, 0, win32con.FW_BOLD,
                0, 0, 0, win32con.DEFAULT_CHARSET, win32con.OUT_OUTLINE_PRECIS,
                win32con.CLIP_DEFAULT_PRECIS, win32con.CLEARTYPE_QUALITY, win32con.VARIABLE_PITCH,
                "Terminus (TTF) for Windows",
            )

        ps = winfuncs.PAINTSTRUCT()
        dc = c.windll.user32.BeginPaint(self.hwnd, c.byref(ps))

        width = self.applied_position[2]
        height = self.applied_position[3]
        
        border_pen = c.windll.gdi32.CreatePen(win32con.PS_SOLID, self.to_colorref((0, 0, 0)))

        if self.entries:
            entry_width = width // len(self.entries)
            for i, entry in enumerate(self.entries):
                x = entry_width*i

                box_width = entry_width

                is_last_entry = i == len(self.entries)-1
                if is_last_entry:
                    box_width = width-x

                bg_brush = c.windll.gdi32.CreateSolidBrush(self.to_colorref(entry["bg_color"]))

                c.windll.gdi32.SelectObject(dc, bg_brush)
                c.windll.gdi32.Rectangle(dc, x, 0, x+box_width, height)

                c.windll.gdi32.SetBkMode(dc, win32con.TRANSPARENT)
                c.windll.gdi32.SetTextColor(dc, self.to_colorref(entry["text_color"]))

                text_rect = w.RECT()
                text_rect.left = x+10
                text_rect.right = x+box_width-10
                text_rect.top = 0
                text_rect.bottom = height

                c.windll.gdi32.SelectObject(dc, RenderState.TitleFont)

                c.windll.user32.DrawTextW(dc,
                    entry["title"], len(entry["title"]),
                    c.pointer(text_rect),
                    win32con.DT_WORD_ELLIPSIS | win32con.DT_NOPREFIX | win32con.DT_VCENTER | win32con.DT_SINGLELINE
                )

                if is_last_entry and self.state.get("pending", False):
                    glyph = "-PENDING-"
                    c.windll.user32.DrawTextW(dc,
                        glyph, len(glyph),
                        c.pointer(text_rect),
                        win32con.DT_WORD_ELLIPSIS | win32con.DT_NOPREFIX | win32con.DT_RIGHT | win32con.DT_VCENTER | win32con.DT_SINGLELINE
                    )

                c.windll.gdi32.DeleteObject(bg_brush)


        c.windll.gdi32.DeleteObject(border_pen)
        dc = c.windll.user32.EndPaint(self.hwnd, c.byref(ps))

    def update(self):
        if self.closed:
            return
        self.update_visibility()
        if self.visible:
            self.update_position()

    def update_visibility(self):
        should_show = False
        if not winfuncs.IsWindow(self.target_hwnd):
            should_show = False
        elif winfuncs.IsWindowVisible(self.target_hwnd):
            should_show = True
        elif time.time() - self.set_timestamp < 0.3:
            should_show = True

        if should_show:
            if not self.visible:
                self.visible = True
                winfuncs.ShowWindowAsync(self.hwnd, winfuncs.SW_SHOWNOACTIVATE)
        else:
            if self.visible:
                self.visible = False
                winfuncs.ShowWindowAsync(self.hwnd, winfuncs.SW_HIDE)

    def force_reposition(self):
        self.hwnd_change_timestamp = 0.0

    def update_position(self):
        if self.applied_position and time.time() - self.hwnd_change_timestamp < 0.3 and time.time() - self.create_timestamp > 0.3:
            return
        if not winfuncs.IsWindow(self.target_hwnd):
            return
        has_rect = winfuncs.GetWindowRect(self.target_hwnd, winfuncs.c.byref(self.target_position))
        if not has_rect:
            return

        wanted_position = [
            self.target_position.left + 6,
            self.target_position.top - 30,
            self.target_position.right - self.target_position.left - 12,
            32,
        ]

        if wanted_position != self.applied_position:
            self.applied_position = wanted_position
            self.repaint = True
            winfuncs.SetWindowPos(
                self.hwnd,
                winfuncs.HWND_TOPMOST,
                wanted_position[0], wanted_position[1],
                wanted_position[2], wanted_position[3],
                winfuncs.SWP_NOACTIVATE
            )

    def get_entry_index_at_pos(self, lParam):
        if not self.entries:
            return None

        x = (lParam & 0x0000ffff)
        y = (lParam & 0xffff0000) >> 16

        width = self.applied_position[2]
        entry_width = width // len(self.entries)

        return min(x // entry_width, len(self.entries)-1)

    def handle_message(self, message, wParam, lParam):
        if message == win32con.WM_DESTROY:
            self.close()
            return 0
        elif message == win32con.WM_PAINT:
            if self.repaint or time.time() > self.last_paint + 1.0:
                self.paint()
            return 0
        elif message == win32con.WM_SIZE or message == win32con.WM_MOVE:
            self.repaint = True
            return 0
        elif message == win32con.WM_LBUTTONUP:
            entry = self.get_entry_index_at_pos(lParam)
            if entry is not None:
                OutputQueue.put([self.header_id, "click", 0, entry])
            return 0
        elif message == win32con.WM_MBUTTONUP:
            entry = self.get_entry_index_at_pos(lParam)
            if entry is not None:
                OutputQueue.put([self.header_id, "click", 1, entry])
            return 0
        elif message == win32con.WM_RBUTTONUP:
            entry = self.get_entry_index_at_pos(lParam)
            if entry is not None:
                OutputQueue.put([self.header_id, "click", 2, entry])
            return 0
        return winfuncs.DefWindowProcW(self.hwnd, message, wParam, lParam)
        
    def close(self):
        if self.closed:
            return
        self.closed = True
        winfuncs.DestroyWindow(self.hwnd)

        del RenderState.Headers[self.header_id]

def update_headers():
    for id, header in RenderState.Headers.items():
        header.update()

def handle_command(cmd):
    if cmd[0] == "create":
        header_id = cmd[1]
        target_hwnd = cmd[2]
        entries = cmd[3]
        header = RenderHeaderWindow(header_id, target_hwnd, entries)
    elif cmd[0] == "update":
        header_id = cmd[1]
        target_hwnd = cmd[2]
        entries = cmd[3]
        state = cmd[4]
        if header_id in RenderState.Headers:
            RenderState.Headers[header_id].set(target_hwnd, entries, state)
    elif cmd[0] == "close":
        header_id = cmd[1]
        if header_id in RenderState.Headers:
            RenderState.Headers[header_id].close()

def run():
    RenderState.Running = True
    faulthandler.enable()

    message = w.MSG()
    while RenderState.Running:
        while winfuncs.PeekMessageW(c.byref(message), None, 0, 0, winfuncs.PM_REMOVE):
            winfuncs.TranslateMessage(c.byref(message))
            winfuncs.DispatchMessageW(c.byref(message))

        update_headers()

        cmd = None
        try:
            cmd = CommandQueue.get(block=True, timeout=1.0/60.0)
        except:
            pass

        if cmd:
            handle_command(cmd)

        while CommandQueue.qsize() != 0:
            cmd = None
            try:
                cmd = CommandQueue.get(block=False)
            except:
                pass
            if cmd:
                handle_command(cmd)

if __name__ == "__main__":
    run()