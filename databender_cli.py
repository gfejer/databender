import argparse
import os
import imageio

from core.filters import *
from core.processor import apply_effects


def parse_arguments():
    # flag arguments
    parser = argparse.ArgumentParser(description="a databending script for manipulating images/videos.")
    parser.add_argument("file", nargs='+', type=str, help="The path of your image/video.", metavar="FILE")

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

def build_config(args):
    config = {
        "color_offset": args.color_offset,
        
        "do_shift": args.do_shift,
        "shift_prob": args.probability,
        "shift_max": args.shift,

        "red": args.red,
        "green": args.green,
        "blue": args.blue,

        "sort_mode": args.sort
    }

    # ROI
    if args.roi:
        config["roi_mode"] = args.roi[0]
        config["roi_x"] = int(args.roi[1])
        config["roi_y"] = int(args.roi[2])
        config["roi_w"] = int(args.roi[3])
        config["roi_h"] = int(args.roi[4])
    else:
        config["roi_mode"] = "none"

    # warp
    if args.warp:
        config["warp_mode"] = args.warp[0]
        config["warp_val"] = float(args.warp[1])
    else:
        config["warp_mode"] = "none"
        config["warp_val"] = 0.0

    return config

def process_video(input_path, output_path, config):
    reader = imageio.get_reader(input_path)
    meta = reader.get_meta_data()
    fps = meta["fps"]
        
    try:
        total_frames = reader.count_frames()
    except:
        total_frames = int(meta.get("duration", 0) * fps) # if imageio can't count frames (missing from header)
        if total_frames <= 0: total_frames = 100 # if the duration is missing from meta 

    writer = imageio.get_writer(output_path, fps=fps, codec="libx264", macro_block_size=None)

    frame_count = 0
        
    for frame in reader:
        frame_count += 1

        if total_frames != "Unknown":
            print(f"Processing frame: {frame_count}/{total_frames}", end="\r")

        else:
            print(f"Processing frame: {frame_count}", end="\r")

        data = np.array(frame, dtype=np.int32)
        data = apply_effects(data, config)

        final_data = (data % 256).astype(np.uint8)
        writer.append_data(final_data)
        
    reader.close()
    writer.close()
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
    config = build_config(args)
    print(config)

    if args.out_dir:
        os.makedirs(args.out_dir, exist_ok=True)

    video_exts = [".mp4", ".avi", ".mov", ".mkv"]

    for file_path in args.file:
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

            process_video(file_path, out_path, config)

        else:
            # --- PROCESSING IMAGE ---
            print(f"Processing image: {file_path}")

            try:
                # image to numpy array
                imgin = Image.open(file_path)
                imgin.load()
                data = np.asarray(imgin, dtype="int32")

                data = apply_effects(data, config)

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