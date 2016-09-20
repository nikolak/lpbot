# -*- coding: utf-8 -*-

# Copyright 2014, Edward D. Powell, embolalia.net
# Licensed under the Eiffel Forum License 2.

# Copyright 2016, Benjamin Eßer, <benjamin.esser1@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
from enum import Enum

# Color names are as specified at http://www.mirc.com/colors.html

CONTROL_NORMAL = '\x0f'
"""The control code to reset formatting"""
CONTROL_COLOR = '\x03'
"""The control code to start or end color formatting"""
CONTROL_UNDERLINE = '\x1f'
"""The control code to start or end underlining"""
CONTROL_BOLD = '\x02'
"""The control code to start or end bold formatting"""


class colors(Enum):
    WHITE = '00'
    BLACK = '01'
    BLUE = '02'
    NAVY = BLUE
    GREEN = '03'
    RED = '04'
    BROWN = '05'
    MAROON = BROWN
    PURPLE = '06'
    ORANGE = '07'
    OLIVE = ORANGE
    YELLOW = '08'
    LIGHT_GREEN = '09'
    LIME = LIGHT_GREEN
    TEAL = '10'
    LIGHT_CYAN = '11'
    CYAN = LIGHT_CYAN
    LIGHT_BLUE = '12'
    ROYAL = LIGHT_BLUE
    PINK = '13'
    LIGHT_PURPLE = PINK
    FUCHSIA = PINK
    GREY = '14'
    GRAY = GREY
    LIGHT_GREY = '15'
    SILVER = LIGHT_GREY


def _get_color(color):
    if color is None:
        return None

    # You can pass an int or string of the color code
    try:
        color = int(color)
    except ValueError:
        pass
    if isinstance(color, int):
        max_value = max([int(color.value) for color in colors])
        if color > max_value:
            raise ValueError('Maximum color value is {}.'.format(max_value))
        return color.rjust(2, '0')

    # You can also pass the name of the color
    color_name = color.upper()
    try:
        return colors.color.value
    except AttributeError:
        raise ValueError('Unknown color name: {}'.format(color))


def color(text, fg=None, bg=None):
    """Return the text, with the given colors applied in IRC formatting.

    The color can be a string of the color name, or the color code as string or integer. 
	The known color names can be found in the `colors` class of this module."""
    if not fg and not bg:
        return text

    fg = _get_color(fg)
    bg = _get_color(bg)

    if not bg:
        text = ''.join([CONTROL_COLOR, fg, text, CONTROL_COLOR])
    else:
        text = ''.join([CONTROL_COLOR, fg, ',', bg, text, CONTROL_COLOR])
    return text


def bold(text):
    """Return the text, with bold IRC formatting."""
    return ''.join([CONTROL_BOLD, text, CONTROL_BOLD])


def underline(text):
    """Return the text, with underline IRC formatting."""
    return ''.join([CONTROL_UNDERLINE, text, CONTROL_UNDERLINE])
