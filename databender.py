import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image
import numpy as np
from typing import Callable
import os

# --- ORIGINAL FUNCTIONS ---

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

def warp(data, mode, val):
    height = data.shape[0]
    val = float(val)

    for i in range(height):
        if mode == "normal":
            data[i] = np.roll(data[i], int(i/(21 - val)), axis=0)
        elif mode == "sin":
            data[i] = np.roll(data[i], int(val * np.sin(i / 10.0)), axis=0)
    return data

# --- A TKINTER GUI ---

class DatabendingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Databender")
        self.root.geometry("450x560")
        self.root.resizable(False, False)

        self.image_path = None

        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Upload Image
        file_frame = ttk.Frame(main_frame)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.btn_open = ttk.Button(file_frame, text="Upload image", command=self.load_image)
        self.btn_open.pack(side=tk.LEFT)
        
        self.lbl_file = ttk.Label(file_frame, text="No image uploaded")
        self.lbl_file.pack(side=tk.LEFT, padx=10)

        # 2. Color Manipulation
        color_frame = ttk.LabelFrame(main_frame, text="Color Manipulation", padding="5")
        color_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(color_frame, text="Color Offset (0-255):").grid(row=0, column=0, sticky=tk.W)
        self.var_color_offset = tk.IntVar(value=0)
        ttk.Scale(color_frame, from_=0, to=255, variable=self.var_color_offset, orient=tk.HORIZONTAL).grid(row=0, column=1, sticky=tk.EW, padx=5)

        # 3. Row Shifting
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

        # 4. Chromatic Aberration
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

        # 5. Pixel Sorting
        sorting_frame = ttk.LabelFrame(main_frame, text="Pixel Sorting", padding="5")
        sorting_frame.pack(fill=tk.X, pady=5)
        
        self.var_sort = tk.BooleanVar(value=False)
        ttk.Checkbutton(sorting_frame, text="Pixel sorting (based on luminosity)", variable=self.var_sort).grid(row=0, column=0, sticky=tk.W)

        # 6. Warping
        warp_frame = ttk.LabelFrame(main_frame, text="Warping", padding="5")
        warp_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(warp_frame, text="Mode:").grid(row=0, column=0, sticky=tk.W)
        self.var_warp_mode = tk.StringVar(value="none")
        warp_cb = ttk.Combobox(warp_frame, textvariable=self.var_warp_mode, values=["none", "normal", "sin"], state="readonly", width=10)
        warp_cb.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(warp_frame, text="Intensity:").grid(row=1, column=0, sticky=tk.W)
        self.var_warp_val = tk.DoubleVar(value=0.0)
        ttk.Entry(warp_frame, textvariable=self.var_warp_val, width=10).grid(row=1, column=1, sticky=tk.W)

        # 7. Action Buttons
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

    def process(self, save=False):
        if not self.image_path:
            messagebox.showwarning("Notice", "Please upload an image first!")
            return

        try:
            # Image to numpy array
            imgin = Image.open(self.image_path)
            imgin.load()
            data = np.asarray(imgin, dtype="int32")

            # 1. Color Offset
            data = color_offset(data, self.var_color_offset.get())

            # 2. Row Shifting
            if self.var_do_shift.get():
                data = row_shifting(data, self.var_probability.get(), self.var_shift.get())
            
            # 3. Chromatic Aberration
            data = chromatic_aberration(data, self.var_red.get(), self.var_green.get(), self.var_blue.get())    

            # 4. Pixel Sorting
            if self.var_sort.get():
                data = sort_pixels(data,
                        lambda pixels: np.average(pixels, axis=2) / 255,
                        lambda lum: (lum > 2 / 6) & (lum < 4 / 6), 1)
            
            # 5. Warping
            mode = self.var_warp_mode.get()
            if mode != "none":
                data = warp(data, mode, self.var_warp_val.get())

            # Numpy array to image
            final_data = (data % 256).astype(np.uint8)
            imgout = Image.fromarray(final_data, "RGB")

            # Handling results
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
