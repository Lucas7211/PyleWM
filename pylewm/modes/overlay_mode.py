import pygame
import pylewm.hotkeys
import threading
import win32gui
import win32con
import win32api
from pylewm.rects import Rect


OVERLAY_WINDOW = None
class OverlayWindow:
    def __init__(self):
        self.thread = threading.Thread(target = self.window_loop)
        self.thread.start()
        self.shown = False
        self.rect = Rect()
        self.bg_color = (255, 192, 203)

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

    def window_loop(self):
        pygame.init()

        self.display = pygame.display.set_mode((100, 100), pygame.NOFRAME | pygame.HIDDEN)
        pygame.display.set_caption("PyleWM_Internal")

        self.hwnd = pygame.display.get_wm_info()["window"]
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)
        win32gui.SetLayeredWindowAttributes(self.hwnd, win32api.RGB(*self.bg_color), 0, win32con.LWA_COLORKEY)

        while not pylewm.commands.stopped:
            while not self.shown:
                while pygame.event.get():
                    pass
                pygame.display.update()

            self.display = pygame.display.set_mode((self.rect.width, self.rect.height), pygame.NOFRAME | pygame.HIDDEN)
            win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, self.rect.left, self.rect.top, self.rect.width, self.rect.height, 0)
            win32gui.ShowWindow(self.hwnd, win32con.SW_SHOWNORMAL)

            while self.shown:
                while pygame.event.get():
                    pass
                self.display.fill(self.bg_color)
                with pylewm.hotkeys.ModeLock:
                    if self.mode:
                        self.mode.draw(self)
                pygame.display.update()

            win32gui.ShowWindow(self.hwnd, win32con.SW_HIDE)

        pygame.quit()

class OverlayMode(pylewm.hotkeys.Mode):
    def __init__(self, hotkeys):
        super(OverlayMode, self).__init__(hotkeys)

    def overlay_window(self, window):
        global OVERLAY_WINDOW
        if not OVERLAY_WINDOW:
            OVERLAY_WINDOW = OverlayWindow()
        OVERLAY_WINDOW.show(self, window.rect)

    def end_mode(self):
        OVERLAY_WINDOW.hide()

    def draw(self, overlay):
        pass