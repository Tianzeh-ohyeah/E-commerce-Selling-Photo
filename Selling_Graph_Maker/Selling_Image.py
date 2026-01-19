import os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageColor, ImageFilter

# ---------------------------------------------------------
# 1. 图像处理工具函数
# ---------------------------------------------------------

def local_remove_bg(pil_img):
    cv_img = cv2.cvtColor(np.array(pil_img.convert('RGBA')), cv2.COLOR_RGBA2BGRA)
    gray = cv2.cvtColor(cv_img[:, :, :3], cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 252, 255, cv2.THRESH_BINARY_INV) # 提高阈值保留更多细节
    
    kernel = np.ones((3,3), np.uint8)
    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.GaussianBlur(mask, (3,3), 0)
    cv_img[:, :, 3] = mask
    return Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGRA2RGBA))

def advanced_recolor(image, color_mapping_list):
    """
    改进版背景变色：使用渐变因子代替硬遮罩，保留展台细节
    """
    img_rgba = image.convert('RGBA')
    img_np = np.array(img_rgba).astype(np.float32)
    H, W = img_np.shape[:2]
    
    # --- 核心改进：创建平滑渐变系数 ---
    # 0.0 表示完全保留原图（展台），1.0 表示完全应用新颜色（背景）
    gradient_mask = np.ones((H, W), dtype=np.float32)
    for y in range(H):
        if y > H * 0.6:  # 从60%高度开始向展台过渡
            # 在底部区域，保留约85%的原图细节，只渗入15%的新色调
            factor = 1.0 - ((y - H * 0.6) / (H * 0.4))
            gradient_mask[y, :] = max(0.15, factor)

    result_rgb = img_np[:, :, :3].copy()

    for (old_rgb, new_hex) in color_mapping_list:
        if new_hex.lower() == "placeholder": continue
        target_rgb = np.array(ImageColor.getrgb(new_hex), dtype=np.float32)
        
        for c in range(3):
            # 基于渐变系数进行颜色混合
            diff = (target_rgb[c] - result_rgb[:, :, c])
            result_rgb[:, :, c] += diff * gradient_mask

    result_rgb = np.clip(result_rgb, 0, 255).astype(np.uint8)
    img_np[:, :, :3] = result_rgb
    
    return Image.fromarray(img_np.astype(np.uint8)), None

# ---------------------------------------------------------
# 2. 居中与阴影合成核心逻辑
# ---------------------------------------------------------

def apply_product_to_center(canvas, product_img, center_ratio=(0.5, 0.75), scale_ratio=0.35):
    """
    基于你提供的逻辑：精准放置、双层阴影、且根据 skus_scale 调整大小
    """
    cw, ch = canvas.size
    
    # --- 缩放逻辑改进：读取 skus_scale 让产品变大 ---
    target_h = int(ch * scale_ratio)
    pw, ph = product_img.size
    zoom_factor = target_h / ph
    product_img = product_img.resize((int(pw * zoom_factor), target_h), Image.Resampling.LANCZOS)
    pw, ph = product_img.size

    # 动态限制最大宽度
    max_w = int(cw * 0.55) 
    if pw > max_w:
        ratio = max_w / pw
        product_img = product_img.resize((max_w, int(ph * ratio)), Image.Resampling.LANCZOS)
        pw, ph = product_img.size

    tx = int(cw * center_ratio[0]) - (pw // 2)
    ty = int(ch * center_ratio[1]) - ph # 底部对齐展台中心
    
    # --- 双层阴影层次感 ---
    # 1. 落地大阴影 (Soft Shadow)
    drop_shadow = Image.new("RGBA", (int(pw*1.4), 40), (0, 0, 0, 0))
    ds_draw = ImageDraw.Draw(drop_shadow)
    ds_draw.ellipse([10, 10, pw*1.4-10, 30], fill=(0, 0, 0, 50)) 
    drop_shadow = drop_shadow.filter(ImageFilter.GaussianBlur(10))
    
    # 2. 接触阴影 (AO Shadow)
    ao_shadow = Image.new("RGBA", (pw, 20), (0, 0, 0, 0))
    ao_draw = ImageDraw.Draw(ao_shadow)
    ao_draw.ellipse([pw*0.05, 5, pw*0.95, 15], fill=(0, 0, 0, 150)) 
    ao_shadow = ao_shadow.filter(ImageFilter.GaussianBlur(3))
    
    # 合成顺序：背景 -> 落地影 -> 接触影 -> 产品
    canvas.alpha_composite(drop_shadow, dest=(tx - int(pw*0.2), ty + ph - 25))
    canvas.alpha_composite(ao_shadow, dest=(tx, ty + ph - 12))
    canvas.alpha_composite(product_img, dest=(tx, ty))

    return canvas

# ---------------------------------------------------------
# 3. 处理主流程
# ---------------------------------------------------------

def process_event(event_name, events_root, bg_path):
    event_dir = os.path.join(events_root, event_name)
    cfg_path = os.path.join(event_dir, "config.txt")
    if not os.path.exists(cfg_path): return
    
    cfg = {}
    with open(cfg_path, 'r', encoding='utf-8') as f:
        for l in f:
            if ':' in l:
                k, v = l.strip().split(':', 1)
                cfg[k.strip()] = v.strip()

    original_bg = Image.open(bg_path).convert("RGBA")
    # 高清 resize
    target_h = 1080
    bg_ratio = target_h / original_bg.size[1]
    original_bg = original_bg.resize((int(original_bg.size[0] * bg_ratio), target_h), Image.Resampling.BICUBIC)
    
    # 颜色配置
    color_map = []
    for k, v in cfg.items():
        if k.startswith("color_map_"):
            rgb_str, hex_val = v.split(':')
            color_map.append((tuple(map(int, rgb_str.strip().split(','))), hex_val.strip()))
    
    # 变色处理 (现在是平滑变色)
    recolored_bg, _ = advanced_recolor(original_bg, color_map)
    W, H = recolored_bg.size

    skus_root = os.path.join(event_dir, "skus")
    categories = [d for d in os.listdir(skus_root) if os.path.isdir(os.path.join(skus_root, d))]

    for cat in categories:
        cat_path = os.path.join(skus_root, cat)
        for img_name in os.listdir(cat_path):
            if not img_name.lower().endswith(('.png', '.jpg', '.jpeg')): continue
            
            canvas = recolored_bg.copy()
            p_img = Image.open(os.path.join(cat_path, img_name)).convert("RGBA")
            p_img = local_remove_bg(p_img)
            
            # 使用整合了双层阴影的逻辑
            canvas = apply_product_to_center(canvas, p_img, center_ratio=(0.5, 0.78))
            
            # --- 标题与副标题动态处理 ---
            draw = ImageDraw.Draw(canvas)
            text_color = cfg.get("text_color", "white") # 获取配置颜色，默认为白色
            
            for prefix in ["main_title", "sub_title"]:
                content = cfg.get(prefix, "")
                if not content: continue
                
                # 从 config 获取尺寸和位置（比例转像素）
                # 如果获取不到，设置一个合理的默认值
                size_ratio = float(cfg.get(f"{prefix}_size", "0.05"))
                pos_str = cfg.get(f"{prefix}_pos", "0.5, 0.1")
                
                font_size = int(H * size_ratio)
                pos_x_ratio, pos_y_ratio = map(float, pos_str.split(','))
                
                tx, ty = int(W * pos_x_ratio), int(H * pos_y_ratio)

                try: 
                    font = ImageFont.truetype("msyh.ttc", font_size)
                except: 
                    font = ImageFont.load_default()
                
                # 绘制文字：使用你 config 里的位置坐标
                draw.text((tx, ty), content, font=font, fill=text_color)

            # --- 保存 ---
            out_dir = os.path.join(os.path.dirname(events_root), "output", event_name, cat)
            os.makedirs(out_dir, exist_ok=True)
            canvas.convert("RGB").save(os.path.join(out_dir, img_name), quality=95)

def main():
    root = os.path.dirname(os.path.abspath(__file__))
    events_root = os.path.join(root, "events")
    bg_path = os.path.join(events_root, "background.jpg")
    
    for item in os.listdir(events_root):
        if os.path.isdir(os.path.join(events_root, item)) and item != "output":
            print(f"🚀 处理活动: {item}")
            process_event(item, events_root, bg_path)

if __name__ == "__main__":
    main()