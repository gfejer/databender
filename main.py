from PIL import Image
import numpy as np
import argparse
import scipy

def parse_arguments():
    # flag arguments
    parser = argparse.ArgumentParser(description="Databending script for manipulating images.")
    parser.add_argument("image", type=str, help="The path of your image.", metavar="IMAGE")

    color_group = parser.add_argument_group('Color Manipulation')
    color_group.add_argument("-c", "--color-offset", type=int, required=False, default=0, help="Adds an integer value to all color channels (R, G, B) using wrap-around (modulo 256) arithmetic. (0-255)")

    shift_group = parser.add_argument_group('Row Shifting (Glitch Effect)')
    shift_group.add_argument("--do-shift", action="store_true", help="Enable row shifting with default values.")
    shift_group.add_argument("-p", "--probability", type=float, required=False, default=None, help="Probability of a row being shifted (0.0 - 1.0). (Default: 0.2)")
    shift_group.add_argument("-x", "--shift", type=int, default=None, help="Maximum horizontal shift in pixels (Default: 50)")

    aberration_group = parser.add_argument_group("Chromatic Aberration")
    aberration_group.add_argument("-r", "--red", type=int, default=0, help=("Horizontal shift of the red channel.  (Default: 0)"))
    aberration_group.add_argument("-g", "--green", type=int, default=0, help=("Horizontal shift of the green channel. (Default: 0)"))
    aberration_group.add_argument("-b", "--blue", type=int, default=0, help=("Horizontal shift of the blue channel. (Default: 0)"))

    parser.add_argument("-s", "--save", type=str, required=False, help="Input filename to save file.", metavar="FILENAME")

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
    if red > 0:
        data[:,:,0] = np.roll(data[:,:,0], red, axis=1)
    if green > 0:
        data[:,:,1] = np.roll(data[:,:,1], green, axis=1)
    if blue > 0:
        data[:,:,2] = np.roll(data[:,:,2], blue, axis=1)
    else:
        pass

    return data

def main():
    args = parse_arguments()

    # image to numpy array
    imgin = Image.open(args.image)
    imgin.load()
    data = np.asarray(imgin, dtype="int32")

    data = color_offset(data, args.color_offset)

    if args.do_shift:
        data = row_shifting(data, args.probability, args.shift)
    
    data = chromatic_aberration(data, args.red, args.green, args.blue)

    # numpy array to image
    final_data = (data % 256).astype(np.uint8)
    imgout = Image.fromarray(final_data, "RGB")

    if args.save:
        imgout.save(args.save)
    else:
        imgout.show()

if __name__ == "__main__":
    main()