import io
import os
import tempfile
import datetime
import docx
from docx import Document
from docx.shared import Inches
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import streamlit as st

# Rembg AI Background removal import check
try:
    from rembg import remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

# OpenCV check for Face AI features
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

# ================= CONSTANTS =================
CM_TO_PT = 28.35
PAPER_SIZES = {
    "A4 Sheet": (A4[0], A4[1], 25, 6),             # (W, H, Margin, Gap in PT)
    "4x6 Photo Paper (4R)": (4 * 72, 6 * 72, 12, 4) # (288pt, 432pt, Margin, Gap)
}

PHOTO_PRESETS = {
    "Auto-Fit (Original Ratio)": None,
    "Standard Passport (3.5 x 4.5 cm)": (3.5 * CM_TO_PT, 4.5 * CM_TO_PT),
    "Stamp Size (2.0 x 2.5 cm)": (2.0 * CM_TO_PT, 2.5 * CM_TO_PT),
    "PAN Card Size (2.5 x 3.5 cm)": (2.5 * CM_TO_PT, 3.5 * CM_TO_PT),
    "VISA Size (2 x 2 inch)": (2.0 * 72, 2.0 * 72)
}
BORDER = 1
# ============================================

st.set_page_config(
    page_title="PhotoPass Pro AI Studio",
    page_icon="📷",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] {
    font-family: 'Montserrat', sans-serif !important;
}
.stApp { background: #f0fafb; }
#MainMenu, footer, header { visibility: hidden; }

.block-container { padding: 0 !important; max-width: 100% !important; }

.hero {
    background: #fff;
    border-bottom: 3px solid #00bcd4;
    padding: 2.2rem 1.2rem 1.8rem;
    text-align: center;
}
.hero-icon {
    width: 60px; height: 60px;
    background: #00bcd4;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto .8rem;
    font-size: 28px;
    color: white;
}
.hero h1 {
    font-size: clamp(1.6rem, 5vw, 2.4rem);
    font-weight: 900;
    color: #0d0d0d;
    margin-bottom: .3rem;
}
.hero h1 span { color: #00bcd4; }
.hero p {
    font-size: clamp(.85rem, 2.5vw, 1rem);
    font-weight: 600;
    color: #555;
}

.content { max-width: 700px; margin: 0 auto; padding: 1.5rem 1rem 2rem; }

.sec-lbl {
    font-size: .75rem; font-weight: 800; letter-spacing: .1em;
    text-transform: uppercase; color: #00838f; margin-bottom: .5rem; display: block;
}

[data-testid="stFileUploader"] {
    background: #fff !important; border: 2.5px dashed #00bcd4 !important;
    border-radius: 14px !important; padding: 1.5rem 1rem !important; width: 100% !important;
}

.stButton > button {
    width: 100% !important; background: #00bcd4 !important; color: #fff !important;
    border: none !important; border-radius: 12px !important; padding: .9rem 1rem !important;
    font-weight: 800 !important; text-transform: uppercase !important;
    box-shadow: 0 4px 14px rgba(0,188,212,.35) !important; min-height: 52px !important;
}
.stButton > button:hover { background: #0097a7 !important; }

[data-testid="stDownloadButton"] button {
    width: 100% !important; background: #00897b !important; color: #fff !important;
    border: none !important; border-radius: 10px !important; min-height: 48px !important;
    font-weight: 800 !important;
}
[data-testid="stDownloadButton"] button:hover { background: #00695c !important; }

.option-card {
    background: #fff; border: 1.5px solid #b2ebf2; border-radius: 12px;
    padding: 1rem; margin-bottom: 1rem;
}
.divider { height: 1px; background: #b2ebf2; margin: 1.2rem 0; }
</style>
""",
    unsafe_allow_html=True,
)

# ── Session State Memory Initializer ──
if "processed" not in st.session_state:
    st.session_state.processed = False
    st.session_state.pdf_bytes = None
    st.session_state.pil_pages = []
    st.session_state.docx_bytes = None

def get_pil_font(size):
    font_names = ["arial.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf", "FreeSans.ttf", "Helvetica.ttf"]
    for fn in font_names:
        try:
            return ImageFont.truetype(fn, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

# ── AI FACE ALIGNMENT & SMART CROP ──
def auto_face_align_and_crop(pil_img):
    if not OPENCV_AVAILABLE:
        return pil_img
    
    img_np = np.array(pil_img)
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
    
    if len(faces) > 0:
        faces = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)
        fx, fy, fw, fh = faces[0]
        
        # Calculate ideal passport head-to-shoulder ratio
        total_h = int(fh / 0.52)
        total_w = int(total_h * (3.5 / 4.5))
        
        cx = fx + fw // 2
        top_y = max(0, fy - int(fh * 0.45))
        bottom_y = top_y + total_h
        
        left_x = max(0, cx - total_w // 2)
        right_x = left_x + total_w
        
        img_h, img_w = img_np.shape[:2]
        top_y = max(0, min(top_y, img_h))
        bottom_y = min(img_h, bottom_y)
        left_x = max(0, min(left_x, img_w))
        right_x = min(img_w, right_x)
        
        cropped_np = img_np[top_y:bottom_y, left_x:right_x]
        if cropped_np.size > 0:
            return Image.fromarray(cropped_np)
            
    return pil_img

# ── AI FACE RETOUCH & LIGHTING ENGINE ──
def auto_face_retouch_and_lighting(pil_img):
    if not OPENCV_AVAILABLE:
        return pil_img
        
    img_np = np.array(pil_img)
    
    # 1. Edge-preserving skin smoothing filter
    smoothed = cv2.bilateralFilter(img_np, d=7, sigmaColor=50, sigmaSpace=50)
    blended = cv2.addWeighted(img_np, 0.35, smoothed, 0.65, 0)
    
    # 2. CLAHE adaptive face lighting adjustment
    lab = cv2.cvtColor(blended, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=1.8, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    limg = cv2.merge((cl, a, b))
    
    final_np = cv2.cvtColor(limg, cv2.COLOR_LAB2RGB)
    return Image.fromarray(final_np)

# ── FORMAL SUIT / COAT OVERLAY DRAWING ──
def draw_formal_suit_overlay(img, suit_type, pos_y_offset, suit_scale):
    if suit_type == "None":
        return img
    
    w, h = img.size
    suit_w = int(w * suit_scale)
    suit_h = int(h * 0.45 * suit_scale)
    
    suit = Image.new("RGBA", (suit_w, suit_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(suit)
    
    suit_color = (20, 24, 30, 255) if "Black" in suit_type else (25, 45, 85, 255) if "Blue" in suit_type else (45, 45, 50, 255)
    shirt_color = (250, 250, 250, 255)
    tie_color = (180, 20, 30, 255)
    
    # Base Shoulders
    draw.ellipse([0, int(suit_h * 0.25), suit_w, suit_h * 2], fill=suit_color)
    # White Shirt Collar
    draw.polygon([(int(suit_w * 0.35), 0), (int(suit_w * 0.65), 0), (int(suit_w * 0.5), int(suit_h * 0.45))], fill=shirt_color)
    # Tie
    draw.polygon([(int(suit_w * 0.47), int(suit_h * 0.1)), (int(suit_w * 0.53), int(suit_h * 0.1)), (int(suit_w * 0.52), int(suit_h * 0.7)), (int(suit_w * 0.5), int(suit_h * 0.85)), (int(suit_w * 0.48), int(suit_h * 0.7))], fill=tie_color)
    # Coat Lapels
    draw.polygon([(int(suit_w * 0.15), int(suit_h * 0.3)), (int(suit_w * 0.38), int(suit_h * 0.15)), (int(suit_w * 0.42), suit_h)], fill=suit_color)
    draw.polygon([(int(suit_w * 0.85), int(suit_h * 0.3)), (int(suit_w * 0.62), int(suit_h * 0.15)), (int(suit_w * 0.58), suit_h)], fill=suit_color)

    overlay_x = (w - suit_w) // 2
    overlay_y = int(h * 0.58) + pos_y_offset

    img_rgba = img.convert("RGBA")
    img_rgba.paste(suit, (overlay_x, overlay_y), suit)
    return img_rgba.convert("RGB")

def apply_image_enhancements(img, brightness, contrast, sharpness):
    if brightness != 1.0:
        img = ImageEnhance.Brightness(img).enhance(brightness)
    if contrast != 1.0:
        img = ImageEnhance.Contrast(img).enhance(contrast)
    if sharpness != 1.0:
        img = ImageEnhance.Sharpness(img).enhance(sharpness)
    return img

def process_single_image(uf, bg_option, custom_bg_color, add_dop, dop_date, brightness, contrast, sharpness, auto_crop, auto_retouch, suit_type, suit_y_offset, suit_scale):
    uf.seek(0)
    img = Image.open(uf).convert("RGB")
    
    # 1. AI Smart Crop & Face Alignment
    if auto_crop:
        img = auto_face_align_and_crop(img)
        
    # 2. AI Retouching & Lighting
    if auto_retouch:
        img = auto_face_retouch_and_lighting(img)

    # 3. Manual Enhancements
    img = apply_image_enhancements(img, brightness, contrast, sharpness)
    
    # 4. Suit / Dress Overlay
    if suit_type != "None":
        img = draw_formal_suit_overlay(img, suit_type, suit_y_offset, suit_scale)

    # 5. AI Background Removal/Replacement
    if bg_option != "Original Background":
        if REMBG_AVAILABLE:
            img_rgba = remove(img, alpha_matting=True, alpha_matting_foreground_threshold=240)
            if bg_option == "Plain White":
                fill_color = (255, 255, 255)
            elif bg_option == "Light Blue":
                fill_color = (212, 230, 241)
            elif bg_option == "Red (Lal)":
                fill_color = (235, 64, 52)
            else:
                fill_color = hex_to_rgb(custom_bg_color)

            bg_img = Image.new("RGBA", img_rgba.size, fill_color)
            bg_img.paste(img_rgba, (0, 0), img_rgba)
            img = bg_img.convert("RGB")

    # 6. Direct Photo Text (File Name + DOP)
    w, h = img.size
    file_stem = os.path.splitext(uf.name)[0]
    
    if add_dop and dop_date:
        label = f"{file_stem} DOP: {dop_date}"
        font_size = max(9, int(h * 0.033))
    else:
        label = file_stem
        font_size = max(11, int(h * 0.048))

    sample_box = (0, int(h * 0.85), int(w * 0.90), h)
    crop_area = img.crop(sample_box).convert("L")
    pixels = list(crop_area.getdata())
    avg_brightness = sum(pixels) / max(1, len(pixels))

    if avg_brightness < 128:
        text_color = (255, 255, 255)
        stroke_color = (0, 0, 0)
    else:
        text_color = (0, 0, 0)
        stroke_color = (255, 255, 255)

    draw = ImageDraw.Draw(img)
    font = get_pil_font(font_size)

    try:
        bbox = draw.textbbox((0, 0), label, font=font)
        text_h = bbox[3] - bbox[1]
    except AttributeError:
        text_h = font_size

    text_x = max(2, int(w * 0.015))
    text_y = h - text_h - max(3, int(h * 0.025))

    draw.text((text_x, text_y), label, fill=text_color, font=font, stroke_width=2, stroke_fill=stroke_color)

    return img

def calculate_grid_layout(paper_choice, preset_choice, img_size, custom_gap):
    page_w, page_h, margin, default_gap = PAPER_SIZES[paper_choice]
    gap = custom_gap if custom_gap is not None else default_gap
    ow, oh = img_size
    
    if PHOTO_PRESETS[preset_choice] is not None:
        target_w, target_h = PHOTO_PRESETS[preset_choice]
        scale = min(target_w / ow, target_h / oh)
        fw, fh = int(ow * scale), int(oh * scale)
    else:
        max_h = 4.5 * CM_TO_PT
        usable_w = page_w - 2 * margin - 5 * gap
        adj_w = usable_w / 6
        scale = min(adj_w / ow, max_h / oh, 1.0)
        fw, fh = int(ow * scale), int(oh * scale)
        
    photos_per_row = max(1, int((page_w - 2 * margin + gap) / (fw + gap)))
    return page_w, page_h, margin, gap, fw, fh, photos_per_row

def build_pdf_bytes(uploaded_files, copies, paper_choice, preset_choice, bg_option, custom_bg_color, add_dop, dop_date, brightness, contrast, sharpness, draw_cutting_lines, custom_gap, auto_crop, auto_retouch, suit_type, suit_y_offset, suit_scale):
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
        pdf_path = tmp_pdf.name

    sample_img = Image.open(uploaded_files[0])
    page_w, page_h, margin, gap, fw, fh, photos_per_row = calculate_grid_layout(paper_choice, preset_choice, sample_img.size, custom_gap)

    c = canvas.Canvas(pdf_path, pagesize=(page_w, page_h))
    x_s, y_s = margin, page_h - margin
    x, y = x_s, y_s
    row_max_h = 0
    photo_in_row = 0
    tmp_files = []

    for uf in uploaded_files:
        img = process_single_image(uf, bg_option, custom_bg_color, add_dop, dop_date, brightness, contrast, sharpness, auto_crop, auto_retouch, suit_type, suit_y_offset, suit_scale)
        img_b = ImageOps.expand(img, border=BORDER, fill="black")
        
        tf = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tf.close()
        img_b.save(tf.name, format="PNG", dpi=(300, 300))
        tmp_files.append(tf.name)

        for _ in range(int(copies)):
            if y - fh < margin:
                c.showPage()
                x, y = x_s, y_s
                row_max_h = 0
                photo_in_row = 0

            c.drawImage(tf.name, x, y - fh, fw, fh, preserveAspectRatio=True)

            if draw_cutting_lines:
                c.setDash(2, 2)
                c.setStrokeColorRGB(0.6, 0.6, 0.6)
                c.rect(x - 1, y - fh - 1, fw + 2, fh + 2)

            row_max_h = max(row_max_h, fh)
            photo_in_row += 1
            x += fw + gap

            if photo_in_row >= photos_per_row:
                x, y = x_s, y - row_max_h - gap
                row_max_h = 0
                photo_in_row = 0

    c.save()

    for f in tmp_files:
        if os.path.exists(f): os.remove(f)

    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
    os.remove(pdf_path)

    return pdf_data

def build_pil_pages(uploaded_files, copies, paper_choice, preset_choice, bg_option, custom_bg_color, add_dop, dop_date, brightness, contrast, sharpness, draw_cutting_lines, custom_gap, auto_crop, auto_retouch, suit_type, suit_y_offset, suit_scale):
    DPI = 300
    SCALE = DPI / 72.0

    sample_img = Image.open(uploaded_files[0])
    page_w_pt, page_h_pt, margin_pt, gap_pt, fw_pt, fh_pt, photos_per_row = calculate_grid_layout(paper_choice, preset_choice, sample_img.size, custom_gap)

    PAGE_W_PX = int(page_w_pt * SCALE)
    PAGE_H_PX = int(page_h_pt * SCALE)
    MARGIN_PX = int(margin_pt * SCALE)
    GAP_PX = int(gap_pt * SCALE)
    BORDER_PX = max(1, int(BORDER * SCALE))
    fw_px = int(fw_pt * SCALE)
    fh_px = int(fh_pt * SCALE)

    pages = []
    def create_new_page():
        return Image.new("RGB", (PAGE_W_PX, PAGE_H_PX), "white")

    current_page = create_new_page()

    x_s, y_s = MARGIN_PX, MARGIN_PX
    x, y = x_s, y_s
    row_max_h = 0
    photo_in_row = 0

    for uf in uploaded_files:
        img = process_single_image(uf, bg_option, custom_bg_color, add_dop, dop_date, brightness, contrast, sharpness, auto_crop, auto_retouch, suit_type, suit_y_offset, suit_scale)
        img_resized = img.resize((fw_px - 2 * BORDER_PX, fh_px - 2 * BORDER_PX), Image.Resampling.LANCZOS)
        img_b = ImageOps.expand(img_resized, border=BORDER_PX, fill="black")

        for _ in range(int(copies)):
            if y + fh_px > PAGE_H_PX - MARGIN_PX:
                pages.append(current_page)
                current_page = create_new_page()
                x, y = x_s, y_s
                row_max_h = 0
                photo_in_row = 0

            current_page.paste(img_b, (x, y))

            if draw_cutting_lines:
                draw_p = ImageDraw.Draw(current_page)
                draw_p.rectangle([x - 1, y - 1, x + fw_px + 1, y + fh_px + 1], outline="gray")

            row_max_h = max(row_max_h, fh_px)
            photo_in_row += 1
            x += fw_px + GAP_PX

            if photo_in_row >= photos_per_row:
                x, y = x_s, y + row_max_h + GAP_PX
                row_max_h = 0
                photo_in_row = 0

    pages.append(current_page)
    return pages

def build_docx_bytes(pil_pages, paper_choice):
    doc = Document()
    for section in doc.sections:
        if "4x6" in paper_choice:
            section.page_width, section.page_height = Inches(4.0), Inches(6.0)
            section.top_margin = section.bottom_margin = section.left_margin = section.right_margin = Inches(0.15)
            img_w_in = 3.7
        else:
            section.page_width, section.page_height = Inches(8.27), Inches(11.69)
            section.top_margin = section.bottom_margin = section.left_margin = section.right_margin = Inches(0.2)
            img_w_in = 7.87

    for i, page_img in enumerate(pil_pages):
        if i > 0: doc.add_page_break()
        img_io = io.BytesIO()
        page_img.save(img_io, format="JPEG", quality=100, subsampling=0, dpi=(300, 300))
        img_io.seek(0)
        doc.add_picture(img_io, width=Inches(img_w_in))

    doc_io = io.BytesIO()
    doc.save(doc_io)
    return doc_io.getvalue()

# ── Hero ──
st.markdown(
    """
<div class="hero">
    <div class="hero-icon">📷</div>
    <h1>Photo<span>Pass</span> Pro AI Studio</h1>
    <p>AI Auto Crop, Face Retouch & Formal Suit Changer Engine</p>
</div>
<div class="content">
""",
    unsafe_allow_html=True,
)

# ── Upload ──
st.markdown('<span class="sec-lbl">📁 Photos Upload Karo</span>', unsafe_allow_html=True)
uploaded_files = st.file_uploader(
    "JPG, JPEG ya PNG photos chunno",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)

# ── AI Smart Editing Section ──
st.markdown('<span class="sec-lbl">🤖 AI & Smart Editing Tools</span>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="option-card">', unsafe_allow_html=True)
    col_ai1, col_ai2 = st.columns(2)
    with col_ai1:
        auto_crop = st.checkbox("🎯 AI Auto Face Align & Smart Crop", value=True)
    with col_ai2:
        auto_retouch = st.checkbox("✨ AI Face Retouch & Smooth Lighting", value=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Suit Changer Options
    suit_type = st.selectbox("👔 AI Dress / Suit Changer", ["None", "Black Suit & Red Tie", "Navy Blue Suit & Tie", "Charcoal Formal Suit"])
    suit_y_offset, suit_scale = 0, 1.0
    if suit_type != "None":
        s_c1, s_c2 = st.columns(2)
        with s_c1:
            suit_y_offset = st.slider("📐 Suit Position Up/Down", -30, 30, 0)
        with s_c2:
            suit_scale = st.slider("🔍 Suit Size Scale", 0.8, 1.3, 1.0, 0.05)

    st.markdown('</div>', unsafe_allow_html=True)

# ── General Settings ──
st.markdown('<span class="sec-lbl">⚙️ Layout & Paper Settings</span>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="option-card">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        paper_choice = st.selectbox("🖨️ Paper Size", list(PAPER_SIZES.keys()), index=0)
    with c2:
        preset_choice = st.selectbox("📐 Photo Size Preset", list(PHOTO_PRESETS.keys()), index=0)
        
    c3, c4 = st.columns(2)
    with c3:
        copies = st.number_input("🔢 Har Photo Ki Copies", min_value=1, max_value=30, value=2, step=1)
    with c4:
        bg_option = st.selectbox("🎨 Background Color (AI)", ["Original Background", "Plain White", "Light Blue", "Red (Lal)", "Custom Color"], index=0)

    custom_bg_color = "#D4E6F1"
    if bg_option == "Custom Color":
        custom_bg_color = st.color_picker("Background Color Select Karo", "#D4E6F1")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    add_dop = st.checkbox("📅 Photo Par DOP (Date of Photo) Add Karein?", value=True)
    today_str = datetime.date.today().strftime("%d/%m/%Y")
    dop_date = st.text_input("DOP Date Put Karein:", value=today_str) if add_dop else ""

    st.markdown('</div>', unsafe_allow_html=True)

# ── Manual Touchup Controls ──
st.markdown('<span class="sec-lbl">🛠️ Manual Light & Print Customization</span>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="option-card">', unsafe_allow_html=True)
    
    col_e1, col_e2, col_e3 = st.columns(3)
    with col_e1:
        brightness = st.slider("☀️ Brightness", 0.5, 1.5, 1.0, 0.05)
    with col_e2:
        contrast = st.slider("🌓 Contrast", 0.5, 1.5, 1.0, 0.05)
    with col_e3:
        sharpness = st.slider("🔪 Sharpness", 0.5, 2.0, 1.0, 0.1)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        draw_cutting_lines = st.checkbox("✂️ Cutting Lines (Dotted Borders)", value=True)
    with col_p2:
        custom_gap = st.slider("📏 Photo Gap (Spacing)", 2, 15, 6)

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Action Button ──
if st.button("⚡ Process & Generate Files"):
    if not uploaded_files:
        st.error("❌ Pehle photos upload karo!")
        st.session_state.processed = False
    else:
        prog = st.progress(0)
        status = st.empty()

        def update_prog(p, msg):
            prog.progress(p, text=msg)

        update_prog(30, "📐 Processing PDF Sheet...")
        st.session_state.pdf_bytes = build_pdf_bytes(
            uploaded_files, copies, paper_choice, preset_choice, bg_option, custom_bg_color, add_dop, dop_date, brightness, contrast, sharpness, draw_cutting_lines, custom_gap, auto_crop, auto_retouch, suit_type, suit_y_offset, suit_scale
        )

        update_prog(70, "🖼️ Processing High-Res Image...")
        st.session_state.pil_pages = build_pil_pages(
            uploaded_files, copies, paper_choice, preset_choice, bg_option, custom_bg_color, add_dop, dop_date, brightness, contrast, sharpness, draw_cutting_lines, custom_gap, auto_crop, auto_retouch, suit_type, suit_y_offset, suit_scale
        )

        update_prog(90, "📝 Processing Word Document...")
        st.session_state.docx_bytes = build_docx_bytes(st.session_state.pil_pages, paper_choice)

        update_prog(100, "✅ Done!")
        status.empty()
        st.session_state.processed = True

# ── Download Buttons ──
if st.session_state.get("processed", False) and uploaded_files:
    st.markdown("### 🎉 Download Files:")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button("📄 PDF Sheet", st.session_state.pdf_bytes, "passport_photos.pdf", "application/pdf", use_container_width=True)

    with col2:
        pil_pages = st.session_state.pil_pages
        if len(pil_pages) == 1:
            img_byte_arr = io.BytesIO()
            pil_pages[0].save(img_byte_arr, format="JPEG", quality=100, dpi=(300, 300))
            st.download_button("🖼️ JPG Image", img_byte_arr.getvalue(), "passport_photos.jpg", "image/jpeg", use_container_width=True)
        else:
            for idx, page_img in enumerate(pil_pages):
                img_byte_arr = io.BytesIO()
                page_img.save(img_byte_arr, format="JPEG", quality=100, dpi=(300, 300))
                st.download_button(f"🖼️ JPG (Page {idx+1})", img_byte_arr.getvalue(), f"passport_photos_page_{idx+1}.jpg", "image/jpeg", key=f"jpg_btn_{idx}", use_container_width=True)

    with col3:
        st.download_button("📝 Word Document", st.session_state.docx_bytes, "passport_photos.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)
