from pylewm import pyleinit, pyletick, pylecommand, config
from pylewm.windows import isEmptyWindow, isRelevantWindow
import pylewm.windows
import pylewm.focus
import pylewm.rects
import pylewm.style
import pylewm.floating
import pylewm.selector
import win32gui, win32con, win32api
from ctypes import CFUNCTYPE, POINTER, c_uint, windll
import atexit
import traceback

TileWindowOverlap = 4
DelayTicks = 25

@pylecommand
def focus_dir(dir):
    """ Focus the neighbouring child to the selected one in a particular direction. """
    # Send focus command to floating layer if the current window is floating
    if pylewm.floating.isFloatingFocused():
        return pylewm.floating.focus_dir(dir)()

    # Check which tile to give focus to based on the currently focused one
    tile = FocusTile
    while tile is not None:
        inDir = tile.in_dir(dir)
        if inDir is not None:
            inDir.focus()
            teleportMouse(inDir)
            return
        tile = tile.parent

    # Fall back on a window-based focus_dir if no tile supports the operation
    pylewm.windows.focus_dir(dir)()

@pylecommand
def focus_floating():
    """ Toggle whether a floating window is focused on not. """
    curWindow = win32gui.GetForegroundWindow()
    if not win32gui.IsWindow(curWindow):
        RootTile.childList[0].focus()
        return
    curRect = win32gui.GetWindowRect(curWindow)

    if pylewm.floating.isFloatingFocused():
        # Focus the closest tile to the current floating window
        tile = getClosestTile(curRect)
        if tile is not None:
            tile.focus()
    else:
        # Focus the closest floating window to the current tile
        floatingWindow = pylewm.floating.getClosestFloatingWindow(curRect)
        if floatingWindow is not None:
            floatingWindow.focus()

@pylecommand
def move_dir(dir):
    """ Move the focused single window in a particular direction. """
    # Find the destination tile in that direction
    sourceTile = FocusTile
    destTile = sourceTile
    while destTile is not None:
        inDir = destTile.in_dir(dir)
        if inDir is not None:
            destTile = inDir
            break
        destTile = destTile.parent

    if destTile is None:
        return

    # Resolve the source to a single window
    sourceTile = getWindowTile(FocusWindow)

    if sourceTile is None:
        return

    print(f"MOVE {sourceTile.title} ONTO {destTile.title}")
    print_tree()

    # Check if we should replace the window with one from the destination
    replaceWindow = None
    if destTile.parent is not None:
        replaceWindow = destTile.parent.getReplaceWindow(sourceTile, destTile)

    if replaceWindow is not None:
        # Swap this window for the window we want to replace
        replaceParent = replaceWindow.parent
        sourceParent = sourceTile.parent

        replaceParent.remove(replaceWindow)
        sourceParent.remove(sourceTile)

        replaceParent.add(sourceTile)
        sourceParent.add(replaceWindow)
    else:
        # Add it as a new singular tile to the existing destination
        newTile = TileSingular()
        newTile.hidden = True
        newTile.rect = sourceTile.rect
        sourceParent = sourceTile.parent
        sourceParent.remove(sourceTile)
        sourceParent.update()
        newTile.add(sourceTile)
        newTile.visibleChild = sourceTile
        destTile.addOnTile(newTile)
        newTile.focus()

    teleportMouse(sourceTile)

    print("AFTER")
    print_tree()

@pylecommand
def move_tile_dir(dir):
    """ Move the focused entire tile in a particular direction. """
    # Find the destination tile in that direction
    sourceTile = FocusTile
    destTile = sourceTile
    while destTile is not None:
        inDir = destTile.in_dir(dir)
        if inDir is not None:
            destTile = inDir
            break
        destTile = destTile.parent

    if destTile is None:
        return

    print(f"MOVE {FocusTile.title} ONTO {destTile.title}")
    print_tree()

    if sourceTile.persistent:
        # Persistent tiles should just lose all their children instead
        focusWindowTile = getWindowTile(FocusWindow)
        newTile = TileSingular()
        newTile.rect = sourceTile.rect
        for child in sourceTile.childList[:]:
            sourceTile.remove(child)
            newTile.add(child)
        newTile.visibleChild = focusWindowTile
        destTile.addOnTile(newTile)
        teleportMouse(focusWindowTile)
    elif sourceTile.parent is destTile.parent:
        # Just swap the positions of the children
        sourceTile.parent.swapChildren(sourceTile, destTile)
        teleportMouse(sourceTile)
    else:
        # Remove window from its parent
        sourceTile.parent.remove(sourceTile)

        # Add window to new parent
        destTile.addOnTile(sourceTile)
        teleportMouse(sourceTile)
    print("AFTER")
    print_tree()

@pylecommand
def switch_next():
    """ Switch to the next window contained in the active tile. """
    tile_bubble(FocusTile, "next")

@pylecommand
def switch_prev():
    """ Switch to the previous window contained in the active tile. """
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

@pylecommand
def toggle_floating():
    """ Toggle the currently selected window between being tiled or floating. """
    curWindow = win32gui.GetForegroundWindow()
    if not win32gui.IsWindow(curWindow):
        return

    if pylewm.floating.isFloatingFocused():
        # Drop the window into a tile
        pylewm.floating.stopFloatingWindow(curWindow)
        startTilingWindow(curWindow)
    else:
        # Raise the window to floating
        stopTilingWindow(curWindow)
        pylewm.floating.startFloatingWindow(curWindow)

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
        self.isMaximize = False

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

    def getInnerActive(self):
        return self

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

    def swapChildren(self, fromTile, toTile):
        fromIndex = self.childList.index(fromTile)
        toIndex = self.childList.index(toTile)
        self.childList[fromIndex], self.childList[toIndex] = self.childList[toIndex], self.childList[fromIndex]

    def getReplaceWindow(self, forWindow, onTile):
        return None

    def addOnTile(self, tile, onToTile=None):
        onIndex = 0
        if onToTile is not None:
            onIndex = self.childList.index(onToTile)
        self.add(tile)
        if onToTile is not None:
            self.childList.remove(tile)
            self.childList.insert(onIndex, tile)

    def next(self):
        return False

    def prev(self):
        return False

    @property
    def title(self):
        return f"{self.__class__.__name__} {self.rect}"

class TileRoot(TileBase):
    def __init__(self):
        self.focusChild = None
        TileBase.__init__(self)

    def getInnerFocused(self):
        for child in self.childList:
            if child.focused:
                return child.getInnerFocused()
        return None

    def in_dir(self, dir, fromChild = None):
        if fromChild is None:
            fromChild = self.focusChild
        if fromChild is None or fromChild not in self.childList:
            return None
        sel = pylewm.rects.getClosestInDirection(
            dir, fromChild.rect, self.childList, lambda tile: tile.rect,
            wrap = True, ignore = fromChild
        )
        print(f"SELECT {dir} = {fromChild.title} -> {sel.title}")
        return sel

    def update(self):
        TileBase.update(self)
        # Update focused status
        self.focused = False
        self.focusChild = None
        for i, child in enumerate(self.childList):
            if child.focused:
                self.focused = True
                self.focusChild = child
                break
        return True

class TileSingular(TileBase):
    def __init__(self):
        self.focusChild = None
        self.visibleChild = None
        self.wasLostChild = False
        self.focusDelay = 0
        super(TileSingular, self).__init__()

    def update(self):
        if self.focusDelay > 0:
            self.focusDelay -= 1
        # Update child status
        i = 0
        cnt = len(self.childList)
        keepFocus = False
        lostChild = False
        while i < cnt:
            self.childList[i].rect = self.rect
            if not self.childList[i].update():
                child = self.childList[i]
                if self.focusChild is self.childList[i]:
                    keepFocus = True
                if not hasattr(child, "wasLostChild") or child.wasLostChild:
                    lostChild = True
                self.remove(self.childList[i])
                i -= 1
                cnt -= 1
            i += 1
        if cnt > 0:
            self.pending = False
        if not self.persistent and not self.pending and len(self.childList) == 0:
            self.wasLostChild = lostChild
            return False
        # Update focused status
        self.focused = False
        self.focusChild = None
        self.visibleChild = None
        for i, child in enumerate(self.childList):
            if child.checkFocus():
                self.focused = True
                self.focusChild = child
                self.visibleChild = child
                break
            if not child.isHidden():
                self.visibleChild = child
        if self.visibleChild is None and len(self.childList) != 0:
            self.visibleChild = self.childList[0]
        if keepFocus and self.visibleChild is not None:
            self.focusChild = self.visibleChild
            self.visibleChild.focus()
        if self.visibleChild is not None:
            while self.visibleChild is not self.childList[0]:
                child = self.childList[0]
                del self.childList[0]
                self.childList.append(child)
        # Update which child is visible
        if self.focusDelay <= 0:
            for child in self.childList:
                if child is self.visibleChild and not self.hidden:
                    if child.isHidden():
                        child.show()
                else:
                    if not child.isHidden():
                        child.hide()
        return True

    def switchTo(self, tile):
        if self.visibleChild is not None:
            self.visibleChild.hide()
        self.visibleChild = tile
        tile.show()
        if self.focused:
            tile.focus()
            self.focusDelay = DelayTicks

    def focus(self):
        if self.visibleChild is not None:
            self.visibleChild.focus()

    def add(self, tile):
        print(f"ADD {tile.title} / {len(self.childList)} FROM {self.title} = {self.rect}")
        self.childList.append(tile)
        tile.rect = self.rect
        tile.parent = self

    def remove(self, tile):
        TileBase.remove(self, tile)

    def addOnTile(self, tile, onToTile=None):
        if isinstance(tile, TileSingular):
            # Merge all its windows into this
            toFocus = None
            if tile.visibleChild:
                toFocus = tile.visibleChild
            for child in tile.childList[:]:
                tile.remove(child)
                self.add(child)
            if toFocus is not None:
                self.switchTo(toFocus)
        else:
            raise "Not Allowed"

    def hide(self):
        for child in self.childList:
            child.hide()
        self.hidden = True

    def show(self):
        if self.visibleChild is not None:
            self.visibleChild.show()
        self.hidden = False

    def isHidden(self):
        return self.hidden

    def next(self):
        if len(self.childList) <= 1:
            return True
        for i, child in enumerate(self.childList):
            if child is self.visibleChild:
                self.switchTo(self.childList[(i+1) % len(self.childList)])
                return True
        return True

    def prev(self):
        if len(self.childList) <= 1:
            return True
        for i, child in enumerate(self.childList):
            if child is self.visibleChild:
                self.switchTo(self.childList[(i-1) % len(self.childList)])
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
        splitTile.persistent = self.persistent
        self.persistent = False
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
        self.wasLostChild = False
        super(TileListBase, self).__init__()

    def update(self):
        # Update child status
        i = 0
        cnt = len(self.childList)
        self.updateRects()
        keepFocus = None
        lostChild = False
        while i < cnt:
            if not self.childList[i].update():
                child = self.childList[i]
                if not hasattr(child, "wasLostChild") or child.wasLostChild:
                    if self.focusChild is child or self.lastFocusChild is child and cnt >= 2:
                        keepFocus = self.childList[(i-1)%cnt]
                    print(f"{self.title} LOST CHILD {child.title}")
                    lostChild = True
                self.remove(self.childList[i])
                i -= 1
                cnt -= 1
            i += 1
        if cnt > 0:
            self.pending = False
        if keepFocus is not None:
            print(f"KEEP FOCUS {self.title} : {keepFocus.title}")
            keepFocus.focus()
        if not self.persistent and not self.pending and len(self.childList) == 0:
            self.wasLostChild = lostChild
            return False
        # A list with only one child removes itself and puts the child back on its parent
        if len(self.childList) == 1:
            print(f"COLLAPSE {self.title}")
            child = self.childList[0]
            self.remove(child)
            self.parent.replaceChild(self, child)
            child.persistent = self.persistent
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
        if setTo is None and self.childList:
            setTo = self.childList[0]
        if setTo is not None:
            setTo.focus()

    def getInnerActive(self):
        inner = self.focusChild
        if inner is None:
            inner = self.lastFocusChild
        if inner is None and self.childList:
            inner = self.childList[0]
        if inner is None:
            return self
        else:
            return inner.getInnerActive()

    def add(self, tile):
        print(f"ADD {tile.title} / {len(self.childList)} FROM {self.title} = {self.rect}")
        self.childList.append(tile)
        self.updateRects()
        tile.show()
        tile.parent = self

    def addTile(self, tile, onToTile=None):
        if onToTile is None:
            onToTile = self.lastFocusChild
        TileBase.addTile(self, tile, onToTile=onToTile)

    def addWindowTile(self, windowTile, onToTile=None):
        tile = TileSingular()
        tile.add(windowTile)
        self.addTile(tile, onToTile)

    def replaceChild(self, fromTile, toTile):
        if self.lastFocusChild is fromTile:
            self.lastFocusChild = toTile
        TileBase.replaceChild(self, fromTile, toTile)

    def getReplaceWindow(self, forWindow, onTile):
        # Do a replace if we're the window's second parent
        if forWindow.parent is not None and self is forWindow.parent.parent:
            if isinstance(onTile, TileSingular):
                if onTile.visibleChild is not None:
                    return onTile.visibleChild
        return None

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
        self.resizeDelay = 0
        self.prevRect = (0,0,0,0)
        print(f"MAKE {self.title}")
        super(TileWindow, self).__init__()

    @property
    def title(self):
        return win32gui.GetWindowText(self.window)

    def checkFocus(self):
        return FocusWindow == self.window

    def getInnerFocused(self):
        return None

    def updatePosition(self, force=False):
        if not self.hidden:
            placement = win32gui.GetWindowPlacement(self.window)
            if placement[1] != win32con.SW_MAXIMIZE and self.parent.isMaximize:
                win32gui.ShowWindow(self.window, win32con.SW_MAXIMIZE)
            elif (placement[1] == win32con.SW_MAXIMIZE and not self.parent.isMaximize) or placement[1] == win32con.SW_MINIMIZE:
                win32gui.ShowWindow(self.window, win32con.SW_SHOWNOACTIVATE)
            if win32gui.IsIconic(self.window):
                win32gui.ShowWindow(self.window, win32con.SW_RESTORE)
            if (win32gui.GetWindowRect(self.window) != self.rect or force) and not self.noResize and (self.resizeDelay <= 0 or self.prevRect != self.rect or force):
                print(f"REPOSITION {self.title} % {self.hidden}: {win32gui.GetWindowRect(self.window)} => {self.rect}")
                try:
                    win32gui.SetWindowPos(self.window, win32con.HWND_BOTTOM if self.hidden else win32con.HWND_TOP,
                        self.rect[0], self.rect[1],
                        self.rect[2] - self.rect[0], self.rect[3] - self.rect[1],
                        win32con.SWP_NOACTIVATE)
                    if self.prevRect != self.rect:
                        self.prevRect = self.rect
                    else:
                        self.resizeDelay = DelayTicks
                except:
                    self.noResize = True


    def update(self):
        if not win32gui.IsWindow(self.window):
            return False
        if self.resizeDelay > 0:
            self.resizeDelay -= 1
        if not self.isHidden():
            self.updatePosition()
        return True

    def focus(self):
        print(f"FOCUS {self.title}")
        pylewm.focus.set(self.window)

    def show(self):
        print(f"SHOW {self.title}")
        self.hidden = False
        self.updatePosition(force=True)
        pylewm.floating.showWithParent(self.window)

    def hide(self):
        print(f"HIDE {self.title}")
        self.hidden = True
        pylewm.floating.hideWithParent(self.window)
        #self.updatePosition(force=True)

    def isHidden(self):
        return self.hidden

def getWindowTile(window):
    check = [RootTile]
    ind = 0
    while ind < len(check):
        tile = check[ind]
        if isinstance(tile, TileWindow):
            if tile.window == window:
                return tile
        check.extend(tile.childList)
        ind += 1
    return None

def getCurrentMonitorTile(rect):
    best = None
    if len(rect) == 4:
        best = pylewm.rects.getMostOverlapping(rect, RootTile.childList, lambda tile: tile.rect)
    elif len(rect) == 2:
        for tile in RootTile.childList:
            if tile.rect[0] <= rect[0] and tile.rect[2] >= rect[0] \
                and tile.rect[1] <= rect[1] and tile.rect[3] >= rect[1]:
                best = tile
    if best is None:
        best = PrimaryTile
    return best

def getClosestTile(toRect, windowTilesOnly=True, ignore=None):
    check = [RootTile]
    valid = []
    ind = 0
    while ind < len(check):
        tile = check[ind]
        if not tile.hidden:
            if not windowTilesOnly or isinstance(tile, TileWindow):
                valid.append(tile)
            check.extend(tile.childList)
        ind += 1
    return pylewm.rects.getClosestTo(toRect, valid,
        lambda tile: tile.rect, ignore=ignore)


def startTilingWindow(window):
    # Find which tile to use for this window
    InTile = None
    if len(PendingOpenTiles) != 0:
        InTile = PendingOpenTiles[0]
        del PendingOpenTiles[0]
    # If the mouse is on a monitor that doesn't have any windows yet,
    # open the window there
    monitor = getCurrentMonitorTile(win32gui.GetCursorPos())
    if monitor is not None:
        if len(monitor.childList) == 0:
            InTile = monitor
    if InTile is None:
        InTile = FocusTile
    if InTile is None:
        InTile = PrevFocusTile
    if InTile is None:
        InTile = getCurrentMonitorTile(win32gui.GetWindowRect(window))
    pylewm.style.applyTiled(window)
    newTile = TileWindow(window)
    newTile.originalRect = win32gui.GetWindowRect(window)
    InTile.add(newTile)

def stopTilingWindow(window, keepTilingFocus=False):
    windowTile = getWindowTile(window)
    if windowTile is None:
        return
    windowTile.parent.remove(windowTile)
    win32gui.SetWindowPos(window, win32con.HWND_TOP,
                    windowTile.originalRect[0], windowTile.originalRect[1],
                    windowTile.originalRect[2] - windowTile.originalRect[0],
                    windowTile.originalRect[3] - windowTile.originalRect[1],
                    win32con.SWP_NOACTIVATE)
    if keepTilingFocus and windowTile.focused:
        windowTile.parent.focus()

def onWindowCreated(window):
    if isPopup(window) or pylewm.selector.matches(window, pylewm.config.get("FloatingWindows", [])):
        # Add window to our floating layout
        pylewm.floating.onWindowCreated(window)
    else:
        startTilingWindow(window)

def isFocused(window):
    return FocusWindow == window

def isPopup(hwnd):
    style = win32api.GetWindowLong(hwnd, win32con.GWL_STYLE)
    return bool(style & win32con.WS_POPUP)

def print_tree():
    print_sub(0, RootTile)

def print_sub(indent, tile):
    print(" "*indent + tile.title)
    for child in tile.childList:
        print_sub(indent+4, child)


def teleportMouse(tile):
    tile = tile.getInnerActive()
    if pylewm.config.get("TeleportMouse", False):
        try:
            win32api.SetCursorPos((tile.rect[0] + 10, tile.rect[1] + 10))
        except:
            pass # Not allowed, probably an administrator window has focus or something

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
        unknown_windows.append(hwnd)
    win32gui.EnumWindows(enumUnknown, None)

    # Manage adding newly created windows to tiles
    for win in unknown_windows:
        global KnownWindows
        KnownWindows.add(win)

        # Only trigger something for this window if it's not ignored
        title = win32gui.GetWindowText(win)
        if len(title) == 0:
            continue
        if not isRelevantWindow(win):
            continue
        if isEmptyWindow(win):
            continue
        onWindowCreated(win)

    # Update existing tile focus
    global FocusWindow
    global FocusTile
    global PrevFocusTile
    FocusWindow = win32gui.GetForegroundWindow()
    RootTile.update()
    FocusTile = RootTile.getInnerFocused()
    if FocusTile is not None:
        PrevFocusTile = FocusTile
