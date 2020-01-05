class Direction:
    Left = 0
    Up = 1
    Right = 2
    Down = 3
    Next = 4
    Previous = 5

class Rect:
    def __init__(self, position=None):
        if not position:
            self.position = [0,0,0,0]
        else:
            self.position = list(position)

    def __str__(self):
        return repr(self.position)

    def copy(self):
        return Rect(self.position)

    def assign(self, other):
        for i in range(0, 4):
            self.position[i] = other.position[i]

    @property
    def width(self):
        return self.position[2] - self.position[0]

    @property
    def height(self):
        return self.position[3] - self.position[1]

    @property
    def coordinates(self):
        return self.position

    @coordinates.setter
    def coordinates(self, newcoords):
        for i in range(0, 4):
            self.position[i] = newcoords[i]

    def equal_coordinates(self, coords):
        return (coords[0] == self.position[0]
                and coords[1] == self.position[1]
                and coords[2] == self.position[2]
                and coords[3] == self.position[3])

    @property
    def topleft(self):
        return (self.position[0], self.position[1])

    @topleft.setter
    def topleft(self, coord):
        self.position[0] = coord[0]
        self.position[1] = coord[1]

    @property
    def bottomright(self):
        return (self.position[2], self.position[3])

    @bottomright.setter
    def bottomright(self, coord):
        self.position[2] = coord[0]
        self.position[3] = coord[1]

    @property
    def center(self):
        return ((self.position[0] + self.position[2]) / 2,
                (self.position[1] + self.position[3]) / 2)

    @property
    def left(self):
        return self.position[0]

    @left.setter
    def left(self, pos):
        self.position[0] = pos

    @property
    def top(self):
        return self.position[1]

    @top.setter
    def top(self, pos):
        self.position[1] = pos

    @property
    def right(self):
        return self.position[2]

    @right.setter
    def right(self, pos):
        self.position[2] = pos

    @property
    def bottom(self):
        return self.position[3]

    @bottom.setter
    def bottom(self, pos):
        self.position[3] = pos

    def contains(self, pos):
        return (pos[0] >= self.position[0] and pos[0] <= self.position[2] and
                pos[1] >= self.position[1] and pos[1] <= self.position[3])

    def overlaps(self, rect):
        other_position = rect.position
        if other_position[0] > self.position[2] or other_position[1] > self.position[3]:
            return False
        if other_position[2] < self.position[0] or other_position[3] < self.position[1]:
            return False
        return True

    def extend_to_cover(self, rect):
        other_position = rect.position
        self.position[0] = min(self.position[0], other_position[0])
        self.position[1] = min(self.position[1], other_position[1])
        self.position[2] = max(self.position[2], other_position[2])
        self.position[3] = max(self.position[3], other_position[3])

    def get_overlap_area(self, rect):
        other_position = rect.position
        return ((min(self.position[2], other_position[2]) - max(self.position[0], other_position[0]))
             * (min(self.position[3], other_position[3]) - max(self.position[1], other_position[1])))

    def get_most_overlapping(self, rect_list, rect_function = None):
        most_area = 0
        sel = None

        for other_elem in rect_list:
            other_rect = None
            if rect_function:
                other_rect = rect_function(other_elem)
            else:
                other_rect = other_elem
            if not other_rect.overlaps(self):
                continue
            area = self.get_overlap_area(other_rect)
            if area > most_area:
                most_area = area
                sel = other_elem
                
        return sel

    def get_closest_in_direction(self, direction, rect_list, rect_function = None, wrap_area = None):
        """ Get the closest rect in the list in the direction from fromRect. """
        def getDim(rect):
            if direction == Direction.Left or direction == Direction.Previous: return rect.coordinates[0]
            if direction == Direction.Up: return rect.coordinates[1]
            if direction == Direction.Right or direction == Direction.Next: return rect.coordinates[0]
            return rect.coordinates[1]
        def getOppositeEnd(rect):
            if direction == Direction.Left or direction == Direction.Previous: return rect.coordinates[2]
            if direction == Direction.Up: return rect.coordinates[3]
            if direction == Direction.Right or direction == Direction.Next: return rect.coordinates[0]
            return rect.coordinates[1]
        def getOtherDim(rect):
            if direction == Direction.Left or direction == Direction.Previous: return rect.coordinates[1]
            if direction == Direction.Up: return rect.coordinates[0]
            if direction == Direction.Right or direction == Direction.Next: return rect.coordinates[1]
            return rect.coordinates[0]
        def isAfter(A, B):
            if direction == Direction.Left or direction == Direction.Previous or direction == Direction.Up:
                return B <= A
            else:
                return A <= B

        curStart = getDim(self)
        curOtherDim = getOtherDim(self)
        maxDiff = float(1e20)
        sel = None

        # Find which rect is the closest in the particular direction
        def checkRects():
            nonlocal maxDiff
            nonlocal sel
            for other in rect_list:
                otherRect = rect_function(other) if rect_function else other
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
            if wrap_area:
                curStart = getOppositeEnd(wrap_area)
                curOtherDim = curStart
                checkRects()
            return sel