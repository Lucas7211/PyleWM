class Rect:
    def __init__(self, position=None):
        if not position:
            self.position = [0,0,0,0]
        else:
            self.position = position

    def __str__(self):
        return repr(self.position)

    def copy(self):
        return Rect(self.position)

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
    def set_coordinates(self, newcoords):
        self.position = newcoords

    @property
    def topleft(self):
        return (self.position[0], self.position[1])

    @topleft.setter
    def set_topleft(self, coord):
        self.position[0] = coord[0]
        self.position[1] = coord[1]

    @property
    def bottomright(self):
        return (self.position[2], self.position[3])

    @bottomright.setter
    def set_bottomright(self, coord):
        self.position[2] = coord[0]
        self.position[3] = coord[1]

    @property
    def left(self):
        return self.position[0]

    @left.setter
    def set_left(self, pos):
        self.position[0] = pos

    @property
    def top(self):
        return self.position[1]

    @top.setter
    def set_top(self, pos):
        self.position[1] = pos

    @property
    def right(self):
        return self.position[2]

    @right.setter
    def set_right(self, pos):
        self.position[2] = pos

    @property
    def bottom(self):
        return self.position[3]

    @bottom.setter
    def set_bottom(self, pos):
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