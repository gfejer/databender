import numpy as np
from PIL import Image
from typing import Callable


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

def channel_swapping(data, mode):
    # channel swapping
    if mode.lower() == "bgr":
        data = data[:,:,[2, 1, 0]]

    elif mode.lower() == "brg":
        data = data[:,:,[2, 0, 1]]

    elif mode.lower() == "grb":
        data = data[:,:,[1, 0, 2]]
    
    elif mode.lower() == "gbr":
        data = data[:,:,[1, 2, 0]]
    
    elif mode.lower() == "rbg":
        data = data[:,:,[0, 2, 1]]
    else:
        pass
    return data

def warp(data, mode, val):
    # warping
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

def block_displacement(data, num_blocks, max_block_size, shift_amount, fixed_mode):
    # block displacement
    height, width = data.shape[:2]
    
    if shift_amount <= 0 or max_block_size <= 10:
        return data

    # to avoid the block being bigger than the image
    safe_max_size = min(max_block_size, width - 1, height - 1)
    
    if safe_max_size <= 10:
        return data

    if fixed_mode:
        np.random.seed(24)

    for i in range(num_blocks):
        bw = np.random.randint(10, safe_max_size)
        bh = np.random.randint(10, safe_max_size)

        src_x = np.random.randint(0, width - bw)
        src_y = np.random.randint(0, height - bh)

        shift_x = np.random.randint(-shift_amount, shift_amount + 1)
        shift_y = np.random.randint(-shift_amount, shift_amount + 1)

        dst_x = np.clip(src_x + shift_x, 0, width - bw)
        dst_y = np.clip(src_y + shift_y, 0, height - bh)

        block = data[src_y:src_y+bh, src_x:src_x+bw].copy()
        data[dst_y:dst_y+bh, dst_x:dst_x+bw] = block

    if fixed_mode:
        np.random.seed()

    return data