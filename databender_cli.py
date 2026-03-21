from PIL import Image
import numpy as np
import argparse
import os
from typing import Callable
import cv2

def parse_arguments():
    # flag arguments
    parser = argparse.ArgumentParser(description="a databending script for manipulating images/videos.")
    parser.add_argument("media", nargs='+', type=str, help="The path of your image/video.", metavar="MEDIA")

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

    parser.add_argument("-o", "--out-dir", type=str, required=False, help="Output directory to save files. If omitted, images/video will just be displayed.", metavar="DIR")

    args = parser.parse_args()

    # checking if row shifting is enabled and managing default value
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
            data[i] = np.roll(data[i], int(i/(21 - val)), axis=0)
        elif mode == "sin":
            data[i] = np.roll(data[i], int(val * np.sin(i / 10.0)), axis=0)
        else: 
            continue
    return data

def apply_effects(data, args):
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
            return data

    # applying color offset
    target_data = color_offset(target_data, args.color_offset)

    # applying row shifting
    if args.do_shift:
        target_data = row_shifting(target_data, args.probability, args.shift)
            
    # applying chromatic aberration
    target_data = chromatic_aberration(target_data, args.red, args.green, args.blue)    

    # applying pixel sort
    if args.sort == "lum":
        target_data = sort_pixels(target_data,
                lambda pixels: np.average(pixels, axis=2) / 255,
                lambda lum: (lum > 2 / 6) & (lum < 4 / 6), 1)
                
    elif args.sort == "hue":
        target_data = sort_pixels(target_data, hue, lambda h: (h > 2 / 6) & (h < 4 / 6), 1)

    # applying warp
    if args.warp:
        target_data = warp(target_data,args.warp[0], args.warp[1])

    # placing ROI back
    if roi_mode == "inside":
        data[ry:ry+rh, rx:rx+rw] = target_data

    elif roi_mode == "outside":
        target_data[ry:ry+rh, rx:rx+rw] = original_roi
        data = target_data

    else:
        data = target_data

    return data

def process_video(input_path, output_path, args):
    cap = cv2.VideoCapture(input_path)

    # video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        print(f"Processing frame: {frame_count}/{total_frames}", end="\r")
        data = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).astype("int32")
        data = apply_effects(data, args)
        final_data = (data % 256).astype(np.uint8)
        final_frame = cv2.cvtColor(final_data, cv2.COLOR_RGB2BGR)
        out.write(final_frame)

    cap.release()
    out.release()
    print(f"\nVideo saved: {output_path}")

# to avoid overwriting files
def get_unique_filename(path):
    if not os.path.exists(path):
        return path
        
    directory, filename = os.path.split(path)
    name, ext = os.path.splitext(filename)
    counter = 1
    
    while True:
        new_name = f"{name}_{counter}{ext}"
        new_path = os.path.join(directory, new_name)
        if not os.path.exists(new_path):
            return new_path
        counter += 1

def main():
    args = parse_arguments()

    if args.out_dir:
        os.makedirs(args.out_dir, exist_ok=True)

    video_exts = [".mp4", ".avi", ".mov", ".mkv"]

    for file_path in args.media:
        ext = os.path.splitext(file_path)[1].lower()

        if ext in video_exts:
            # --- PROCESSING VIDEO ---
            print(f"Processing video: {file_path}")
            base_out = "glitched_" + os.path.basename(file_path)
            if args.out_dir:
                out_path = os.path.join(args.out_dir, base_out)
            else:
                out_path = base_out
            
            out_path = get_unique_filename(out_path)

            process_video(file_path, out_path, args)

        else:
            # --- PROCESSING IMAGE ---
            print(f"Processing image: {file_path}")

            try:
                # image to numpy array
                imgin = Image.open(file_path)
                imgin.load()
                data = np.asarray(imgin, dtype="int32")

                data = apply_effects(data, args)

                # numpy array to image
                final_data = (data % 256).astype(np.uint8)
                imgout = Image.fromarray(final_data, "RGB")

                if args.out_dir:
                    base_filename = os.path.basename(file_path)
                    save_path = os.path.join(args.out_dir, base_filename)

                    save_path = get_unique_filename(save_path)
                    imgout.save(save_path)
                else:
                    imgout.show()
            
            except Exception as e:
                print(f"There was an error processing {file_path}, {e}")

if __name__ == "__main__":
    main()