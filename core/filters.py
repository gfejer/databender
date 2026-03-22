import numpy as np
from PIL import Image
from typing import Callable


def color_offset(data, offset):
    # color offset
    if offset == 0:
        return data
    else:
        return data + offset

def row_shifting(data, probability, max_shift):
    # row shifting
    height = data.shape[0]
    for i in range(height):
        if np.random.rand() < probability:
            shift = np.random.randint(-max_shift, max_shift)
            data[i] = np.roll(data[i], shift, axis=0)
    return data

def chromatic_aberration(data, red, green, blue):
    # chromatic aberration
    if red != 0:
        data[:,:,0] = np.roll(data[:,:,0], red, axis=1)
    if green != 0:
        data[:,:,1] = np.roll(data[:,:,1], green, axis=1)
    if blue != 0:
        data[:,:,2] = np.roll(data[:,:,2], blue, axis=1)
    else:
        pass

    return data

def sort_pixels(data, value: Callable, condition: Callable, rotation: int = 0):
    # https://www.reddit.com/r/pixelsorting/comments/dewpt6/pixel_sorting_in_20_lines_of_python_using_numpy/
    pixels = np.rot90(np.array(data), rotation)
    values = value(pixels)
    edges = np.apply_along_axis(lambda row: np.convolve(row, [-1, 1], 'same'), 0, condition(values))
    intervals = [np.flatnonzero(row) for row in edges]

    for row, key in enumerate(values):
        order = np.split(key, intervals[row])
        for index, interval in enumerate(order[1:]):
            order[index + 1] = np.argsort(interval) + intervals[row][index]
        order[0] = range(order[0].size)
        order = np.concatenate(order)

        for channel in range(3):
            pixels[row, :, channel] = pixels[row, order.astype('uint32'), channel]

    return np.rot90(pixels, -rotation)

def hue(pixels):
    r, g, b = np.split(pixels, 3, 2)
    return np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)[:, :, 0]

def warp(data, mode, val):
    height = data.shape[0]
    val = float(val)

    for i in range(height):
        if mode == "normal":
            data[i] = np.roll(data[i], int(i/(21 - val)), axis=0)
        elif mode == "sin":
            data[i] = np.roll(data[i], int(val * np.sin(i / 10.0)), axis=0)
        else: 
            continue
    return data
