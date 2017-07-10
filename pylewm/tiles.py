from pylewm import pyleinit, pyletick, pylecommand
from pylewm.windows import isEmptyWindow, isRelevantWindow
import pylewm.windows
import pylewm.focus
import win32gui, win32con, win32api
from ctypes import CFUNCTYPE, POINTER, c_uint, windll
import atexit

TileWindowOverlap = 4

@pylecommand
def focus_dir(dir):
    """ Focus the neighbouring child to the selected one in a particular direction. """
    tile = FocusTile
    while tile is not None:
        inDir = tile.in_dir(dir)
        if inDir is not None:
            inDir.focus()
            return
        tile = tile.parent
    
    # Fall back on a window-based focus_dir if no tile supports the operation
    pylewm.windows.focus_dir(dir)()

@pylecommand
def focus_next():
    """ Focus the next child in the active tile. """
    tile_bubble(FocusTile, "next")
 
@pylecommand
def focus_prev():
    """ Focus the previous child in the active tile. """
    tile_bubble(FocusTile, "prev")

@pylecommand
def vsplit():
    """ Split the currently active tile vertically. """
    tile_bubble(FocusTile, "vsplit")
    
@pylecommand
def hsplit():
    """ Split the currently active tile horizontally. """
    tile_bubble(FocusTile, "hsplit")
    
@pylecommand
def vextend():
    """ Extend the currently active vertical split by one. """
    tile_bubble(FocusTile, "vextend")
    
@pylecommand
def hextend():
    """ Extend the currently active horizontal split by one. """
    tile_bubble(FocusTile, "hextend")
    
@pylecommand
def extend():
    """ Extend the currently active split by one. """
    tile_bubble(FocusTile, "extend")
    
@pylecommand
def cancel_pending():
    """ Cancel any pending tiles that were opened. """
    global PendingOpenTiles
    for pending in PendingOpenTiles:
        pending.pending = False
    PendingOpenTiles = []
    
def tile_bubble(tile, cmdName):
    if tile is not None:
        if hasattr(tile, cmdName):
            if getattr(tile, cmdName)():
                return True
        return tile_bubble(tile.parent, cmdName)

RootTile = None
PrimaryTile = None
KnownWindows = set()
FocusTile = None
FocusWindow = None
PendingOpenTiles = []
PrevFocusTile = None

class TileBase:
    def __init__(self):
        self.parent = None
        self.childList = []
        self.rect = (0,0,0,0)
        self.focused = False
        self.persistent = False
        self.hidden = False
        self.pending = False
        
    def checkFocus(self):
        for child in self.childList:
            if child.checkFocus():
                return True
        return False
    
    def getInnerFocused(self):
        if not self.focused:
            return None
        for child in self.childList:
            if child.focused:
                return child.getInnerFocused()
        return self
        
    def update(self):
        i = 0
        cnt = len(self.childList)
        while i < cnt:
            if not self.childList[i].update():
                del self.childList[i]
                i -= 1
                cnt -= 1
            i += 1
        return True
        
    def focus(self):
        pass
        
    def in_dir(self, dir, fromChild = None):
        return None
        
    def hide(self):
        for child in self.childList:
            child.hide()
        self.hidden = True
        
    def show(self):
        for child in self.childList:
            child.show()
        self.hidden = False
        
    def isHidden(self):
        return self.hidden
        
    def add(self, tile):
        self.childList.append(tile)
        tile.parent = self
        
    def remove(self, tile):
        self.childList.remove(tile)
        tile.parent = None
        
    def replaceChild(self, fromTile, toTile):
        # print(f"REPLACE {fromTile} out of {self.childList}")
        wasIndex = self.childList.index(fromTile)
        self.remove(fromTile)
        self.add(toTile)
        # Swap the order of children so it's in the same order it was before
        self.childList[wasIndex], self.childList[-1] = self.childList[-1], self.childList[wasIndex]
        
    def next(self):
        return False
        
    def prev(self):
        return False
        
    @property
    def title(self):
        return f"{self.__class__.__name__} {self.rect}"
        
class TileRoot(TileBase):
    def getInnerFocused(self):
        for child in self.childList:
            if child.focused:
                return child.getInnerFocused()
        return None
        
class TileSingular(TileBase):
    def __init__(self):
        self.isMaximize = False
        self.focusChild = None
        self.childMRU = []
        super(TileSingular, self).__init__()
        
    def update(self):
        # Update child status
        i = 0
        cnt = len(self.childList)
        while i < cnt:
            self.childList[i].rect = self.rect
            if not self.childList[i].update():
                self.remove(self.childList[i])
                i -= 1
                cnt -= 1
            i += 1
        if cnt > 0:
            self.pending = False
        if not self.persistent and not self.pending and len(self.childList) == 0:
            return False
        # Update focused status
        self.focused = False
        self.focusChild = None
        for i, child in enumerate(self.childMRU):
            if child.checkFocus():
                if i != 0:
                    self.setFocus(child)
                self.focused = True
                self.focusChild = child
                break
        # Show a window if we don't have one visible
        if len(self.childMRU) != 0 and self.childMRU[0].isHidden():
            self.hideExisting(self.childMRU[0])
            self.childMRU[0].show()
        return True
        
    def hideExisting(self, donthide=0):
        for child in self.childList:
            if child is not donthide and not child.isHidden():
                child.hide()
    
    def setFocus(self, tile):
        self.hideExisting(tile)
        self.childMRU.remove(tile)
        self.childMRU.insert(0, tile)
        
    def focus(self):
        if len(self.childMRU) != 0:
            self.childMRU[0].focus()
        
    def focusTo(self, tile):
        self.setFocus(tile)
        tile.rect = self.rect
        tile.show()
                
    def add(self, tile):
        print(f"ADD {tile.title} / {len(self.childList)} FROM {self.title} = {self.rect}")
        self.hideExisting()
        self.childMRU.insert(0, tile)
        self.childList.append(tile)
        tile.rect = self.rect
        tile.show()
        tile.parent = self
        
    def remove(self, tile):
        print(f"REMOVE {tile.title} / {len(self.childList)} FROM {self.title} = {self.rect}")
        self.childMRU.remove(tile)
        self.childList.remove(tile)
        if tile is self.focusChild:
            if len(self.childMRU) != 0:
                self.focusTo(self.childMRU[0])
            
    def hide(self):
        self.hideExisting()
        self.hidden = True
        
    def show(self):
        if len(self.childMRU) != 0:
            self.childMRU[0].show()
        self.hidden = False
        
    def isHidden(self):
        return self.hidden
        
    def next(self):
        if len(self.childList) <= 1:
            return True
        for i, child in enumerate(self.childList):
            if child is self.focusChild:
                self.focusTo(self.childList[(i+1) % len(self.childList)])
                return True
        return True
        
    def prev(self):
        if len(self.childList) <= 1:
            return True
        for i, child in enumerate(self.childList):
            if child is self.focusChild:
                self.focusTo(self.childList[(i-1) % len(self.childList)])
                return True
        return True
        
    def split(self, splitClass):
        print(f"SPLIT {self.title}")
        print_tree()
        splitTile = splitClass()
        splitTile.rect = self.rect
        self.parent.replaceChild(self, splitTile)
        splitTile.add(self)
        pendingTile = TileSingular()
        pendingTile.pending = True
        splitTile.add(pendingTile)
        PendingOpenTiles.insert(0, pendingTile)
        splitTile.updateRects()
        print(f"AFTER")
        print_tree()
        return True
        
    def hsplit(self):
        return self.split(TileListVertical)
        
    def vsplit(self):
        return self.split(TileListHorizontal)
        
class TileListBase(TileBase):
    def __init__(self):
        self.focusChild = None
        self.lastFocusChild = None
        super(TileListBase, self).__init__()
        
    def update(self):
        # Update child status
        i = 0
        cnt = len(self.childList)
        self.updateRects()
        while i < cnt:
            if not self.childList[i].update():
                self.remove(self.childList[i])
                i -= 1
                cnt -= 1
            i += 1
        if cnt > 0:
            self.pending = False
        if not self.persistent and not self.pending and len(self.childList) == 0:
            return False
        # A list with only one child removes itself and puts the child back on its parent
        if len(self.childList) == 1:
            print(f"COLLAPSE {self.title}")
            child = self.childList[0]
            self.remove(child)
            self.parent.replaceChild(self, child)
            return True
        # Update focused status
        self.focused = False
        self.focusChild = None
        for i, child in enumerate(self.childList):
            if child.checkFocus():
                self.focused = True
                self.focusChild = child
                break
        if self.lastFocusChild is not None and self.lastFocusChild not in self.childList:
            self.lastFocusChild = None
        if self.focusChild is not None:
            self.lastFocusChild = self.focusChild
        return True
        
    def updateRects(self):
        pass
        
    def focus(self):
        setTo = self.focusChild
        if setTo is None:
            setTo = self.lastFocusChild
        if setTo is not None:
            setTo.focus()
                
    def add(self, tile):
        print(f"ADD {tile.title} / {len(self.childList)} FROM {self.title} = {self.rect}")
        self.childList.append(tile)
        self.updateRects()
        tile.show()
        tile.parent = self
        
    def remove(self, tile):
        print(f"REMOVE {tile.title} / {len(self.childList)} FROM {self.title} = {self.rect}")
        self.childList.remove(tile)
        self.updateRects()
            
    def hide(self):
        for child in self.childList:
            child.hide()
        self.hidden = True
        
    def show(self):
        for child in self.childList:
            child.show()
        self.hidden = False
        
    def isHidden(self):
        return self.hidden
                    
    def extend(self):
        pendingTile = TileSingular()
        pendingTile.pending = True
        self.add(pendingTile)
        PendingOpenTiles.insert(0, pendingTile)
        self.updateRects()
        return True

class TileListVertical(TileListBase):
    def updateRects(self):
        rect = self.rect
        totalSize = rect[3] - rect[1]
        pos = rect[1]
        if len(self.childList) != 0 and totalSize != 0:
            childSize = int(totalSize / len(self.childList))
            for child in self.childList[:-1]:
                child.rect = (rect[0], pos, rect[2], pos+childSize + TileWindowOverlap)
                pos += childSize
            self.childList[-1].rect = (rect[0], pos, rect[2], rect[3])

    def hextend(self):
        return self.extend()
        
    def in_dir(self, dir, fromChild = None):
        if fromChild is None:
            fromChild = self.focusChild
        if fromChild is None or fromChild not in self.childList:
            return None
        if dir == "up":
            index = self.childList.index(fromChild)
            if index == 0:
                return None
            return self.childList[index-1]
        elif dir == "down":
            index = self.childList.index(fromChild)
            if index == len(self.childList)-1:
                return None
            return self.childList[index+1]
        else:
            return None
        
            
class TileListHorizontal(TileListBase):
    def updateRects(self):
        rect = self.rect
        totalSize = rect[2] - rect[0]
        pos = rect[0]
        if len(self.childList) != 0 and totalSize != 0:
            childSize = int(totalSize / len(self.childList))
            for child in self.childList[:-1]:
                child.rect = (pos, rect[1], pos+childSize + TileWindowOverlap, rect[3])
                pos += childSize
            self.childList[-1].rect = (pos, rect[1], rect[2], rect[3])
            
    def vextend(self):
        return self.extend()
                
    def in_dir(self, dir, fromChild = None):
        if fromChild is None:
            fromChild = self.focusChild
        if fromChild is None or fromChild not in self.childList:
            return None
        if dir == "left":
            index = self.childList.index(fromChild)
            if index == 0:
                return None
            return self.childList[index-1]
        elif dir == "right":
            index = self.childList.index(fromChild)
            if index == len(self.childList)-1:
                return None
            return self.childList[index+1]
        else:
            return None
        
class TileWindow(TileBase):
    def __init__(self, window):
        self.window = window
        self.noResize = False
        print(f"MAKE {self.title}")
        super(TileWindow, self).__init__()
        
    @property
    def title(self):
        return win32gui.GetWindowText(self.window)
        
    def checkFocus(self):
        return FocusWindow == self.window
        
    def getInnerFocused(self):
        return None
        
    def hide(self):
        print(f"HIDE {self.title}")
        if not win32gui.IsIconic(self.window):
            win32gui.ShowWindow(self.window, win32con.SW_FORCEMINIMIZE)
        self.hidden = True
        
    def update(self):
        if not win32gui.IsWindow(self.window):
            return False
        if not self.isHidden():
            if win32gui.GetWindowRect(self.window) != self.rect and not self.noResize:
                print(f"REPOSITION {self.title} FROM {win32gui.GetWindowRect(self.window)} TO {self.rect} ({self.parent.title})")
                try:
                    win32gui.SetWindowPos(self.window, win32con.HWND_TOP,
                        self.rect[0], self.rect[1],
                        self.rect[2] - self.rect[0], self.rect[3] - self.rect[1],
                        win32con.SWP_NOACTIVATE)
                except:
                    print(f"CANNOT RESIZE {self.title}")
                    self.noResize = True
        return True
        
    def focus(self):
        pylewm.focus.set(self.window)
        
    def show(self):
        print(f"SHOW {self.title}")
        self.hidden = False
        try:
            win32gui.SetWindowPos(self.window, win32con.HWND_TOP,
                self.rect[0], self.rect[1],
                self.rect[2] - self.rect[0], self.rect[3] - self.rect[1],
                0)
        except:
            pass # Probably not a window we can set position on
        win32gui.ShowWindow(self.window, win32con.SW_RESTORE)
        #if self.isMaximize:
            #win32gui.ShowWindow(window, win32con.SW_MAXIMIZE)
        
    def isHidden(self):
        return win32gui.IsIconic(self.window)
    
def onWindowCreated(window):
    # Find which tile to use for this window
    InTile = None
    if len(PendingOpenTiles) != 0:
        InTile = PendingOpenTiles[0]
        del PendingOpenTiles[0]
    if InTile is None:
        InTile = FocusTile
    if InTile is None:
        InTile = PrevFocusTile
    if InTile is None:
        InTile = PrimaryTile
    InTile.add(TileWindow(window))

def isFocused(window):
    return FocusWindow == window
    
def print_tree():
    print_sub(0, RootTile)
    
def print_sub(indent, tile):
    print(" "*indent + tile.title)
    for child in tile.childList:
        print_sub(indent+4, child)
    
@pyleinit
def initTiles():
    # Create an empty top level tile for each monitor
    global PrimaryTile
    global RootTile
    RootTile = TileRoot()
    for mhnd in win32api.EnumDisplayMonitors(None, None):
        monitor = win32api.GetMonitorInfo(mhnd[0])
        tile = TileSingular()
        tile.persistent = True
        tile.isMaximize = True
        tile.rect = tuple(monitor['Work'][0:4])
        RootTile.add(tile)
        if monitor['Flags'] & win32con.MONITORINFOF_PRIMARY:
            PrimaryTile = tile
    
@pyletick
def tickTiles():
    # Check for any newly created windows
    unknown_windows = []
    def enumUnknown(hwnd, param):
        if hwnd in KnownWindows:
            return
        if not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd)
        if len(title) == 0:
            return
        #TODO: HACK: Should detect the desktop window instead of using its title
        if title == "Program Manager":
            return
        if not isRelevantWindow(hwnd):
            return
        if isEmptyWindow(hwnd):
            return
        unknown_windows.append(hwnd)
    win32gui.EnumWindows(enumUnknown, None)

    # Manage adding newly created windows to tiles
    for win in unknown_windows:
        onWindowCreated(win)
        global KnownWindows
        KnownWindows.add(win)
        
    # Update existing tile focus
    global FocusWindow
    global FocusTile
    global PrevFocusTile
    FocusWindow = win32gui.GetForegroundWindow()
    RootTile.update()
    FocusTile = RootTile.getInnerFocused()
    if FocusTile is not None:
        PrevFocusTile = FocusTile