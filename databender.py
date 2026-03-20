import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image
import numpy as np
from typing import Callable
import os

# -------------------------------- ORIGINAL FUNCTIONS --------------------------------

def color_offset(data, offset):
    if offset == 0:
        return data
    else:
        return data + offset

def row_shifting(data, probability, max_shift):
    height = data.shape[0]
    for i in range(height):
        if np.random.rand() < probability:
            shift = np.random.randint(-max_shift, max_shift)
            data[i] = np.roll(data[i], shift, axis=0)
    return data

def chromatic_aberration(data, red, green, blue):
    if red > 0:
        data[:,:,0] = np.roll(data[:,:,0], red, axis=1)
    if green > 0:
        data[:,:,1] = np.roll(data[:,:,1], green, axis=1)
    if blue > 0:
        data[:,:,2] = np.roll(data[:,:,2], blue, axis=1)
    return data

def sort_pixels(data, value: Callable, condition: Callable, rotation: int = 0):
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
    r, g, b = np.split(pixels[:, :, :3], 3, 2)
    return np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)[:, :, 0]

def warp(data, mode, val):
    height = data.shape[0]
    val = float(val)

    for i in range(height):
        if mode == "normal":
            data[i] = np.roll(data[i], int(i/(21 - val)), axis=0)
        elif mode == "sin":
            data[i] = np.roll(data[i], int(val * np.sin(i / 10.0)), axis=0)
    return data

# -------------------------------- TKINTER GUI --------------------------------

class DatabendingApp:
    def __init__(self, root):
        version = "v1.1"
        self.root = root
        self.root.title(f"databender-{version}")
        self.root.minsize(450, 770)
        self.root.resizable(True, True)

        self.image_path = None

        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # upload image
        file_frame = ttk.Frame(main_frame)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.btn_open = ttk.Button(file_frame, text="Upload image", command=self.load_image)
        self.btn_open.pack(side=tk.LEFT)
        
        self.lbl_file = ttk.Label(file_frame, text="No image uploaded")
        self.lbl_file.pack(side=tk.LEFT, padx=10)

        #info
        info_frame = ttk.LabelFrame(main_frame, text="Image Info", padding="5")
        info_frame.pack(fill=tk.X, pady=(0, 10))

        self.var_info_x = tk.StringVar(value="X: ")
        self.var_info_y = tk.StringVar(value="Y: ")

        self.lbl_info_x = ttk.Label(info_frame, textvariable=self.var_info_x)
        self.lbl_info_x.pack(side=tk.LEFT, padx=(5, 20))

        self.lbl_info_y = ttk.Label(info_frame, textvariable=self.var_info_y)
        self.lbl_info_y.pack(side=tk.LEFT, padx=5)

        # region of interest (ROI)
        roi_frame = ttk.LabelFrame(main_frame, text="Region of Interest (Area Mask)", padding="5")
        roi_frame.pack(fill=tk.X, pady=5)

        self.var_roi_enable = tk.BooleanVar(value=False)
        ttk.Checkbutton(roi_frame, text="Enable Area Mask", variable=self.var_roi_enable).grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=(0, 5))

        # coordinate sliders/fields
        ttk.Label(roi_frame, text="X Pos:").grid(row=1, column=0, sticky=tk.E, padx=2)
        self.var_roi_x = tk.IntVar(value=0)
        self.slider_roi_x = ttk.Scale(roi_frame, from_=0, to=100, variable=self.var_roi_x, orient=tk.HORIZONTAL, command=lambda v: self.var_roi_x.set(int(float(v))))
        self.slider_roi_x.grid(row=1, column=1, sticky=tk.EW, padx=5)
        ttk.Entry(roi_frame, textvariable=self.var_roi_x, width=5).grid(row=1, column=2, sticky=tk.W)

        ttk.Label(roi_frame, text="Y Pos:").grid(row=1, column=3, sticky=tk.E, padx=5)
        self.var_roi_y = tk.IntVar(value=0)
        self.slider_roi_y = ttk.Scale(roi_frame, from_=0, to=100, variable=self.var_roi_y, orient=tk.HORIZONTAL, command=lambda v: self.var_roi_y.set(int(float(v))))
        self.slider_roi_y.grid(row=1, column=4, sticky=tk.EW, padx=5)
        ttk.Entry(roi_frame, textvariable=self.var_roi_y, width=5).grid(row=1, column=5, sticky=tk.W)

        ttk.Label(roi_frame, text="Width:").grid(row=2, column=0, sticky=tk.E, padx=2, pady=2)
        self.var_roi_w = tk.StringVar(value="200")
        ttk.Entry(roi_frame, textvariable=self.var_roi_w, width=5).grid(row=2, column=1, sticky=tk.W, pady=2)

        ttk.Label(roi_frame, text="Height:").grid(row=2, column=3, sticky=tk.E, padx=(10, 2), pady=2)
        self.var_roi_h = tk.StringVar(value="200")
        ttk.Entry(roi_frame, textvariable=self.var_roi_h, width=5).grid(row=2, column=4, sticky=tk.W, pady=2)
        
        # color manipulation
        color_frame = ttk.LabelFrame(main_frame, text="Color Manipulation", padding="5")
        color_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(color_frame, text="Color Offset (0-255):").grid(row=0, column=0, sticky=tk.W)
        self.var_color_offset = tk.IntVar(value=0)

        self.lbl_color_val = ttk.Label(color_frame, text="0")
        self.lbl_color_val.grid(row=0, column=2, sticky=tk.W, padx=5)

        def update_color_lbl(val):
            self.lbl_color_val.config(text=str(int(float(val))))

        ttk.Scale(color_frame, from_=0, to=255, variable=self.var_color_offset, orient=tk.HORIZONTAL, command=update_color_lbl).grid(row=0, column=1, sticky=tk.EW, padx=5)

        # row shifting
        shift_frame = ttk.LabelFrame(main_frame, text="Row Shifting", padding="5")
        shift_frame.pack(fill=tk.X, pady=5)
        
        self.var_do_shift = tk.BooleanVar(value=False)
        ttk.Checkbutton(shift_frame, text="Enable", variable=self.var_do_shift).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        ttk.Label(shift_frame, text="Probability (0.0-1.0):").grid(row=1, column=0, sticky=tk.W)
        self.var_probability = tk.DoubleVar(value=0.2)
        ttk.Entry(shift_frame, textvariable=self.var_probability, width=10).grid(row=1, column=1, sticky=tk.W)
        
        ttk.Label(shift_frame, text="Max Shift (px):").grid(row=2, column=0, sticky=tk.W)
        self.var_shift = tk.IntVar(value=50)
        ttk.Entry(shift_frame, textvariable=self.var_shift, width=10).grid(row=2, column=1, sticky=tk.W)

        # chromatic aberration
        aberration_frame = ttk.LabelFrame(main_frame, text="Chromatic Aberration", padding="5")
        aberration_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(aberration_frame, text="Red Shift:").grid(row=0, column=0, sticky=tk.W)
        self.var_red = tk.IntVar(value=0)
        ttk.Entry(aberration_frame, textvariable=self.var_red, width=10).grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(aberration_frame, text="Green Shift:").grid(row=1, column=0, sticky=tk.W)
        self.var_green = tk.IntVar(value=0)
        ttk.Entry(aberration_frame, textvariable=self.var_green, width=10).grid(row=1, column=1, sticky=tk.W)
        
        ttk.Label(aberration_frame, text="Blue Shift:").grid(row=2, column=0, sticky=tk.W)
        self.var_blue = tk.IntVar(value=0)
        ttk.Entry(aberration_frame, textvariable=self.var_blue, width=10).grid(row=2, column=1, sticky=tk.W)

        # pixel sorting
        sorting_frame = ttk.LabelFrame(main_frame, text="Pixel Sorting", padding="5")
        sorting_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(sorting_frame, text="Mode:").grid(row=0, column=0, sticky=tk.W)
        self.var_sort_mode =tk.StringVar(value="none")
        sort_cb = ttk.Combobox(sorting_frame, textvariable=self.var_sort_mode, values=["none", "lum", "hue"], state="readonly", width=10)
        sort_cb.grid(row=0, column=1, sticky=tk.W)
        
        # warping
        warp_frame = ttk.LabelFrame(main_frame, text="Warping", padding="5")
        warp_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(warp_frame, text="Mode:").grid(row=0, column=0, sticky=tk.W)
        self.var_warp_mode = tk.StringVar(value="none")
        warp_cb = ttk.Combobox(warp_frame, textvariable=self.var_warp_mode, values=["none", "normal", "sin"], state="readonly", width=10)
        warp_cb.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(warp_frame, text="Intensity:").grid(row=1, column=0, sticky=tk.W)
        self.var_warp_val = tk.DoubleVar(value=0.0)
        ttk.Entry(warp_frame, textvariable=self.var_warp_val, width=10).grid(row=1, column=1, sticky=tk.W)

        # action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=15)

        self.btn_preview = ttk.Button(action_frame, text="Process and View", command=lambda: self.process(save=False))
        self.btn_preview.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.btn_save = ttk.Button(action_frame, text="Save as...", command=lambda: self.process(save=True))
        self.btn_save.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

    def load_image(self):
        filetypes = (
            ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff"),
            ("Every file", "*.*")
        )
        filepath = filedialog.askopenfilename(title="Choose an image", filetypes=filetypes)
        if filepath:
            self.image_path = filepath
            self.lbl_file.config(text=os.path.basename(filepath))
        
            try:
                    with Image.open(filepath) as img:
                        w, h = img.size
                    
                    self.var_info_x.set(f"X: {w}")
                    self.var_info_y.set(f"Y: {h}")

                    self.slider_roi_x.config(to=w-1)
                    self.slider_roi_y.config(to=h-1)

                    self.var_roi_x.set(0)
                    self.var_roi_y.set(0)
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read image dimensions:\n{str(e)}")

    def process(self, save=False):
        if not self.image_path:
            messagebox.showwarning("Notice", "Please upload an image first!")
            return

        try:
            # image to numpy array
            imgin = Image.open(self.image_path)
            imgin.load()
            data = np.asarray(imgin, dtype="int32")
            
            img_h, img_w = data.shape[:2]

            # ROI cut
            if self.var_roi_enable.get():
                try:
                    rx = self.var_roi_x.get()
                    ry = self.var_roi_y.get()

                    rw = int(self.var_roi_w.get()) if self.var_roi_w.get() else img_w
                    rh = int(self.var_roi_h.get()) if self.var_roi_h.get() else img_h

                    rw = max(1, min(rw, img_w - rx))
                    rh = max(1, min(rh, img_h - ry))

                    target_data = data[ry:ry+rh, rx:rx+rw].copy()

                except ValueError:
                    messagebox.showerror("Error", "ROI coordinates must be whole numbers!")
                    return
            else:
                target_data = data
            
            # color offset
            target_data = color_offset(target_data, self.var_color_offset.get())

            # row shifting
            if self.var_do_shift.get():
                target_data = row_shifting(target_data, self.var_probability.get(), self.var_shift.get())
            
            # chromatic aberration
            target_data = chromatic_aberration(target_data, self.var_red.get(), self.var_green.get(), self.var_blue.get())    

            # pixel sorting
            sort_mode = self.var_sort_mode.get()
            if sort_mode == "lum":
                target_data = sort_pixels(target_data,
                    lambda pixels: np.average(pixels, axis=2) / 255,
                    lambda lum: (lum > 2 / 6) & (lum < 4 / 6), 1)
            
            elif sort_mode == "hue":
                target_data = sort_pixels(target_data, hue, lambda h: (h > 2 / 6) & (h < 4 / 6), 1)
            
            # warping
            warp_mode = self.var_warp_mode.get()
            if warp_mode != "none":
                target_data = warp(target_data, warp_mode, self.var_warp_val.get())

            # --- placing the ROI back on the image ---
            if self.var_roi_enable.get():
                data[ry:ry+rh, rx:rx+rw] = target_data
            else:
                data = target_data

            # numpy array to image
            final_data = (data % 256).astype(np.uint8)
            imgout = Image.fromarray(final_data, "RGB")

            # handling results
            if save:
                save_path = filedialog.asksaveasfilename(
                    defaultextension=".png", 
                    filetypes=[("PNG file", "*.png"), ("JPEG file", "*.jpg")]
                )
                if save_path:
                    imgout.save(save_path)
                    messagebox.showinfo("Success", f"Image successfully saved:\n{save_path}")
            else:
                imgout.show()

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while processing the image:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DatabendingApp(root)
    root.mainloop()