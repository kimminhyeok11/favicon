from flask import Flask, request, send_file, send_from_directory
from PIL import Image, ImageDraw, ImageFont
import io
import random
import os

app = Flask(__name__)

def random_color():
    return tuple(random.randint(0, 255) for _ in range(3)) + (255,)

def random_font(size, font_candidates=None):
    font_dir = os.path.join(os.path.dirname(__file__), "fonts")
    if font_candidates is None:
        font_candidates = []
        for fname in os.listdir(font_dir):
            if fname.lower().endswith(('.ttf', '.otf')):
                font_candidates.append(os.path.join(font_dir, fname))
    if not font_candidates:
        return ImageFont.load_default()
    font_path = random.choice(font_candidates)
    try:
        return ImageFont.truetype(font_path, size)
    except:
        return ImageFont.load_default()

def get_max_fontsize(text, img_size, font_candidates, stroke_width):
    min_size = 10
    max_size = img_size
    best_size = min_size
    while min_size <= max_size:
        mid = (min_size + max_size) // 2
        font = random_font(mid, font_candidates)
        dummy_img = Image.new('L', (img_size, img_size))
        draw = ImageDraw.Draw(dummy_img)
        bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        if w <= img_size * 0.95 and h <= img_size * 0.95:
            best_size = mid
            min_size = mid + 1
        else:
            max_size = mid - 1
    return best_size

def draw_gradient(draw, width, height, color1, color2, horizontal=False):
    for i in range(width if horizontal else height):
        ratio = i / (width-1 if horizontal else height-1)
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        a = int(color1[3] * (1 - ratio) + color2[3] * ratio)
        if horizontal:
            draw.line([(i, 0), (i, height)], fill=(r, g, b, a))
        else:
            draw.line([(0, i), (width, i)], fill=(r, g, b, a))

@app.route('/')
def root():
    return send_from_directory('.', 'index.html')

# 예쁜 색상 팔레트 (Material Design 기반)
PALETTES = [
    [(244, 67, 54), (233, 30, 99), (156, 39, 176), (103, 58, 183), (33, 150, 243)],
    [(0, 188, 212), (0, 150, 136), (76, 175, 80), (255, 235, 59), (255, 152, 0)],
    [(121, 85, 72), (158, 158, 158), (96, 125, 139), (255, 87, 34), (205, 220, 57)]
]

# 더 다양한 세련된 팔레트 (Flat UI, Material 등)
PALETTES = [
    [(52, 152, 219), (41, 128, 185), (155, 89, 182), (52, 73, 94), (241, 196, 15), (230, 126, 34), (231, 76, 60)],
    [(26, 188, 156), (22, 160, 133), (39, 174, 96), (142, 68, 173), (243, 156, 18), (211, 84, 0), (192, 57, 43)],
    [(236, 240, 241), (149, 165, 166), (127, 140, 141), (44, 62, 80), (52, 73, 94), (241, 196, 15), (46, 204, 113)],
    [(255, 99, 132), (54, 162, 235), (255, 206, 86), (75, 192, 192), (153, 102, 255), (255, 159, 64)],
    [(33, 150, 243), (156, 39, 176), (233, 30, 99), (255, 193, 7), (76, 175, 80), (255, 87, 34), (205, 220, 57)]
]

def pick_palette():
    palette = random.choice(PALETTES)
    # RGBA 변환
    return [tuple(list(rgb) + [255]) for rgb in palette]

def get_contrasting_color(bg_color, palette):
    # 배경과 가장 대비가 큰 색상 선택 (YIQ 공식)
    def yiq(rgb):
        return (299 * rgb[0] + 587 * rgb[1] + 114 * rgb[2]) / 1000
    bg_yiq = yiq(bg_color)
    return max(palette, key=lambda c: abs(yiq(c) - bg_yiq))

@app.route('/favicon')
def favicon():
    text = request.args.get('text', 'FAVICON')
    chars = [c for c in text if not c.isspace()]
    n_chars = random.randint(1, min(5, len(chars))) if chars else 2
    selected_chars = random.sample(chars, n_chars) if chars else ['?', '?']
    selected = ''.join(selected_chars)

    img_size = 128
    img = Image.new('RGBA', (img_size, img_size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # 팔레트, 배경, 폰트 후보, stroke 등 기존 코드 유지
    palette = pick_palette()
    bg_color = random.choice(palette)
    palette_for_text = [c for c in palette if c != bg_color]
    if not palette_for_text:
        palette_for_text = palette

    if random.choice([True, False]):
        color1 = bg_color
        color2 = random.choice(palette_for_text)
        horizontal = random.choice([True, False])
        draw_gradient(draw, img_size, img_size, color1, color2, horizontal)
        bg_for_contrast = color1
    else:
        draw.rectangle([0, 0, img_size, img_size], fill=bg_color)
        bg_for_contrast = bg_color

    font_dir = os.path.join(os.path.dirname(__file__), "fonts")
    font_candidates = [os.path.join(font_dir, fname) for fname in os.listdir(font_dir) if fname.lower().endswith(('.ttf', '.otf'))]

    # 폰트 크기 미리 계산 (그리드/한줄 모두 적용)
    n = len(selected_chars)
    if n <= 3:
        font_size = get_max_fontsize(selected, img_size, font_candidates, 0)
    else:
        if n <= 4:
            rows, cols = 2, 2
        elif n <= 6:
            rows, cols = 2, 3
        else:
            rows, cols = 3, 3
        cell_w = img_size / cols
        cell_h = img_size / rows
        font_size = int(min(cell_w, cell_h) * 0.8)

    # 테두리 두께를 폰트 크기의 1/8 이하, 최대 3픽셀로 제한
    max_stroke = max(1, min(3, font_size // 8))
    stroke_width = random.randint(1, max_stroke) if random.choice([True, False]) else 0
    stroke_color = get_contrasting_color(bg_for_contrast, palette_for_text) if stroke_width else None

    font = random_font(font_size, font_candidates)

    if n <= 3:
        # 기존 중앙 한 줄
        bbox = draw.textbbox((0, 0), selected, font=font, stroke_width=stroke_width)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = (img_size - w) / 2 - bbox[0]
        y = (img_size - h) / 2 - bbox[1]
        char_x = x
        for i, c in enumerate(selected):
            candidates = [col for col in palette_for_text if abs(col[0]-bg_for_contrast[0])+abs(col[1]-bg_for_contrast[1])+abs(col[2]-bg_for_contrast[2]) > 80]
            if not candidates:
                candidates = palette_for_text
            char_color = random.choice(candidates)
            draw.text((char_x, y), c, font=font, fill=char_color, stroke_width=stroke_width, stroke_fill=stroke_color)
            char_x += draw.textlength(c, font=font)
    else:
        # 네모칸(그리드) 정렬
        if n <= 4:
            rows, cols = 2, 2
        elif n <= 6:
            rows, cols = 2, 3
        else:
            rows, cols = 3, 3
        cell_w = img_size / cols
        cell_h = img_size / rows
        for idx, c in enumerate(selected_chars):
            row = idx // cols
            col = idx % cols
            bbox = draw.textbbox((0, 0), c, font=font, stroke_width=stroke_width)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            cx = col * cell_w + (cell_w - w) / 2 - bbox[0]
            cy = row * cell_h + (cell_h - h) / 2 - bbox[1]
            candidates = [colr for colr in palette_for_text if abs(colr[0]-bg_for_contrast[0])+abs(colr[1]-bg_for_contrast[1])+abs(colr[2]-bg_for_contrast[2]) > 80]
            if not candidates:
                candidates = palette_for_text
            char_color = random.choice(candidates)
            draw.text((cx, cy), c, font=font, fill=char_color, stroke_width=stroke_width, stroke_fill=stroke_color)

    # 랜덤 이미지 테두리(프레임)
    use_img_border = random.choice([True, False])
    if use_img_border:
        border_width = random.randint(3, 10)
        border_color = get_contrasting_color(bg_for_contrast, palette_for_text)
        for i in range(border_width):
            draw.rectangle([i, i, img_size-1-i, img_size-1-i], outline=border_color)

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@app.route('/favicon.ico')
def favicon_ico():
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)