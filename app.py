import io
import os
import tempfile
import datetime
import docx
from docx import Document
from docx.shared import Inches
from PIL import Image, ImageDraw, ImageFont, ImageOps
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import streamlit as st

# Rembg AI Background removal import check
try:
    from rembg import remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

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
    page_title="PhotoPass Pro",
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

def process_single_image(uf, bg_option, custom_bg_color, add_dop, dop_date):
    """Clean Background Replacement + Direct Photo Text Drawing (Corner aligned & Dynamic Font)."""
    uf.seek(0)
    img = Image.open(uf).convert("RGB")
    
    # 1. AI Background Change
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

    # 2. Add File Name + DOP Date
    w, h = img.size
    file_stem = os.path.splitext(uf.name)[0]
    
    # Font size condition: DOP hai toh font chhota karo, sirf name hai toh normal size
    if add_dop and dop_date:
        label = f"{file_stem} DOP: {dop_date}"
        font_size = max(9, int(h * 0.033))  # Chhota font DOP ke sath
    else:
        label = file_stem
        font_size = max(11, int(h * 0.048)) # Normal font sirf Name ke sath

    # Auto Brightness Calculation at Bottom Corner
    sample_box = (0, int(h * 0.85), int(w * 0.90), h)
    crop_area = img.crop(sample_box).convert("L")
    pixels = list(crop_area.getdata())
    avg_brightness = sum(pixels) / max(1, len(pixels))

    # Smart Contrast Colors
    if avg_brightness < 128:
        text_color = (255, 255, 255)
        stroke_color = (0, 0, 0)
    else:
        text_color = (0, 0, 0)
        stroke_color = (255, 255, 255)

    draw = ImageDraw.Draw(img)
    font = get_pil_font(font_size)

    # Exact Text Height Calculate for Tight Corner Placement
    try:
        bbox = draw.textbbox((0, 0), label, font=font)
        text_h = bbox[3] - bbox[1]
    except AttributeError:
        text_h = font_size

    # Ekdum Kone Aur Niche Alignment
    text_x = max(2, int(w * 0.015))                   # Ekdum left kone me
    text_y = h - text_h - max(3, int(h * 0.025))      # Ekdum niche border se thoda upar

    # Draw text with 2px stroke outline
    draw.text((text_x, text_y), label, fill=text_color, font=font, stroke_width=2, stroke_fill=stroke_color)

    return img

def calculate_grid_layout(paper_choice, preset_choice, img_size):
    page_w, page_h, margin, gap = PAPER_SIZES[paper_choice]
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

def build_pdf_bytes(uploaded_files, copies, paper_choice, preset_choice, bg_option, custom_bg_color, add_dop, dop_date):
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
        pdf_path = tmp_pdf.name

    sample_img = Image.open(uploaded_files[0])
    page_w, page_h, margin, gap, fw, fh, photos_per_row = calculate_grid_layout(paper_choice, preset_choice, sample_img.size)

    c = canvas.Canvas(pdf_path, pagesize=(page_w, page_h))
    x_s, y_s = margin, page_h - margin
    x, y = x_s, y_s
    row_max_h = 0
    photo_in_row = 0
    tmp_files = []

    for uf in uploaded_files:
        img = process_single_image(uf, bg_option, custom_bg_color, add_dop, dop_date)
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

def build_pil_pages(uploaded_files, copies, paper_choice, preset_choice, bg_option, custom_bg_color, add_dop, dop_date):
    DPI = 300
    SCALE = DPI / 72.0

    sample_img = Image.open(uploaded_files[0])
    page_w_pt, page_h_pt, margin_pt, gap_pt, fw_pt, fh_pt, photos_per_row = calculate_grid_layout(paper_choice, preset_choice, sample_img.size)

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
        img = process_single_image(uf, bg_option, custom_bg_color, add_dop, dop_date)
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
    <h1>Photo<span>Pass</span> Pro</h1>
    <p>File Name + DOP Date Smart Contrast Ke Saath Generate Karein</p>
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

# ── Settings ──
st.markdown('<span class="sec-lbl">⚙️ Settings & Options</span>', unsafe_allow_html=True)
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

    # DOP Section
    add_dop = st.checkbox("📅 Photo Par DOP (Date of Photo) Add Karein?", value=True)
    today_str = datetime.date.today().strftime("%d/%m/%Y")
    
    if add_dop:
        dop_date = st.text_input("DOP Date Put Karein:", value=today_str)
    else:
        dop_date = ""

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

        update_prog(30, "📐 Processing PDF...")
        st.session_state.pdf_bytes = build_pdf_bytes(
            uploaded_files, copies, paper_choice, preset_choice, bg_option, custom_bg_color, add_dop, dop_date
        )

        update_prog(70, "🖼️ Processing High-Res JPG...")
        st.session_state.pil_pages = build_pil_pages(
            uploaded_files, copies, paper_choice, preset_choice, bg_option, custom_bg_color, add_dop, dop_date
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
