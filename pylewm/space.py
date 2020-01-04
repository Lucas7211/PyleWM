from pylewm.layout import SidebarLayout

class Space:
    def __init__(self, rect):
        self.windows = []
        self.rect = rect.copy()
        self.layout = SidebarLayout()

    def update_layout(self):
        self.layout.window_count = len(self.windows)
        for i, window in enumerate(self.windows):
            window.rect = self.layout.get_window_rect(self.rect, i)

    def add_window(self, window):
        window.space = self
        self.windows.append(window)

    def remove_window(self, window):
        self.windows.remove(window)
        window.space = None