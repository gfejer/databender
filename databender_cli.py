from PIL import Image
import numpy as np
import argparse
import os
from typing import Callable

def parse_arguments():
    # flag arguments
    parser = argparse.ArgumentParser(description="Databending script for manipulating images.")
    parser.add_argument("images", nargs='+', type=str, help="The path(s) of your image(s).", metavar="IMAGES")

    roi_group = parser.add_argument_group("Region of Interest")
    roi_group.add_argument("--roi", nargs=5, help=("Define a specific rectangular area by providing X, Y, width and height values to glitch only a targeted part of the image."), metavar=("MODE", "X", "Y", "WIDTH", "HEIGHT"))

    color_group = parser.add_argument_group('Color Manipulation')
    color_group.add_argument("-c", "--color-offset", type=int, required=False, default=0, help="Adds an integer value to all color channels (R, G, B) using wrap-around (modulo 256) arithmetic. (0-255)")

    shift_group = parser.add_argument_group('Row Shifting')
    shift_group.add_argument("--do-shift", action="store_true", help="Enable row shifting with default values.")
    shift_group.add_argument("-p", "--probability", type=float, required=False, default=None, help="Probability of a row being shifted (0.0 - 1.0). (Default: 0.2)")
    shift_group.add_argument("-x", "--shift", type=int, default=None, help="Maximum horizontal shift in pixels (Default: 50)")

    aberration_group = parser.add_argument_group("Chromatic Aberration")
    aberration_group.add_argument("-r", "--red", type=int, default=0, help=("Horizontal shift of the red channel.  (Default: 0)"))
    aberration_group.add_argument("-g", "--green", type=int, default=0, help=("Horizontal shift of the green channel. (Default: 0)"))
    aberration_group.add_argument("-b", "--blue", type=int, default=0, help=("Horizontal shift of the blue channel. (Default: 0)"))

    sorting_group = parser.add_argument_group("Pixel Sorting")
    sorting_group.add_argument("--sort", default=None, help="Sort pixels based on luminosity or hue (lum/hue).", metavar=("MODE"))

    warp_group = parser.add_argument_group("Warping")
    warp_group.add_argument("--warp", nargs=2, help="Warping mode (normal/sin) and intensity (for normal mode 1-20).", metavar=("MODE", "VAL"))

    parser.add_argument("-o", "--out-dir", type=str, required=False, help="Output directory to save files. If omitted, images will just be displayed.", metavar="DIR")

    args = parser.parse_args()

    # check if row shifting is enabled and managing default value
    if not args.do_shift and (args.probability is not None or args.shift is not None):
        parser.error("The -p/--probability and -x/--shift arguments require --do-shift")

    if args.probability is None:
        args.probability = 0.2

    if args.shift is None:
        args.shift = 50

    return args

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
            data[i] = np.roll(data[i], i/(21 - val), axis=0)
        elif mode == "sin":
            data[i] = np.roll(data[i], int(val * np.sin(i / 10.0)), axis=0)
        else: 
            continue
    return data

def main():
    args = parse_arguments()

    if args.out_dir:
        os.makedirs(args.out_dir)

    for image_path in args.images:
        print(f"Processing: {image_path}")

        try:
            # image to numpy array
            imgin = Image.open(image_path)
            imgin.load()
            data = np.asarray(imgin, dtype="int32")

            # --- CUTTING THE ROI ---
            img_h, img_w = data.shape[:2]

            roi_mode = "none"
            target_data = data.copy()
            original_roi = None
            rx, ry, rw, rh = 0, 0, img_w, img_h

            if args.roi:
                roi_mode = args.roi[0]
                try:
                    rx = int(args.roi[1])
                    ry = int(args.roi[2])

                    rw = int(args.roi[3]) if len(args.roi) > 3 and args.roi[3] else img_w
                    rh = int(args.roi[4]) if len(args.roi) > 4 and args.roi[4] else img_h

                    rw = max(1, min(rw, img_w - rx))
                    rh = max(1, min(rh, img_h - ry))

                    if roi_mode == "outside":
                        original_roi = data[ry:ry+rh, rx:rx+rw].copy()

                    elif roi_mode == "inside":
                        target_data = data[ry:ry+rh, rx:rx+rw].copy()

                except ValueError:
                    print("Error", "ROI coordinates must be whole numbers!")
                    continue

            target_data = color_offset(target_data, args.color_offset)

            if args.do_shift:
                target_data = row_shifting(target_data, args.probability, args.shift)
            
            target_data = chromatic_aberration(target_data, args.red, args.green, args.blue)    

            if args.sort == "lum":
                target_data = sort_pixels(target_data,
                        lambda pixels: np.average(pixels, axis=2) / 255,
                        lambda lum: (lum > 2 / 6) & (lum < 4 / 6), 1)
                
            elif args.sort == "hue":
                target_data = sort_pixels(target_data, hue, lambda h: (h > 2 / 6) & (h < 4 / 6), 1)

            if args.warp:
                target_data = warp(target_data,args.warp[0], args.warp[1])

            if roi_mode == "inside":
                data[ry:ry+rh, rx:rx+rw] = target_data
            elif roi_mode == "outside":
                target_data[ry:ry+rh, rx:rx+rw] = original_roi
                data = target_data
            else:
                data = target_data

            # numpy array to image
            final_data = (data % 256).astype(np.uint8)
            imgout = Image.fromarray(final_data, "RGB")

            if args.out_dir:
                base_filename = os.path.basename(image_path)
                save_path = os.path.join(args.out_dir, base_filename)
                imgout.save(save_path)
            else:
                imgout.show()
        
        except Exception as e:
            print(f"There was an error processing {image_path}, {e}")

if __name__ == "__main__":
    main()