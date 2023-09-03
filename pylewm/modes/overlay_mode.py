import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import pygame
import pylewm.hotkeys
import threading
import win32gui
import win32con
import win32api
import time
import re
from pylewm.rects import Rect

OVERLAY_WINDOW = None

class OverlayWindow:
    def __init__(self):
        self.shown = False
        self.initialized = False
        self.dirty = True
        self.overlay_area = pylewm.monitors.DesktopArea
        self.bg_color = (255, 192, 203)

        self.thread = threading.Thread(target = self.window_loop)
        self.thread.start()

    def show(self, mode, rect):
        self.mode = mode
        self.shown = True
        self.render_area = rect
        self.dirty = True
        if self.initialized:
            pygame.event.post(pygame.event.Event(pygame.USEREVENT))

    def hide(self):
        self.shown = False
        self.mode = None

    def rect_overlay_to_draw(self, rect):
        return rect
        """return Rect((
            rect.left + self.render_area.left - self.overlay_area.left,
            rect.top + self.render_area.top - self.overlay_area.top,
            rect.right + self.render_area.left - self.overlay_area.left,
            rect.bottom + self.render_area.top - self.overlay_area.top,
        ))"""

    def draw_box(self, rect, color):
        rect = self.rect_overlay_to_draw(rect)
        pygame.draw.rect(self.display, color, pygame.Rect(rect.left, rect.top, rect.width, rect.height))

    def draw_border(self, rect, color, width):
        rect = self.rect_overlay_to_draw(rect)
        pygame.draw.rect(self.display, color, pygame.Rect(rect.left, rect.top, width, rect.height))
        pygame.draw.rect(self.display, color, pygame.Rect(rect.right - width, rect.top, width, rect.height))
        pygame.draw.rect(self.display, color, pygame.Rect(rect.left + width, rect.top, rect.width - width*2, width))
        pygame.draw.rect(self.display, color, pygame.Rect(rect.left + width, rect.bottom - width, rect.width - width*2, width))

    def draw_text(self, text, color, rect, align = (0.0, 0.0), font=None, background_box=None):
        rect = self.rect_overlay_to_draw(rect)

        if not font:
            font = self.font

        img = font.render(text, True, color)
        blit_dim = [img.get_width(), img.get_height()]

        if blit_dim[0] > rect.width:
            blit_dim[0] = rect.width
        else:
            rect = rect.shifted((align[0] * (rect.width - blit_dim[0]), 0))

        if blit_dim[1] > rect.height:
            blit_dim[1] = rect.height
        else:
            rect = rect.shifted((0, align[1] * (rect.height - blit_dim[1])))

        if background_box:
            pygame.draw.rect(self.display,
                background_box, pygame.Rect(
                    rect.left - 2, rect.top - 1,
                    blit_dim[0] + 2, blit_dim[1] + 2,
            ))
        self.display.blit(img, (rect.left, rect.top), (0, 0, blit_dim[0], blit_dim[1]))

    def window_loop(self):
        pygame.init()

        # ttf_path = os.path.join(os.path.dirname(__file__), "..", "data", "TerminusTTF-Bold-4.47.0.ttf")
        ttf_path = os.path.join(os.path.dirname(__file__), "..", "data", "Terminess-Bold.ttf")
        self.font = pygame.font.Font(ttf_path, 24)
        if not self.font:
            self.font = pygame.font.SysFont(None, 24)

        self.font_small = pygame.font.Font(ttf_path, 16)
        if not self.font:
            self.font_small = pygame.font.SysFont(None, 16)

        self.display = pygame.display.set_mode((100, 100), pygame.NOFRAME | pygame.HIDDEN)
        pygame.display.set_caption("PyleWM_Internal")

        self.hwnd = pygame.display.get_wm_info()["window"]
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)
        win32gui.SetLayeredWindowAttributes(self.hwnd, win32api.RGB(*self.bg_color), 0, win32con.LWA_COLORKEY)

        self.display = pygame.display.set_mode(self.overlay_area.size, pygame.NOFRAME | pygame.SHOWN)
        win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, self.overlay_area.left, self.overlay_area.top, self.overlay_area.width, self.overlay_area.height, win32con.SWP_NOACTIVATE)
        self.display.fill(self.bg_color)

        self.initialized = True
        while not pylewm.commands.stopped:
            while not self.shown and not pylewm.commands.stopped:
                pygame.time.set_timer(pygame.USEREVENT, 100)
                while pygame.event.wait():
                    pygame.time.set_timer(pygame.USEREVENT, 100)
                    if self.shown or pylewm.commands.stopped:
                        break

            if pylewm.commands.stopped:
                break

            win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, self.render_area.left, self.render_area.top, self.render_area.width, self.render_area.height, win32con.SWP_NOACTIVATE | win32con.SWP_ASYNCWINDOWPOS)
            win32gui.ShowWindow(self.hwnd, win32con.SW_SHOWNOACTIVATE)
            active_time = None

            while self.shown and not pylewm.commands.stopped and self.mode and not self.mode.closed:
                dirty = False
                with pylewm.hotkeys.ModeLock:
                    if self.mode and self.mode in pylewm.hotkeys.ModeStack:
                        if self.mode.should_draw():
                            dirty = True
                            if self.mode.should_clear():
                                self.draw_box(Rect((0,0,self.render_area.width,self.render_area.height)), self.bg_color)
                            self.mode.draw(self)
                if dirty:
                    pygame.display.update()

                if active_time is None:
                    active_time = time.time()
                event = pygame.event.wait(10)
                while event:
                    if (
                        event.type == pygame.MOUSEBUTTONUP
                        or (
                            event.type == pygame.ACTIVEEVENT
                            and hasattr(event, 'gain')
                            and hasattr(event, 'state')
                            and event.gain
                            and event.state == 1
                            and time.time() - active_time > 0.1)
                    ):
                        pos = pygame.mouse.get_pos()
                        if self.mode:
                            with pylewm.hotkeys.ModeLock:
                                self.mode.clicked(pos)
                    event = pygame.event.wait(10)

            self.display.fill(self.bg_color)
            pygame.display.update()
            win32gui.ShowWindow(self.hwnd, win32con.SW_HIDE)

        pygame.quit()

class OverlayMode(pylewm.hotkeys.Mode):
    def __init__(self, hotkeys):
        self.closed = False
        super(OverlayMode, self).__init__(hotkeys)

    def should_draw(self):
        return True

    def should_clear(self):
        return True

    def clicked(self, pos):
        return False

    def overlay_static(self, rect):
        global OVERLAY_WINDOW
        if not OVERLAY_WINDOW:
            OVERLAY_WINDOW = OverlayWindow()
        self.overlay_rect = rect.copy()
        OVERLAY_WINDOW.show(self, self.overlay_rect)

    def overlay_window(self, window):
        global OVERLAY_WINDOW
        if not OVERLAY_WINDOW:
            OVERLAY_WINDOW = OverlayWindow()
        self.overlay_rect = window.real_position
        OVERLAY_WINDOW.show(self, self.overlay_rect)

    def overlay_monitor(self, monitor):
        global OVERLAY_WINDOW
        if not OVERLAY_WINDOW:
            OVERLAY_WINDOW = OverlayWindow()

        self.overlay_rect = monitor.rect.copy()
        self.overlay_rect.bottom = self.overlay_rect.bottom - 3
        OVERLAY_WINDOW.show(self, self.overlay_rect)

    def overlay_global(self):
        global OVERLAY_WINDOW
        if not OVERLAY_WINDOW:
            OVERLAY_WINDOW = OverlayWindow()

        self.overlay_rect = pylewm.monitors.DesktopArea
        OVERLAY_WINDOW.show(self, self.overlay_rect)

    def abs_to_overlay(self, rect):
        return Rect((
            rect.left - self.overlay_rect.left,
            rect.top - self.overlay_rect.top,
            rect.right - self.overlay_rect.left,
            rect.bottom - self.overlay_rect.top,
        ))

    def end_mode(self):
        OVERLAY_WINDOW.hide()

    def draw(self, overlay):
        pass
