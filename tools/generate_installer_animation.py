# -*- coding: utf-8 -*-
"""生成“文件管家”安装过程循环动画。

输出：
  assets/installer/file-manager-installation.mp4
  assets/installer/file-manager-installation-preview.gif
  assets/installer/file-manager-installation-poster.png

MP4 需要 ffmpeg；脚本会优先使用 imageio-ffmpeg 提供的可执行文件。
"""
from __future__ import annotations

import math
import os
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


PROJECT_DIR = Path(__file__).resolve().parent.parent
ASSET_DIR = PROJECT_DIR / "assets"
OUTPUT_DIR = ASSET_DIR / "installer"
FRAME_DIR = OUTPUT_DIR / "frames"

WIDTH, HEIGHT = 1280, 720
FPS = 30
DURATION = 6
FRAME_COUNT = FPS * DURATION
INSTALLER_FRAME_COUNT = 60
INSTALLER_FRAME_SIZE = (720, 405)

BG = (247, 249, 252)
INK = (25, 44, 72)
MUTED = (121, 139, 165)
BLUE = (74, 144, 226)
BLUE_LIGHT = (103, 169, 244)
BLUE_PALE = (230, 240, 253)
ORANGE = (255, 107, 53)
GOLD = (255, 209, 0)
WHITE = (255, 255, 255)


def font(size: int, bold: bool = False):
    candidates = [
        Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" /
        ("msyhbd.ttc" if bold else "msyh.ttc"),
        Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" /
        ("segoeuib.ttf" if bold else "segoeui.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


FONT_TITLE = font(26, True)
FONT_STATUS = font(22, False)
FONT_SMALL = font(15, False)


def rounded_shadow(base: Image.Image, box, radius=24, blur=24, offset=(0, 12), alpha=35):
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    x1, y1, x2, y2 = box
    ox, oy = offset
    draw.rounded_rectangle((x1 + ox, y1 + oy, x2 + ox, y2 + oy), radius,
                           fill=(38, 72, 120, alpha))
    base.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(blur)))


def draw_file_card(draw: ImageDraw.ImageDraw, box, active: float, index: int):
    x1, y1, x2, y2 = box
    active = max(0.0, min(1.0, active))
    fill = tuple(round(WHITE[i] * (1 - active) + BLUE_PALE[i] * active)
                 for i in range(3)) + (245,)
    outline = tuple(round((218, 227, 240)[i] * (1 - active) + BLUE_LIGHT[i] * active)
                    for i in range(3)) + (220,)
    draw.rounded_rectangle(box, 14, fill=fill, outline=outline, width=2)

    icon_x, icon_y = x1 + 18, y1 + 15
    icon_color = tuple(round((152, 174, 203)[i] * (1 - active) + BLUE[i] * active)
                       for i in range(3)) + (255,)
    draw.rounded_rectangle((icon_x, icon_y, icon_x + 26, icon_y + 32), 5,
                           fill=icon_color)
    draw.polygon([(icon_x + 18, icon_y), (icon_x + 26, icon_y + 8),
                  (icon_x + 18, icon_y + 8)], fill=(220, 237, 255, 255))
    line_color = (137, 158, 187, 210)
    widths = [72, 94, 58]
    for row, width in enumerate(widths):
        y = icon_y + 4 + row * 10
        draw.rounded_rectangle((icon_x + 42, y, icon_x + 42 + width, y + 4),
                               2, fill=line_color)
    dot_color = GOLD if index % 3 == 0 else BLUE_LIGHT
    draw.ellipse((x2 - 28, y1 + 24, x2 - 18, y1 + 34), fill=dot_color + (230,))


def lens_position(frame_index: int):
    # 闭合的双波扫描路径，第一帧和最后一帧自然衔接。
    phase = 2 * math.pi * frame_index / FRAME_COUNT
    x = 640 + 305 * math.cos(phase)
    y = 365 + 105 * math.sin(phase * 2)
    return x, y, phase


def render_frame(frame_index: int):
    image = Image.new("RGBA", (WIDTH, HEIGHT), BG + (255,))
    draw = ImageDraw.Draw(image, "RGBA")

    # 背景只保留很淡的品牌光晕。
    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow, "RGBA")
    glow_draw.ellipse((250, 30, 1030, 810), fill=BLUE_LIGHT + (18,))
    image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(90)))
    draw = ImageDraw.Draw(image, "RGBA")

    # 顶部品牌。
    icon = Image.open(ASSET_DIR / "filecare-256.png").convert("RGBA")
    icon.thumbnail((46, 46), Image.Resampling.LANCZOS)
    image.alpha_composite(icon, (70, 48))
    draw.text((128, 55), "文件管家", font=FONT_TITLE, fill=INK + (255,))

    # 主文件夹面板。
    panel = (230, 150, 1050, 550)
    rounded_shadow(image, panel, radius=36, blur=28, offset=(0, 15), alpha=28)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rounded_rectangle(panel, 36, fill=(250, 252, 255, 250),
                           outline=(220, 231, 246, 255), width=2)

    # 文件夹顶部轮廓。
    draw.rounded_rectangle((278, 125, 544, 190), 25, fill=BLUE + (235,))
    draw.rounded_rectangle((260, 172, 1020, 520), 32,
                           fill=(235, 243, 253, 245),
                           outline=BLUE_LIGHT + (210,), width=3)

    card_boxes = []
    for row in range(3):
        for col in range(2):
            x = 315 + col * 345
            y = 228 + row * 84
            card_boxes.append((x, y, x + 295, y + 66))

    lens_x, lens_y, phase = lens_position(frame_index)
    for index, box in enumerate(card_boxes):
        cx = (box[0] + box[2]) / 2
        cy = (box[1] + box[3]) / 2
        distance = math.hypot(cx - lens_x, cy - lens_y)
        active = max(0.0, 1.0 - distance / 230.0)
        draw_file_card(draw, box, active, index)

    # 镜头扫描光晕。
    lens_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    lens_draw = ImageDraw.Draw(lens_layer, "RGBA")
    radius = 69 + 3 * math.sin(phase * 3)
    for extra, alpha in ((34, 10), (22, 18), (10, 30)):
        lens_draw.ellipse((lens_x - radius - extra, lens_y - radius - extra,
                           lens_x + radius + extra, lens_y + radius + extra),
                          fill=BLUE_LIGHT + (alpha,))
    lens_layer = lens_layer.filter(ImageFilter.GaussianBlur(10))
    image.alpha_composite(lens_layer)
    draw = ImageDraw.Draw(image, "RGBA")

    # 放大镜本体。
    draw.ellipse((lens_x - radius, lens_y - radius,
                  lens_x + radius, lens_y + radius),
                 fill=(255, 255, 255, 72), outline=ORANGE + (255,), width=14)
    handle_angle = math.radians(44)
    hx1 = lens_x + math.cos(handle_angle) * (radius - 2)
    hy1 = lens_y + math.sin(handle_angle) * (radius - 2)
    hx2 = lens_x + math.cos(handle_angle) * (radius + 64)
    hy2 = lens_y + math.sin(handle_angle) * (radius + 64)
    draw.line((hx1, hy1, hx2, hy2), fill=ORANGE + (255,), width=18)
    draw.ellipse((hx2 - 9, hy2 - 9, hx2 + 9, hy2 + 9), fill=ORANGE + (255,))

    # 金色扫描星点，位置与镜头同步，强度柔和。
    for offset, scale in ((-1.1, 1.0), (0.2, 0.7), (1.4, 0.45)):
        sparkle_phase = phase * 2 + offset
        sx = lens_x - 78 + math.cos(sparkle_phase) * 20
        sy = lens_y - 70 + math.sin(sparkle_phase) * 16
        rr = (5 + 3 * (0.5 + 0.5 * math.sin(sparkle_phase * 2))) * scale
        draw.ellipse((sx - rr, sy - rr, sx + rr, sy + rr), fill=GOLD + (235,))

    # 底部状态文字与循环点，不伪造安装进度。
    status = "正在准备文件…"
    bbox = draw.textbbox((0, 0), status, font=FONT_STATUS)
    text_x = (WIDTH - (bbox[2] - bbox[0])) / 2
    draw.text((text_x, 600), status, font=FONT_STATUS, fill=INK + (235,))
    active_dot = int((frame_index / FPS) * 2) % 3
    for i in range(3):
        color = BLUE if i == active_dot else (205, 216, 230)
        draw.ellipse((613 + i * 26, 650, 623 + i * 26, 660), fill=color + (255,))

    return image.convert("RGB")


def find_ffmpeg():
    executable = shutil.which("ffmpeg")
    if executable:
        return executable
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:
        raise RuntimeError(
            "未找到 ffmpeg。请安装 imageio-ffmpeg 后重试。") from exc


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FRAME_DIR.mkdir(parents=True, exist_ok=True)
    mp4_path = OUTPUT_DIR / "file-manager-installation.mp4"
    gif_path = OUTPUT_DIR / "file-manager-installation-preview.gif"
    poster_path = OUTPUT_DIR / "file-manager-installation-poster.png"

    ffmpeg = find_ffmpeg()
    command = [
        str(ffmpeg), "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{WIDTH}x{HEIGHT}", "-r", str(FPS), "-i", "-",
        "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(mp4_path),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    gif_frames = []
    installer_frames = []
    poster = None
    try:
        for frame_index in range(FRAME_COUNT):
            frame = render_frame(frame_index)
            process.stdin.write(frame.tobytes())
            if frame_index == FRAME_COUNT // 8:
                poster = frame.copy()
            if frame_index % 2 == 0:
                gif_frames.append(frame.resize((960, 540), Image.Resampling.LANCZOS))
            if frame_index % (FRAME_COUNT // INSTALLER_FRAME_COUNT) == 0:
                installer_frames.append(
                    frame.resize(INSTALLER_FRAME_SIZE, Image.Resampling.LANCZOS))
    finally:
        if process.stdin:
            process.stdin.close()
    return_code = process.wait()
    if return_code != 0:
        raise RuntimeError(f"ffmpeg 退出码：{return_code}")

    if poster is not None:
        poster.save(poster_path, optimize=True)
    gif_frames[0].save(
        gif_path, save_all=True, append_images=gif_frames[1:],
        duration=round(2000 / FPS), loop=0, optimize=False,
    )
    for index, frame in enumerate(installer_frames):
        frame.save(FRAME_DIR / f"installer-frame-{index:03d}.png", optimize=True)
    print(mp4_path)
    print(gif_path)
    print(poster_path)
    print(f"{len(installer_frames)} installer frames -> {FRAME_DIR}")


if __name__ == "__main__":
    main()
