from PIL import Image
import numpy as np
import argparse
import scipy

# flag arguments
parser = argparse.ArgumentParser(description="Databending script for manipulating images.")
parser.add_argument("image", type=str, help="The path of your image.", metavar="IMAGE")

color_group = parser.add_argument_group('Color Manipulation')
color_group.add_argument("-c", "--color-offset", type=int, required=False, default=0, help="Adds an integer value to all color channels (R, G, B) using wrap-around (modulo 256) arithmetic. (0-255)")

shift_group = parser.add_argument_group('Row Shifting (Glitch Effect)')
shift_group.add_argument("--do-shift", action="store_true", help="Enable row shifting with default values.")
shift_group.add_argument("-p", "--probability", type=float, required=False, default=0.2, help="Probability of a row being shifted (0.0 - 1.0). (Default: 0.2)")
shift_group.add_argument("-x", "--shift", type=int, default=50, help="Maximum horizontal shift in pixels (Default: 50)")

abberation_group = parser.add_argument_group("Color Abberation")
abberation_group.add_argument("-r", "--red", type=int, default=0, help=("Horizontal shift of the red channel. (Default: 0)"))
abberation_group.add_argument("-g", "--green", type=int, default=0, help=("Horizontal shift of the green channel. (Default: 0)"))
abberation_group.add_argument("-b", "--blue", type=int, default=0, help=("Horizontal shift of the blue channel. (Default: 0)"))

parser.add_argument("-s", "--save", type=str, required=False, help="Input filename to save file.", metavar="FILENAME")

args = parser.parse_args()

# check if row shifting is enabled
if not args.do_shift and (args.probability != 0.2 or args.shift != 50):
    parser.error("The -p/--probability and -x/--shift arguments require --do-shift to be enabled.")

image_path = args.image

# image to numpy array
imgin = Image.open(image_path)
imgin.load()
data = np.asarray(imgin, dtype="int32")

height, width, channel = data.shape

# array manipulation
# color offset
data += args.color_offset

# row shifting
if args.do_shift == True:
    for i in range(height):
        if np.random.rand() < args.probability:
            shift = np.random.randint(-args.shift, args.shift)
            data[i] = np.roll(data[i], shift, axis=0)

# color abberation
if args.red > 0:
    data[:,:,0] = np.roll(data[:,:,0], 30, axis=1)
elif args.green > 0:
    data[:,:,1] = np.roll(data[:,0,:], 30, axis=1)
elif args.blue > 0:
    data[:,:,2] = np.roll(data[:,:,1], 30, axis=1)
else:
    pass

"""
if np.random.rand() > 0.9:
    data[i] = np.sort(data[i], axis=0)
"""
    
# numpy array to image
final_data = (data % 256).astype(np.uint8)
imgout = Image.fromarray(final_data, "RGB")

if args.save is None:
    imgout.show()
else:
    imgout.save(args.save)
