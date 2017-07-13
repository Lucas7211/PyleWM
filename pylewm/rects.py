DesktopArea = [0,0,0,0]

def isInDesktopArea(pos):
    if len(pos) == 4:
        return isInDesktopArea(pos[0:2]) and isInDesktopArea(pos[2:4])
    return pos[0] >= DesktopArea[0] and pos[0] <= DesktopArea[2] and \
           pos[1] >= DesktopArea[1] and pos[1] <= DesktopArea[3]

def overlapsDesktopArea(rect):
    if rect[0] > DesktopArea[2] or rect[1] > DesktopArea[3]:
        return False
    if rect[2] < DesktopArea[0] or rect[3] < DesktopArea[1]:
        return False
    return True

def getClosestInDirection(dir, fromRect, toList, rectFun = lambda x: x, wrap = True, ignore = None):
    """ Get the closest rect in the list in the direction from fromRect. """
    def getDim(rect):
        if dir == "left": return rect[0]
        if dir == "up": return rect[1]
        if dir == "right": return rect[0]
        return rect[1]
    def getOppositeEnd(rect):
        if dir == "left": return rect[2]
        if dir == "up": return rect[3]
        if dir == "right": return rect[0]
        return rect[1]
    def getOtherDim(rect):
        if dir == "left": return rect[1]
        if dir == "up": return rect[0]
        if dir == "right": return rect[1]
        return rect[0]
    def isAfter(A, B):
        if dir == "left" or dir == "up":
            return B <= A
        else:
            return A <= B
    curStart = getDim(fromRect)
    curOtherDim = getOtherDim(fromRect)
    maxDiff = float(1e20)
    sel = None

    # Find which rect is the closest in the particular direction
    def checkRects():
        nonlocal maxDiff
        nonlocal sel
        for other in toList:
            if other == ignore:
                continue
            otherRect = rectFun(other)
            otherStart = getDim(otherRect)
            otherOtherDim = getOtherDim(otherRect)

            # Skip windows not at all extended in the right direction
            if not isAfter(curStart, otherStart):
                continue

            diff = float(abs(curStart - otherStart)) + float(abs(curOtherDim - otherOtherDim) / 10000.0)
            if diff < maxDiff:
                # Closer to the window's starting edge
                maxDiff = diff
                sel = other

    # Return the element with the closest rect
    checkRects()
    if sel is not None:
        return sel
    else:
        # Wrap around to the other side
        if wrap:
            curStart = getOppositeEnd(DesktopArea)
            curOtherDim = curStart
            checkRects()
        return sel

def getMostOverlapping(fromRect, toList, rectFun = lambda x: x, ignore = None):
    """ Get the rect in the list that fromRect overlaps the most. """
    mostOverlap = 0
    sel = None
    for other in toList:
        if other == ignore:
            continue
        otherRect = rectFun(other)
        if fromRect[0] > otherRect[2] or fromRect[1] > otherRect[3]:
            continue
        if fromRect[2] < otherRect[0] or fromRect[3] < otherRect[1]:
            continue

        overlap = (min(fromRect[2], otherRect[2]) - max(fromRect[0], otherRect[0])) * (min(fromRect[3], otherRect[3]) - max(fromRect[1], otherRect[1]))
        if overlap > mostOverlap:
            mostOverlap = overlap
            sel = other
    return sel

def getClosestTo(fromRect, toList, rectFun = lambda x: x, ignore = None):
    """ Get the rect in the list that is the closest. """
    # TODO: Use something better than manhattan distance between top left corners
    leastDistance = 1e8
    sel = None
    for other in toList:
        if other == ignore:
            continue
        otherRect = rectFun(other)
        dist = abs(otherRect[0] - fromRect[0]) + abs(otherRect[1] - fromRect[1])
        if dist < leastDistance:
            sel = other
            leastDistance = dist
    return sel

def overlaps(fromRect, toRect):
    if fromRect[0] > toRect[2] or fromRect[1] > toRect[3]:
        return False
    if fromRect[2] < toRect[0] or fromRect[3] < toRect[1]:
        return False
    return True

def moveRelativeInto(rect, outerRect, targetRect):
    """ Move the rectangle inside outerRect to the same relative position inside targetRect."""
    moved = [0,0,0,0]
    for i in range(0,4):
        outerOffset = outerRect[(i%2)]
        outerSize = outerRect[2+(i%2)] - outerOffset
        relPos = float(rect[i] - outerOffset) / float(outerSize)
        targetOffset = targetRect[(i%2)]
        targetSize = targetRect[2+(i%2)] - targetOffset
        moved[i] = int(relPos * float(targetSize)) + targetOffset
    return moved
