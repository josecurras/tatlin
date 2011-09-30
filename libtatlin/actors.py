from __future__ import division

import math

from OpenGL.GL import *
from OpenGL.GLE import *
from OpenGL.GLUT import *


def line_slope(a, b):
    slope = (b.y - a.y) / (b.x - a.x)
    return slope


class Platform(object):
    # makerbot platform size
    width = 120
    depth = 100
    grid  = 10

    def __init__(self):
        self.color_guides = (0xaf / 255, 0xdf / 255, 0x5f / 255, 0.4)
        self.color_fill   = (0xaf / 255, 0xdf / 255, 0x5f / 255, 0.1)

    def init(self):
        self.display_list = glGenLists(1)
        glNewList(self.display_list, GL_COMPILE)
        self.draw()
        glEndList()

    def draw(self):
        glPushMatrix()

        glTranslate(-self.width / 2, -self.depth / 2, 0)
        glColor(*self.color_guides)

        # draw the grid
        glBegin(GL_LINES)
        for i in range(0, self.width + self.grid, self.grid):
            glVertex3f(float(i), 0.0,        0.0)
            glVertex3f(float(i), self.depth, 0.0)

        for i in range(0, self.depth + self.grid, self.grid):
            glVertex3f(0,          float(i), 0.0)
            glVertex3f(self.width, float(i), 0.0)
        glEnd()

        # draw fill
        glColor(*self.color_fill)
        glRectf(0.0, 0.0, float(self.width), float(self.depth))

        glPopMatrix()

    def display(self):
        glCallList(self.display_list)


class GcodeModel(object):
    def __init__(self, layers):
        self.layers = layers
        self.max_layers = len(self.layers)
        self.num_layers_to_draw = self.max_layers
        self.arrows_enabled = True

        self.colors = {
            'red':    (1.0, 0.0, 0.0, 0.6),
            'yellow': (1.0, 0.875, 0.0, 0.6),
            'orange': (1.0, 0.373, 0.0, 0.6),
            'green':  (0.0, 1.0, 0.0, 0.6),
            'cyan':   (0.0, 0.875, 0.875, 0.6),
            'gray':   (0.5, 0.5, 0.5, 0.5),
        }

        line_count = 0
        for layer in self.layers:
            line_count += len(layer)
        print '!!! line count:     ', line_count
        print '!!! lines per layer:', round(line_count / self.max_layers)

    def init(self):
        """
        Create a display list for each model layer.
        """
        self.display_lists = self.draw_layers()

        self.arrow_lists = []
        if self.arrows_enabled:
            for layer in self.layers:
                self.draw_arrows(layer, self.arrow_lists)

    def draw_layers(self, list_container=None):
        if list_container is None:
            list_container = []


        for layer_no, layer in enumerate(self.layers):
            layer_list = glGenLists(1)
            glNewList(layer_list, GL_COMPILE)

            glPushMatrix()
            self.draw_layer(layer, (layer_no == self.num_layers_to_draw - 1))
            glPopMatrix()

            glEndList()
            list_container.append(layer_list)

        return list_container

    def draw_layer(self, layer, last=False):
        for movement in layer:
            glColor(*self.movement_color(movement))

            point_a = movement.point_a
            point_b = movement.point_b

            glBegin(GL_LINES)
            glVertex3f(point_a.x, point_a.y, point_a.z)
            glVertex3f(point_b.x, point_b.y, point_b.z)
            glEnd()

    def draw_arrows(self, layer, list_container=None):
        if list_container is None:
            list_container = []

        layer_arrow_list = glGenLists(1)
        glNewList(layer_arrow_list, GL_COMPILE)

        for movement in layer:
            color = self.movement_color(movement)
            glColor(*color)
            self.draw_arrow(movement)

        glEndList()
        list_container.append(layer_arrow_list)

        return list_container

    def draw_arrow(self, movement):
        a = movement.point_a
        b = movement.point_b

        try:
            slope = line_slope(a, b)
            angle = math.degrees(math.atan(slope))
            if b.x > a.x:
                angle = 180 + angle
        except ZeroDivisionError:
            angle = 90
            if b.y > a.y:
                angle = 180 + angle

        glPushMatrix()

        glTranslate(b.x, b.y, b.z)
        glRotate(angle, 0.0, 0.0, 1.0)
        glColor(*self.movement_color(movement))

        glBegin(GL_TRIANGLES)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.4, -0.2, 0.0)
        glVertex3f(0.4, 0.2, 0.0)
        glEnd()

        glPopMatrix()

    def movement_color(self, movement):
        if not movement.extruder_on:
            color = self.colors['gray']
        elif movement.is_loop:
            color = self.colors['yellow']
        elif movement.is_perimeter and movement.is_perimeter_outer:
            color = self.colors['cyan']
        elif movement.is_perimeter:
            color = self.colors['green']
        else:
            color = self.colors['red']

        return color

    def display(self):
        for layer in self.display_lists[:self.num_layers_to_draw]:
            glCallList(layer)

        if self.arrows_enabled:
            glCallList(self.arrow_lists[self.num_layers_to_draw - 1])
