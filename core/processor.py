from core.filters import *

def apply_effects(data, config):
    img_h, img_w = data.shape[:2]
    roi_mode = config.get("roi_mode", "none")
    target_data = data.copy()
    original_roi = None
    rx, ry, rw, rh = 0, 0, img_w, img_h

    # cutting the ROI
    if roi_mode in ["inside", "outside"]:
        rx = config.get("roi_x", 0)
        ry = config.get("roi_y", 0)
        rw = config.get("roi_w", img_w)
        rh = config.get("roi_h", img_h)

        rw = max(1, min(rw, img_w - rx))
        rh = max(1, min(rh, img_h - ry))

        if roi_mode == "outside":
            original_roi = data[ry:ry+rh, rx:rx+rw].copy()
        elif roi_mode == "inside":
            target_data = data[ry:ry+rh, rx:rx+rw].copy()

    # applying flipping
    if config.get("h_flip", False):
        target_data = h_flip(target_data)
    if config.get("v_flip", False):
        target_data = v_flip(target_data)

    # applying pixel sort
    sort_mode = config.get("sort_mode", "none")
    if sort_mode == "lum":
        target_data = sort_pixels(target_data, lambda pixels: np.average(pixels, axis=2) / 255, lambda lum: (lum > 2 / 6) & (lum < 4 / 6), 1)
    elif sort_mode == "hue":
        target_data = sort_pixels(target_data, hue, lambda h: (h > 2 / 6) & (h < 4 / 6), 1)

    # applying color offset
    offset = config.get("color_offset", 0)
    target_data = color_offset(target_data, offset)
    
    # applying row shifting
    if config.get("do_shift", False):
        target_data = row_shifting(target_data, config.get("shift_prob", 0), config.get("shift_max", 50))

    # applying chromatic aberration
    target_data = chromatic_aberration(target_data, config.get("red", 0), config.get("green", 0), config.get("blue", 0))    
    
    # applying channel swap
    target_data = channel_swapping(target_data, config.get("cswap_mode"))

    # applying warp
    warp_mode = config.get("warp_mode", "none")
    if warp_mode != "none":
        target_data = warp(target_data, warp_mode, config.get("warp_val", 0.0))

    # applying block displacement
    if config.get("do_blocks", False):
        target_data = block_displacement(target_data, config.get("num_blocks", 0), config.get("min_block_size", 0), config.get("max_block_size",0), config.get("shift_amount",0), config.get("fixed_mode", False))

    # applying pixelation
    pixel_amount = config.get("pixelation_amount", 0)
    if pixel_amount > 1:
        target_data = pixelation(target_data, pixel_amount)

    # applying xor glitch
    xor_value = config.get("xor_glitch_value", 0)
    if xor_value > 0:
        target_data = xor_glitch(target_data, xor_value)

    # applying jpeg compression
    comp_value = config.get("compression_amount", 0)
    if comp_value > 0:
        target_data = jpeg_compression(target_data, comp_value)

    # placing the ROI back
    if roi_mode == "inside":
        data[ry:ry+rh, rx:rx+rw] = target_data
    elif roi_mode == "outside":
        target_data[ry:ry+rh, rx:rx+rw] = original_roi
        data = target_data
    else:
        data = target_data

    return data