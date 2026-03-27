import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox

# for image and array processing
import numpy as np
from PIL import Image

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
        self.version = "v1.3.3"
        self.repo_url = "gfejer/databender"
        self.update_queue = queue.Queue()

        self.root = root
        self.root.title(f"databender-{self.version}")

        self.root.minsize(550, 600)
        self.root.geometry("550x600")
        self.root.resizable(True, True)

        self.image_path = None
        self.video_exts = [".mp4", ".avi", ".mov", ".mkv"]
        self.stop_processing = False

        self.create_widgets()

    def create_widgets(self):
        # ==========================================
        #               1. Top Frame
        # ==========================================
        top_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        top_frame.pack(side="top", fill="x", padx=10, pady=(10, 5))
        
        self.btn_open = ctk.CTkButton(top_frame, text="Upload File",corner_radius=6 ,command=self.load_file)
        self.btn_open.pack(side="left")
        
        self.lbl_file = ctk.CTkLabel(top_frame, text="No file uploaded")
        self.lbl_file.pack(side="left", padx=10)

        self.btn_update = ctk.CTkButton(top_frame, text="Check for Updates",corner_radius=6, command=self.start_update_check)
        self.btn_update.pack(side="right")

        # ==========================================
        #              2. Bottom Frame
        # ==========================================
        bottom_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", padx=10, pady=(5, 15))

        self.progress_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        self.progress_frame.pack(fill="x", pady=(0, 5))
        
        self.lbl_status = ctk.CTkLabel(self.progress_frame, text="")
        self.lbl_status.pack(side="top", anchor="w")
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, variable=self.progress_var, orientation="horizontal")
        
        action_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        action_frame.pack(fill="x")

        self.btn_preview = ctk.CTkButton(action_frame, text="Process and View",corner_radius=6, command=lambda: self.process(save=False), height=40)
        self.btn_preview.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.btn_save = ctk.CTkButton(action_frame, text="Save as...",corner_radius=6, command=lambda: self.process(save=True), height=40)
        self.btn_save.pack(side="right", fill="x", expand=True, padx=(5, 0))

        # ==========================================
        #               3. Tab View
        # ==========================================
        self.tabview = ctk.CTkTabview(self.root, fg_color="transparent")
        self.tabview.pack(side="top", fill="both", expand=True, padx=10, pady=5)

        tab_gen = self.tabview.add("General & Mask")
        tab_disp = self.tabview.add("Displacement")
        tab_color = self.tabview.add("Advanced (the cool stuff)")

        # ------------------------------------------
        #           TAB 1: General & Mask
        # ------------------------------------------
        # Info
        info_title_lbl = ctk.CTkLabel(tab_gen, text="Info", font=ctk.CTkFont(weight="bold"))
        info_title_lbl.pack(anchor="w", padx=5, pady=(5, 0))

        info_frame = ctk.CTkFrame(tab_gen, border_width=2, border_color="#555555", corner_radius=6)
        info_frame.pack(fill="x", pady=(0, 10))

        self.var_info_x = tk.StringVar(value="X: ")
        self.var_info_y = tk.StringVar(value="Y: ")

        self.lbl_info_x = ctk.CTkLabel(info_frame, textvariable=self.var_info_x)
        self.lbl_info_x.grid(row=0, column=0, padx=(15, 20), pady=8)
        self.lbl_info_y = ctk.CTkLabel(info_frame, textvariable=self.var_info_y)
        self.lbl_info_y.grid(row=0, column=1, padx=5, pady=8)

        # ROI
        roi_title_lbl = ctk.CTkLabel(tab_gen, text="Region of Interest (Area Mask)", font=ctk.CTkFont(weight="bold"))
        roi_title_lbl.pack(anchor="w", padx=5, pady=(5, 0))

        roi_frame = ctk.CTkFrame(tab_gen, border_width=2, border_color="#555555", corner_radius=6)
        roi_frame.pack(fill="x", pady=(0, 10))

        roi_frame.columnconfigure(1, weight=1)
        roi_frame.columnconfigure(4, weight=1)

        ctk.CTkLabel(roi_frame, text="Mode:").grid(row=0, column=0, sticky="e", padx=10, pady=(10, 5))
        self.var_roi_mode = tk.StringVar(value="none")
        ctk.CTkComboBox(roi_frame, variable=self.var_roi_mode, values=["none", "inside", "outside"], state="readonly", width=120).grid(row=0, column=1, sticky="w", pady=(10, 5))

        ctk.CTkLabel(roi_frame, text="X Pos:").grid(row=1, column=0, sticky="e", padx=10, pady=5)
        self.var_roi_x = tk.IntVar(value=0)
        self.slider_roi_x = ctk.CTkSlider(roi_frame, from_=0, to=100, variable=self.var_roi_x, command=lambda v: self.var_roi_x.set(int(float(v))))
        self.slider_roi_x.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        ctk.CTkEntry(roi_frame, textvariable=self.var_roi_x, width=60).grid(row=1, column=2, sticky="w", pady=5)

        ctk.CTkLabel(roi_frame, text="Y Pos:").grid(row=1, column=3, sticky="e", padx=10, pady=5)
        self.var_roi_y = tk.IntVar(value=0)
        self.slider_roi_y = ctk.CTkSlider(roi_frame, from_=0, to=100, variable=self.var_roi_y, command=lambda v: self.var_roi_y.set(int(float(v))))
        self.slider_roi_y.grid(row=1, column=4, sticky="ew", padx=5, pady=5)
        ctk.CTkEntry(roi_frame, textvariable=self.var_roi_y, width=60).grid(row=1, column=5, sticky="w", padx=10, pady=5)

        ctk.CTkLabel(roi_frame, text="Width").grid(row=2, column=0, sticky="e", padx=10, pady=(5, 10))
        self.var_roi_w = tk.StringVar(value="200")
        ctk.CTkEntry(roi_frame, textvariable=self.var_roi_w, width=60).grid(row=2, column=1, sticky="w", pady=(5, 10))

        ctk.CTkLabel(roi_frame, text="Height").grid(row=2, column=3, sticky="e", padx=10, pady=(5, 10))
        self.var_roi_h = tk.StringVar(value="200")
        ctk.CTkEntry(roi_frame, textvariable=self.var_roi_h, width=60).grid(row=2, column=4, sticky="w", pady=(5, 10))

        # Color Manipulation
        color_offset_title_lbl = ctk.CTkLabel(tab_gen, text="Color Manipulation", font=ctk.CTkFont(weight="bold"))
        color_offset_title_lbl.pack(anchor="w", padx=5, pady=(5, 0))

        color_frame = ctk.CTkFrame(tab_gen, border_width=2, border_color="#555555", corner_radius=6)
        color_frame.pack(fill="x", pady=(0, 10))

        color_frame.columnconfigure(1, weight=1)

        ctk.CTkLabel(color_frame, text="Color Offset:").grid(row=0, column=0, sticky="e", padx=10, pady=10)
        self.var_color_offset = tk.IntVar(value=0)
        ctk.CTkSlider(color_frame, from_=0, to=255, variable=self.var_color_offset, command=lambda v: self.var_color_offset.set(int(float(v)))).grid(row=0, column=1, sticky="ew", padx=10)
        ctk.CTkEntry(color_frame, textvariable=self.var_color_offset, width=50).grid(row=0, column=2, sticky="w", padx=10)

        # ------------------------------------------
        #             TAB 2: Displacement
        # ------------------------------------------
        # Row Shifting
        shift_title_lbl = ctk.CTkLabel(tab_disp, text="Row Shifting", font=ctk.CTkFont(weight="bold"))
        shift_title_lbl.pack(anchor="w", padx=5, pady=(5, 0))

        shift_frame = ctk.CTkFrame(tab_disp, border_width=2, border_color="#555555", corner_radius=6)
        shift_frame.pack(fill="x", pady=(0, 10))

        self.var_do_shift = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(shift_frame, text="Enable", variable=self.var_do_shift, checkbox_width=20, checkbox_height=20, corner_radius=6, border_width=2).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))
        ctk.CTkLabel(shift_frame, text="Probability (0.0-1.0):").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        
        self.var_probability = tk.DoubleVar(value=0.2)
        ctk.CTkEntry(shift_frame, textvariable=self.var_probability, width=60).grid(row=1, column=1, sticky="w", padx=5, pady=5)
        ctk.CTkLabel(shift_frame, text="Max Shift (px):").grid(row=2, column=0, sticky="w", padx=10, pady=(5, 10))
        
        self.var_shift = tk.IntVar(value=50)
        ctk.CTkEntry(shift_frame, textvariable=self.var_shift, width=60).grid(row=2, column=1, sticky="w", padx=5, pady=(5, 10))

        # Block Displacement
        title_displace_lbl = ctk.CTkLabel(tab_disp, text="Block Displacement", font=ctk.CTkFont(weight="bold"))
        title_displace_lbl.pack(anchor="w", padx=5, pady=(5, 0))

        displace_frame = ctk.CTkFrame(tab_disp, border_width=2, border_color="#555555", corner_radius=6)
        displace_frame.pack(fill="x", pady=(0, 10))

        displace_frame.columnconfigure(1, weight=1)
        
        self.var_fixed_mode = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(displace_frame, text="Fix Position (Video)", variable=self.var_fixed_mode, checkbox_width=20, checkbox_height=20, corner_radius=6, border_width=2).grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(displace_frame, text="Blocks:").grid(row=1, column=0, sticky="w", padx=10, pady=2)
        self.var_num_blocks = tk.IntVar(value=0)
        ctk.CTkSlider(displace_frame, from_=0, to=500, variable=self.var_num_blocks, command=lambda v: self.var_num_blocks.set(int(float(v)))).grid(row=1, column=1, sticky="ew", padx=5)
        ctk.CTkEntry(displace_frame, textvariable=self.var_num_blocks, width=40).grid(row=1, column=2, sticky="w", padx=(0, 10))
        
        ctk.CTkLabel(displace_frame, text="Min Size (px):").grid(row=2, column=0, sticky="w", padx=10, pady=2)
        self.var_min_block_size = tk.IntVar(value=0)
        ctk.CTkSlider(displace_frame, from_=0, to=500, variable=self.var_min_block_size, command=lambda v: self.var_min_block_size.set(int(float(v)))).grid(row=2, column=1, sticky="ew", padx=5)
        ctk.CTkEntry(displace_frame, textvariable=self.var_min_block_size, width=40).grid(row=2, column=2, sticky="w", padx=(0, 10))

        ctk.CTkLabel(displace_frame, text="Max Size (px):").grid(row=3, column=0, sticky="w", padx=10, pady=2)
        self.var_max_block_size = tk.IntVar(value=0)
        ctk.CTkSlider(displace_frame, from_=0, to=500, variable=self.var_max_block_size, command=lambda v: self.var_max_block_size.set(int(float(v)))).grid(row=3, column=1, sticky="ew", padx=5)
        ctk.CTkEntry(displace_frame, textvariable=self.var_max_block_size, width=40).grid(row=3, column=2, sticky="w", padx=(0, 10))
        
        ctk.CTkLabel(displace_frame, text="Max Shift (px):").grid(row=4, column=0, sticky="w", padx=10, pady=(2, 10))
        self.var_shift_amount = tk.IntVar(value=0)
        ctk.CTkSlider(displace_frame, from_=0, to=500, variable=self.var_shift_amount, command=lambda v: self.var_shift_amount.set(int(float(v)))).grid(row=4, column=1, sticky="ew", padx=5, pady=(0, 10))
        ctk.CTkEntry(displace_frame, textvariable=self.var_shift_amount, width=40).grid(row=4, column=2, sticky="w", padx=(0, 10), pady=(0, 10))

        # ------------------------------------------
        #      TAB 3: Advanced (the cool stuff)
        # ------------------------------------------
        # Chromatic Aberration
        aberration_title_lbl = ctk.CTkLabel(tab_color, text="Chromatic Aberration", font=ctk.CTkFont(weight="bold"))
        aberration_title_lbl.pack(anchor="w", padx=5, pady=(5, 0))
        
        aberration_frame = ctk.CTkFrame(tab_color, border_width=2, border_color="#555555", corner_radius=6)
        aberration_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(aberration_frame, text="Red Shift (px):").grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        self.var_red = tk.IntVar(value=0)
        ctk.CTkEntry(aberration_frame, textvariable=self.var_red, width=60).grid(row=0, column=1, sticky="w", pady=(10, 5))
        
        ctk.CTkLabel(aberration_frame, text="Green Shift (px):").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.var_green = tk.IntVar(value=0)
        ctk.CTkEntry(aberration_frame, textvariable=self.var_green, width=60).grid(row=1, column=1, sticky="w", pady=5)
        
        ctk.CTkLabel(aberration_frame, text="Blue Shift (px):").grid(row=2, column=0, sticky="w", padx=10, pady=(5, 10))
        self.var_blue = tk.IntVar(value=0)
        ctk.CTkEntry(aberration_frame, textvariable=self.var_blue, width=60).grid(row=2, column=1, sticky="w", pady=(5, 10))

        # Warping
        warp_title_lbl = ctk.CTkLabel(tab_color, text="Warping", font=ctk.CTkFont(weight="bold"))
        warp_title_lbl.pack(anchor="w", padx=5, pady=(5, 0))
        
        warp_frame = ctk.CTkFrame(tab_color, border_width=2, border_color="#555555", corner_radius=6)
        warp_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(warp_frame, text="Mode:").grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        self.var_warp_mode = tk.StringVar(value="none")
        ctk.CTkComboBox(warp_frame, variable=self.var_warp_mode, values=["none", "normal", "sin"], state="readonly", width=100).grid(row=0, column=1, sticky="w", pady=(10, 5))
        
        ctk.CTkLabel(warp_frame, text="Intensity:").grid(row=1, column=0, sticky="w", padx=10, pady=(5, 10))
        self.var_warp_val = tk.DoubleVar(value=0.0)
        ctk.CTkEntry(warp_frame, textvariable=self.var_warp_val, width=60).grid(row=1, column=1, sticky="w", pady=(5, 10))

        # Swapping & Sorting container
        bottom_color_container = ctk.CTkFrame(tab_color, fg_color="transparent")
        bottom_color_container.pack(fill="x")

        # Channel Swapping
        swap_container = ctk.CTkFrame(bottom_color_container, fg_color="transparent")
        swap_container.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        swap_title_lbl = ctk.CTkLabel(swap_container, text="Channel Swapping", font=ctk.CTkFont(weight="bold"))
        swap_title_lbl.pack(anchor="w", padx=5, pady=(0, 2))
        
        swapping_frame = ctk.CTkFrame(swap_container, border_width=2, border_color="#555555", corner_radius=6)
        swapping_frame.pack(fill="x")
        
        ctk.CTkLabel(swapping_frame, text="Mode:").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.var_channel_swapping_mode = tk.StringVar(value="none")
        ctk.CTkComboBox(swapping_frame, variable=self.var_channel_swapping_mode, values=["none", "RBG", "GRB", "GBR", "BRG", "BGR"], state="readonly", width=100).grid(row=0, column=1, sticky="w", padx=5, pady=10)

        # Pixel Sorting
        sort_container = ctk.CTkFrame(bottom_color_container, fg_color="transparent")
        sort_container.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        sort_title_lbl = ctk.CTkLabel(sort_container, text="Pixel Sorting", font=ctk.CTkFont(weight="bold"))
        sort_title_lbl.pack(anchor="w", padx=5, pady=(0, 2))
        
        sorting_frame = ctk.CTkFrame(sort_container, border_width=2, border_color="#555555", corner_radius=6)
        sorting_frame.pack(fill="x")
        
        ctk.CTkLabel(sorting_frame, text="Mode:").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.var_sort_mode = tk.StringVar(value="none")
        ctk.CTkComboBox(sorting_frame, variable=self.var_sort_mode, values=["none", "lum", "hue"], state="readonly", width=100).grid(row=0, column=1, sticky="w", padx=5, pady=10)

    def start_update_check(self):
        self.btn_update.configure(state="disabled", text="Checking...")
        threading.Thread(target=self.check_for_updates, daemon=True).start()
        self.root.after(100, self.process_update_queue)

    def check_for_updates(self):
        api_url = f"https://api.github.com/repos/{self.repo_url}/releases/latest"
        
        try:
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            context = ssl.create_default_context(cafile=certifi.where())

            with urllib.request.urlopen(req, timeout=5, context=context) as response:
                data = json.loads(response.read().decode())
                
            latest_version = data.get("tag_name", "")
            release_url = data.get("html_url", "")
            
            self.update_queue.put({"status": "success", "version": latest_version, "url": release_url})
            
        except Exception as e:
            self.update_queue.put({"status": "error", "message": str(e)})

    def process_update_queue(self):
        try:
            result = self.update_queue.get_nowait()
            
            self.btn_update.configure(state="normal", text="Check for Updates")
            
            if result["status"] == "success":
                latest_version = result["version"]
                release_url = result["url"]
                
                if latest_version > self.version:
                    msg = f"A new version is available! ({latest_version})\n\nYou are currently using {self.version}.\nWould you like to download the update?"
                    if messagebox.askyesno("Update Available", msg):
                        webbrowser.open(release_url)
                else:
                    messagebox.showinfo("Up to date", f"You are using the latest version ({self.version}).")
                    
            elif result["status"] == "error":
                messagebox.showerror("Update Error", f"Could not check for updates.\n\nError: {result['message']}")
                
        except queue.Empty:
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
            self.lbl_file.configure(text=os.path.basename(filepath))
            ext = os.path.splitext(filepath)[1].lower()
        
            try:
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

                self.slider_roi_x.configure(to=max(0, w-1))
                self.slider_roi_y.configure(to=max(0, h-1))

                self.var_roi_x.set(0)
                self.var_roi_y.set(0)

            except Exception as e:
                messagebox.showerror("Error", f"Failed to read image dimensions:\n{str(e)}")

    def process_video_render(self, input_path, save_path, config):
        self.stop_processing = False
        reader = imageio.get_reader(input_path)
        meta = reader.get_meta_data()
        fps = meta["fps"]
        
        try:
            total_frames = reader.count_frames()
        except:
            total_frames = int(meta.get("duration", 0) * fps) 
            if total_frames <= 0: total_frames = 100 

        writer = imageio.get_writer(save_path, fps=fps, codec="libx264", macro_block_size=None)

        self.progress_bar.pack(fill="x", expand=True, pady=5)
        self.btn_preview.configure(state="disabled")
        self.btn_save.configure(text="Stop", fg_color="red", hover_color="#8B1A1A")

        frame_count = 0
        for frame in reader:
            if self.stop_processing:
                self.btn_save.configure(state="disabled")
                break
            else:
                frame_count += 1
                
                data = np.array(frame, dtype=np.int32)
                data = apply_effects(data, config)
                
                final_data = (data % 256).astype(np.uint8)
                writer.append_data(final_data)

                if total_frames > 0:
                    progress = min((frame_count / total_frames), 1.0)
                    self.progress_bar.set(progress)
                    self.lbl_status.configure(text=f"Rendering video... {frame_count} / {total_frames} frames")
                else:
                    self.lbl_status.configure(text=f"Rendering video... {frame_count} frames") 
            self.root.update()

        reader.close()
        writer.close()
            
        self.progress_bar.pack_forget()
        self.lbl_status.configure(text="")
        self.btn_preview.configure(state="normal")
        self.btn_save.configure(text="Save as", fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"], hover_color=ctk.ThemeManager.theme["CTkButton"]["hover_color"], state="normal")
        self.progress_var.set(0)

        if self.stop_processing:
            try:
                os.remove(save_path)
            except Exception as e:
                print(f"Could not remove file: {e}")
            messagebox.showinfo("Stopped", f"Video rendering stopped.")
        else:
            messagebox.showinfo("Success", f"Video successfully saved:\n{save_path}")

    def process(self, save=False):
        if self.btn_save.cget("text") == "Stop":
            self.stop_processing = True
            return

        if not self.image_path:
            messagebox.showwarning("Notice", "Please upload a file first!")
            return
 
        if self.var_min_block_size.get() > self.var_max_block_size.get():
            messagebox.showerror("Error", "Min Size cannot be larger than Max Size!")
            return

        try:
            roi_w = int(self.var_roi_w.get()) if self.var_roi_w.get() else 200
            roi_h = int(self.var_roi_h.get()) if self.var_roi_h.get() else 200
        except ValueError:
            roi_w, ad_h = 200, 200

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
            "min_block_size": self.var_min_block_size.get(), 
            "max_block_size": self.var_max_block_size.get(),
            "shift_amount": self.var_shift_amount.get(),
            "fixed_mode":self.var_fixed_mode.get()
        }

        ext = os.path.splitext(self.image_path)[1].lower()
        is_video = ext in self.video_exts

        try:
            if is_video:
                if save:
                    save_path = filedialog.asksaveasfilename(
                        defaultextension=".mp4", 
                        filetypes=[("MP4 Video", "*.mp4")]
                    )
                    if save_path:
                        self.process_video_render(self.image_path, save_path, config)
                else:
                    self.lbl_status.configure(text="Generating frame preview...")
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
                    
                    self.lbl_status.configure(text="")

            else:
                self.lbl_status.configure(text="Processing image...")
                self.root.update()

                imgin = Image.open(self.image_path)
                imgin.load()
                data = np.asarray(imgin, dtype="int32")

                data = apply_effects(data, config)

                final_data = (data % 256).astype(np.uint8)
                imgout = Image.fromarray(final_data, "RGB")

                self.lbl_status.configure(text="")

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
            self.lbl_status.configure(text="")
            self.progress_bar.pack_forget()
            self.btn_preview.configure(state="normal")
            self.btn_save.configure(state="normal")
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    root = ctk.CTk()
    app = databender(root)
    root.mainloop()