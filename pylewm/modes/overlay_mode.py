import pygame
import pylewm.hotkeys
import threading
import win32gui
import win32con
import win32api
import os
import time
from pylewm.rects import Rect

OVERLAY_WINDOW = None
class OverlayWindow:
    def __init__(self):
        self.shown = False
        self.rect = Rect()
        self.bg_color = (255, 192, 203)

        self.thread = threading.Thread(target = self.window_loop)
        self.thread.start()

    def show(self, mode, rect):
        self.rect = rect
        self.mode = mode
        self.shown = True

    def hide(self):
        self.shown = False
        self.mode = None

    def draw_box(self, rect, color):
        pygame.draw.rect(self.display, color, pygame.Rect(rect.left, rect.top, rect.width, rect.height))

    def draw_border(self, rect, color, width):
        pygame.draw.rect(self.display, color, pygame.Rect(rect.left, rect.top, width, rect.height))
        pygame.draw.rect(self.display, color, pygame.Rect(rect.right - width, rect.top, width, rect.height))
        pygame.draw.rect(self.display, color, pygame.Rect(rect.left + width, rect.top, rect.width - width*2, width))
        pygame.draw.rect(self.display, color, pygame.Rect(rect.left + width, rect.bottom - width, rect.width - width*2, width))

    def draw_text(self, text, color, rect, align = (0.0, 0.0)):
        img = self.font.render(text, True, color)
        blit_dim = [img.get_width(), img.get_height()]

        if blit_dim[0] > rect.width:
            blit_dim[0] = rect.width
        else:
            rect.shift((align[0] * (rect.width - blit_dim[0]), 0))

        if blit_dim[1] > rect.height:
            blit_dim[1] = rect.height
        else:
            rect.shift((0, align[1] * (rect.height - blit_dim[1])))

        self.display.blit(img, (rect.left, rect.top), (0, 0, blit_dim[0], blit_dim[1]))

    def window_loop(self):
        pygame.init()

        while not pylewm.commands.stopped:
            while not self.shown and not pylewm.commands.stopped:
                time.sleep(0.1)
                pass

            if pylewm.commands.stopped:
                break
            
            pygame.display.init()

            self.display = pygame.display.set_mode((100, 100), pygame.NOFRAME | pygame.HIDDEN)
            pygame.display.set_caption("PyleWM_Internal")

            self.hwnd = pygame.display.get_wm_info()["window"]
            win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)
            win32gui.SetLayeredWindowAttributes(self.hwnd, win32api.RGB(*self.bg_color), 0, win32con.LWA_COLORKEY)

            ttf_path = os.path.join(os.path.dirname(__file__), "..", "data", "TerminusTTF-Bold-4.47.0.ttf")
            self.font = pygame.font.Font(ttf_path, 24)
            if not self.font:
                self.font = pygame.font.SysFont(None, 24)

            self.display = pygame.display.set_mode((self.rect.width, self.rect.height), pygame.NOFRAME | pygame.HIDDEN)
            win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, self.rect.left, self.rect.top, self.rect.width, self.rect.height, 0)
            win32gui.ShowWindow(self.hwnd, win32con.SW_SHOWNORMAL)

            while self.shown and not pylewm.commands.stopped:
                while pygame.event.get():
                    pass
                self.display.fill(self.bg_color)
                with pylewm.hotkeys.ModeLock:
                    if self.mode:
                        self.mode.draw(self)
                pygame.display.update()

            pygame.display.quit()

        pygame.quit()

class OverlayMode(pylewm.hotkeys.Mode):
    def __init__(self, hotkeys):
        super(OverlayMode, self).__init__(hotkeys)

    def overlay_window(self, window):
        global OVERLAY_WINDOW
        if not OVERLAY_WINDOW:
            OVERLAY_WINDOW = OverlayWindow()
        OVERLAY_WINDOW.show(self, window.rect)

    def overlay_monitor(self, monitor):
        global OVERLAY_WINDOW
        if not OVERLAY_WINDOW:
            OVERLAY_WINDOW = OverlayWindow()

        rect = monitor.rect.copy()
        rect.bottom = rect.bottom - 3
        OVERLAY_WINDOW.show(self, rect)

    def end_mode(self):
        OVERLAY_WINDOW.hide()

    def draw(self, overlay):
        pass