import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# for processing video
import os
import imageio

# for update functions
import urllib.request
import json
import ssl
import certifi

import webbrowser
import threading
import queue

from core.filters import *
from core.processor import apply_effects

class databender:
    def __init__(self, root):
        self.version = "v1.3.2"
        self.repo_url = "gfejer/databender"
        self.update_queue = queue.Queue()

        self.root = root
        self.root.title(f"databender-{self.version}")

        self.root.minsize(650, 750)
        self.root.geometry("650x750")
        self.root.resizable(True, True)

        self.image_path = None
        self.video_exts = [".mp4", ".avi", ".mov", ".mkv"]

        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # upload file
        fileandupdate_frame = ttk.Frame(main_frame)
        fileandupdate_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.btn_open = ttk.Button(fileandupdate_frame, text="Upload File", command=self.load_file)
        self.btn_open.pack(side=tk.LEFT)
        
        self.lbl_file = ttk.Label(fileandupdate_frame, text="No file uploaded")
        self.lbl_file.pack(side=tk.LEFT, padx=10)

        # update button
        self.btn_update = ttk.Button(fileandupdate_frame, text="Check for Updates", command=self.start_update_check)
        self.btn_update.pack(side=tk.RIGHT, padx=5)

        # info
        info_frame = ttk.LabelFrame(main_frame, text="Info", padding="5")
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

        roi_frame.columnconfigure(1, weight=1)
        roi_frame.columnconfigure(4, weight=1)

        ttk.Label(roi_frame, text="Mode:").grid(row=0, column=0, sticky=tk.E, padx=2)
        self.var_roi_mode = tk.StringVar(value="none")
        roi_cb = ttk.Combobox(roi_frame, textvariable=self.var_roi_mode, values=["none", "inside", "outside"], state="readonly", width=8)
        roi_cb.grid(row=0, column=1, sticky=tk.W)

        # coordinate sliders/fields
        ttk.Label(roi_frame, text="X Pos:").grid(row=1, column=0, sticky=tk.E, padx=2)
        self.var_roi_x = tk.IntVar(value=0)
        self.slider_roi_x = ttk.Scale(roi_frame, from_=0, to=100, variable=self.var_roi_x, orient=tk.HORIZONTAL, command=lambda v: self.var_roi_x.set(int(float(v))))
        self.slider_roi_x.grid(row=1, column=1, sticky=tk.EW, padx=5)
        ttk.Entry(roi_frame, textvariable=self.var_roi_x, width=8).grid(row=1, column=2, sticky=tk.W)

        ttk.Label(roi_frame, text="Y Pos:").grid(row=1, column=3, sticky=tk.E, padx=5)
        self.var_roi_y = tk.IntVar(value=0)
        self.slider_roi_y = ttk.Scale(roi_frame, from_=0, to=100, variable=self.var_roi_y, orient=tk.HORIZONTAL, command=lambda v: self.var_roi_y.set(int(float(v))))
        self.slider_roi_y.grid(row=1, column=4, sticky=tk.EW, padx=5)
        ttk.Entry(roi_frame, textvariable=self.var_roi_y, width=8).grid(row=1, column=5, sticky=tk.W)

        ttk.Label(roi_frame, text="Width:").grid(row=2, column=0, sticky=tk.E, padx=2, pady=2)
        self.var_roi_w = tk.StringVar(value="200")
        ttk.Entry(roi_frame, textvariable=self.var_roi_w, width=8).grid(row=2, column=1, sticky=tk.W, pady=2)

        ttk.Label(roi_frame, text="Height:").grid(row=2, column=3, sticky=tk.E, padx=(10, 2), pady=2)
        self.var_roi_h = tk.StringVar(value="200")
        ttk.Entry(roi_frame, textvariable=self.var_roi_h, width=8).grid(row=2, column=4, sticky=tk.W, pady=2)

        # color manipulation
        color_frame = ttk.LabelFrame(main_frame, text="Color Manipulation", padding="5")
        color_frame.pack(fill=tk.X, pady=5)
        
        color_frame.columnconfigure(1, weight=1)

        ttk.Label(color_frame, text="Color Offset (0-255):").grid(row=0, column=0, sticky=tk.W)
        self.var_color_offset = tk.IntVar(value=0)
            
        ttk.Scale(color_frame, from_=0, to=255, variable=self.var_color_offset, orient=tk.HORIZONTAL, command=lambda v: self.var_color_offset.set(int(float(v)))).grid(row=0, column=1, sticky=tk.EW, padx=5)
        ttk.Entry(color_frame, textvariable=self.var_color_offset, width=8).grid(row=0, column=2, sticky=tk.W, padx=5)

        row1_frame = ttk.Frame(main_frame)
        row1_frame.pack(fill=tk.X, pady=5)

        # row shifting
        shift_frame = ttk.LabelFrame(row1_frame, text="Row Shifting", padding="5")
        shift_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.var_do_shift = tk.BooleanVar(value=False)
        ttk.Checkbutton(shift_frame, text="Enable", variable=self.var_do_shift).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        ttk.Label(shift_frame, text="Probability (0.0-1.0):").grid(row=1, column=0, sticky=tk.W)
        self.var_probability = tk.DoubleVar(value=0.2)
        ttk.Entry(shift_frame, textvariable=self.var_probability, width=8).grid(row=1, column=1, sticky=tk.W)
        
        ttk.Label(shift_frame, text="Max Shift (px):").grid(row=2, column=0, sticky=tk.W)
        self.var_shift = tk.IntVar(value=50)
        ttk.Entry(shift_frame, textvariable=self.var_shift, width=8).grid(row=2, column=1, sticky=tk.W)

        # chromatic aberration
        aberration_frame = ttk.LabelFrame(row1_frame, text="Chromatic Aberration", padding="5")
        aberration_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        ttk.Label(aberration_frame, text="Red Shift:").grid(row=0, column=0, sticky=tk.W)
        self.var_red = tk.IntVar(value=0)
        ttk.Entry(aberration_frame, textvariable=self.var_red, width=8).grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(aberration_frame, text="Green Shift:").grid(row=1, column=0, sticky=tk.W)
        self.var_green = tk.IntVar(value=0)
        ttk.Entry(aberration_frame, textvariable=self.var_green, width=8).grid(row=1, column=1, sticky=tk.W)
        
        ttk.Label(aberration_frame, text="Blue Shift:").grid(row=2, column=0, sticky=tk.W)
        self.var_blue = tk.IntVar(value=0)
        ttk.Entry(aberration_frame, textvariable=self.var_blue, width=8).grid(row=2, column=1, sticky=tk.W)

        row2_frame = ttk.Frame(main_frame)
        row2_frame.pack(fill=tk.X, pady=5)

        # warping
        warp_frame = ttk.LabelFrame(row2_frame, text="Warping", padding="5")
        warp_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        ttk.Label(warp_frame, text="Mode:").grid(row=0, column=0, sticky=tk.W)
        self.var_warp_mode = tk.StringVar(value="none")
        warp_cb = ttk.Combobox(warp_frame, textvariable=self.var_warp_mode, values=["none", "normal", "sin"], state="readonly", width=8)
        warp_cb.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(warp_frame, text="Intensity:").grid(row=1, column=0, sticky=tk.W)
        self.var_warp_val = tk.DoubleVar(value=0.0)
        ttk.Entry(warp_frame, textvariable=self.var_warp_val, width=8).grid(row=1, column=1, sticky=tk.W)

        # block displacement
        displace_frame = ttk.LabelFrame(row2_frame, text="Block Displacement", padding=5)
        displace_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        displace_frame.columnconfigure(1, weight=1)

        ttk.Label(displace_frame, text="Number of Blocks:").grid(row=0, column=0, sticky=tk.W)
        self.var_num_blocks = tk.IntVar(value=0)
        ttk.Scale(displace_frame, from_=0, to=500, variable=self.var_num_blocks, orient=tk.HORIZONTAL, command=lambda v: self.var_num_blocks.set(int(float(v)))).grid(row=0, column=1, sticky=tk.EW, padx=5)
        ttk.Entry(displace_frame, textvariable=self.var_num_blocks, width=3).grid(row=0, column=2, sticky=tk.W)

        ttk.Label(displace_frame, text="Max Block Size:").grid(row=1, column=0, sticky=tk.W)
        self.var_max_block_size = tk.IntVar(value=10)
        ttk.Scale(displace_frame, from_=10, to=500, variable=self.var_max_block_size, orient=tk.HORIZONTAL, command=lambda v: self.var_max_block_size.set(int(float(v)))).grid(row=1, column=1, sticky=tk.EW, padx=5)
        ttk.Entry(displace_frame, textvariable=self.var_max_block_size, width=3).grid(row=1, column=2, sticky=tk.W)

        ttk.Label(displace_frame, text="Max Shift Amount").grid(row=2, column=0, sticky=tk.W)
        self.var_shift_amount = tk.IntVar(value=0)
        ttk.Scale(displace_frame, from_=0, to=500, variable=self.var_shift_amount, orient=tk.HORIZONTAL, command=lambda v: self.var_shift_amount.set(int(float(v)))).grid(row=2, column=1, sticky=tk.EW, padx=5)
        ttk.Entry(displace_frame, textvariable=self.var_shift_amount, width=3).grid(row=2, column=2, sticky=tk.W)

        row3_frame = ttk.Frame(main_frame)
        row3_frame.pack(fill=tk.X, pady=5)

        # channel swapping
        swapping_frame = ttk.LabelFrame(row3_frame, text="Channel Swapping", padding="5")
        swapping_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        ttk.Label(swapping_frame, text="Mode:").grid(row=0, column=0, sticky=tk.W)
        self.var_channel_swapping_mode = tk.StringVar(value="none")
        swap_cb = ttk.Combobox(swapping_frame, textvariable=self.var_channel_swapping_mode, values=["none", "RBG", "GRB", "GBR", "BRG", "BGR"], state="readonly", width=8)
        swap_cb.grid(row=0, column=1, sticky=tk.W)

        # pixel sorting
        sorting_frame = ttk.LabelFrame(row3_frame, text="Pixel Sorting", padding="5")
        sorting_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        ttk.Label(sorting_frame, text="Mode:").grid(row=0, column=0, sticky=tk.W)
        self.var_sort_mode =tk.StringVar(value="none")
        sort_cb = ttk.Combobox(sorting_frame, textvariable=self.var_sort_mode, values=["none", "lum", "hue"], state="readonly", width=8)
        sort_cb.grid(row=0, column=1, sticky=tk.W)

        # progress bar
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.lbl_status = ttk.Label(self.progress_frame)
        self.lbl_status.pack(side=tk.TOP, anchor=tk.W)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, maximum=100)
        
        # action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=15)

        self.btn_preview = ttk.Button(action_frame, text="Process and View", command=lambda: self.process(save=False))
        self.btn_preview.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.btn_save = ttk.Button(action_frame, text="Save as...", command=lambda: self.process(save=True))
        self.btn_save.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

    def start_update_check(self):
        self.btn_update.config(state=tk.DISABLED, text="Checking...")
        threading.Thread(target=self.check_for_updates, daemon=True).start()
        self.root.after(100, self.process_update_queue)

    def check_for_updates(self):
        # runs in the background on another thread
        api_url = f"https://api.github.com/repos/{self.repo_url}/releases/latest"
        
        try:
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            context = ssl.create_default_context(cafile=certifi.where())

            with urllib.request.urlopen(req, timeout=5, context=context) as response:
                data = json.loads(response.read().decode())
                
            latest_version = data.get("tag_name", "")
            release_url = data.get("html_url", "")
            
            # result gets thrown in the queue
            self.update_queue.put({"status": "success", "version": latest_version, "url": release_url})
            
        except Exception as e:
            # error gets thrown in the queue
            self.update_queue.put({"status": "error", "message": str(e)})

    def process_update_queue(self):
        # this runs on the main thread
        try:
            # check whether there is queue
            result = self.update_queue.get_nowait()
            
            # if so, the butting is enabled again
            self.btn_update.config(state=tk.NORMAL, text="Check for Updates")
            
            if result["status"] == "success":
                latest_version = result["version"]
                release_url = result["url"]
                
                # comparing versions
                if latest_version > self.version:
                    msg = f"A new version is available! ({latest_version})\n\nYou are currently using {self.version}.\nWould you like to download the update?"
                    if messagebox.askyesno("Update Available", msg):
                        webbrowser.open(release_url)
                else:
                    messagebox.showinfo("Up to date", f"You are using the latest version ({self.version}).")
                    
            elif result["status"] == "error":
                messagebox.showerror("Update Error", f"Could not check for updates.\n\nError: {result['message']}")
                
        except queue.Empty:
            # if the queue is empty, we check again after 100ms
            self.root.after(100, self.process_update_queue)

    def load_file(self):
        filetypes = (
            ("Media files", "*.jpg *.jpeg *.png *.bmp *.mp4 *.avi *.mov *.mkv"),
            ("Image files", "*.jpg *.jpeg *.png *.bmp"),
            ("Video files", "*.mp4 *.avi *.mov *.mkv"),
            ("Every file", "*.*")
        )
        filepath = filedialog.askopenfilename(title="Choose a file", filetypes=filetypes)
        
        if filepath:
            self.image_path = filepath
            self.lbl_file.config(text=os.path.basename(filepath))
            ext = os.path.splitext(filepath)[1].lower()
        
            try:
                # image/video resolution
                if ext in self.video_exts:
                    reader = imageio.get_reader(filepath)
                    meta = reader.get_meta_data()
                    w, h = meta["size"]
                    reader.close()
                else:
                    with Image.open(filepath) as img:
                        w, h = img.size
                
                self.var_info_x.set(f"X: {w}")
                self.var_info_y.set(f"Y: {h}")

                self.slider_roi_x.config(to=max(0, w-1))
                self.slider_roi_y.config(to=max(0, h-1))

                self.var_roi_x.set(0)
                self.var_roi_y.set(0)

            except Exception as e:
                messagebox.showerror("Error", f"Failed to read image dimensions:\n{str(e)}")

    def process_video_render(self, input_path, save_path, config):
        reader = imageio.get_reader(input_path)
        meta = reader.get_meta_data()
        fps = meta["fps"]
        
        try:
            total_frames = reader.count_frames()
        except:
            total_frames = int(meta.get("duration", 0) * fps) # if imageio can't count frames (missing from header), it tries to 
            if total_frames <= 0: total_frames = 100 # if the duration is missing from meta 

        writer = imageio.get_writer(save_path, fps=fps, codec="libx264", macro_block_size=None)

        self.progress_bar.pack(fill=tk.X, expand=True, pady=5)
        self.btn_preview.config(state=tk.DISABLED)
        self.btn_save.config(state=tk.DISABLED)

        frame_count = 0
        for frame in reader:
            frame_count += 1
            
            data = np.array(frame, dtype=np.int32)
            data = apply_effects(data, config)
            
            final_data = (data % 256).astype(np.uint8)
            writer.append_data(final_data)

            # updating GUI
            if total_frames > 0:
                progress = min((frame_count / total_frames) * 100, 100)
                self.progress_var.set(progress)
                self.lbl_status.config(text=f"Rendering video... {frame_count} / {total_frames} frames")
            else:
                self.lbl_status.config(text=f"Rendering video... {frame_count} frames") # if the total frame count is unknown
            self.root.update()

        reader.close()
        writer.close()
            
        # cleaning up
        self.progress_bar.pack_forget()
        self.lbl_status.config(text="")
        self.btn_preview.config(state=tk.NORMAL)
        self.btn_save.config(state=tk.NORMAL)
        self.progress_var.set(0)

        messagebox.showinfo("Success", f"Video successfully saved:\n{save_path}")

    def process(self, save=False):
        if not self.image_path:
            messagebox.showwarning("Notice", "Please upload a file first!")
            return
        try:
            roi_w = int(self.var_roi_w.get()) if self.var_roi_w.get() else 200
            roi_h = int(self.var_roi_h.get()) if self.var_roi_h.get() else 200
        except ValueError:
            roi_w, roi_h = 200, 200

        config = {
            "roi_mode": self.var_roi_mode.get(),
            "roi_x": self.var_roi_x.get(),
            "roi_y": self.var_roi_y.get(),
            "roi_w": roi_w,
            "roi_h": roi_h,

            "color_offset": self.var_color_offset.get(),

            "do_shift": self.var_do_shift.get(),
            "shift_prob": self.var_probability.get(),
            "shift_max": self.var_shift.get(),

            "red": self.var_red.get(),
            "green": self.var_green.get(),
            "blue": self.var_blue.get(),

            "cswap_mode": self.var_channel_swapping_mode.get(),

            "sort_mode": self.var_sort_mode.get(),

            "warp_mode": self.var_warp_mode.get(),
            "warp_val": self.var_warp_val.get(),

            "num_blocks": self.var_num_blocks.get(), 
            "max_block_size": self.var_max_block_size.get(),
            "shift_amount": self.var_shift_amount.get()
        }

        ext = os.path.splitext(self.image_path)[1].lower()
        is_video = ext in self.video_exts

        try:
            # --- PROCESSING VIDEO ---
            if is_video:
                if save:
                    save_path = filedialog.asksaveasfilename(
                        defaultextension=".mp4", 
                        filetypes=[("MP4 Video", "*.mp4")]
                    )
                    if save_path:
                        self.process_video_render(self.image_path, save_path, config)
                else:
                    # showing the first frame edited
                    self.lbl_status.config(text="Generating frame preview...")
                    self.root.update()
                    
                    try:
                        reader = imageio.get_reader(self.image_path)
                        frame = reader.get_data(0)
                        reader.close()
                        
                        data = np.array(frame, dtype=np.int32)
                        data = apply_effects(data, config)
                        final_data = (data % 256).astype(np.uint8)
                        imgout = Image.fromarray(final_data, "RGB")
                        imgout.show()

                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to preview video frame:\n{e}")
                    
                    self.lbl_status.config(text="")

            else:
                # --- PROCESSING IMAGE ---
                self.lbl_status.config(text="Processing image...")
                self.root.update()

                imgin = Image.open(self.image_path)
                imgin.load()
                data = np.asarray(imgin, dtype="int32")

                data = apply_effects(data, config)

                final_data = (data % 256).astype(np.uint8)
                imgout = Image.fromarray(final_data, "RGB")

                self.lbl_status.config(text="")

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
            self.lbl_status.config(text="")
            self.progress_bar.pack_forget()
            self.btn_preview.config(state=tk.NORMAL)
            self.btn_save.config(state=tk.NORMAL)
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = databender(root)
    root.mainloop()