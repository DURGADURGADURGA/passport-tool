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
    "A4 Sheet": (A4[0], A4[1], 25, 6),             # (W, H, Margin, Gap)
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

@keyframes fadeDown { from{opacity:0;transform:translateY(-16px)} to{opacity:1;transform:translateY(0)} }
@keyframes pulse    { 0%,100%{box-shadow:0 0 0 0 rgba(0,188,212,.4)} 50%{box-shadow:0 0 0 10px rgba(0,188,212,0)} }
@keyframes shimmer  { 0%{background-position:-400px 0} 100%{background-position:400px 0} }

*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] {
    font-family: 'Montserrat', sans-serif !important;
    -webkit-text-size-adjust: 100%;
}
.stApp { background: #f0fafb; }
#MainMenu, footer, header { visibility: hidden; }

.block-container { padding: 0 !important; max-width: 100% !important; }
.main > div { padding: 0 !important; }

.hero {
    background: #fff;
    border-bottom: 3px solid #00bcd4;
    padding: 2.5rem 1.5rem 2rem;
    text-align: center;
    animation: fadeDown .5s ease both;
    width: 100%;
}
.hero-icon {
    width: 70px; height: 70px;
    background: #00bcd4;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto .9rem;
    font-size: 30px;
    animation: pulse 2.5s ease-in-out infinite;
}
.hero h1 {
    font-size: clamp(1.6rem, 5vw, 2.6rem);
    font-weight: 900;
    color: #0d0d0d;
    letter-spacing: -.02em;
    margin-bottom: .4rem;
    line-height: 1.1;
}
.hero h1 span { color: #00bcd4; }
.hero p {
    font-size: clamp(.85rem, 2.5vw, 1rem);
    font-weight: 600;
    color: #555;
    margin-bottom: 1.2rem;
    padding: 0 .5rem;
}
.steps-row {
    display: flex; justify-content: center; gap: 6px; flex-wrap: wrap; padding: 0 .5rem;
}
.step-pill {
    background: #e0f7fa; border-radius: 30px; padding: 6px 12px;
    display: inline-flex; align-items: center; gap: 6px; margin-bottom: 4px;
}
.step-pill .sn {
    background: #00bcd4; color: #fff; font-size: 10px; font-weight: 800;
    width: 20px; height: 20px; border-radius: 50%;
    display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.step-pill .st { font-size: 11px; font-weight: 700; color: #007b8a; white-space: nowrap; }

.content { max-width: 700px; margin: 0 auto; padding: 1.5rem 1rem 2rem; }

.sec-lbl {
    font-size: .72rem; font-weight: 800; letter-spacing: .1em;
    text-transform: uppercase; color: #00838f; margin-bottom: .5rem; display: block;
}

[data-testid="stFileUploader"] {
    background: #fff !important; border: 2.5px dashed #00bcd4 !important;
    border-radius: 14px !important; padding: 1.5rem 1rem !important; width: 100% !important;
}
[data-testid="stFileUploader"]:hover { background: #e0f7fa !important; }

[data-testid="stNumberInput"] input, [data-testid="stSelectbox"] select {
    background: #fff !important; border: 2px solid #b2ebf2 !important;
    border-radius: 10px !important; font-family: 'Montserrat', sans-serif !important;
    font-weight: 700 !important;
}

.stButton > button {
    width: 100% !important; background: #00bcd4 !important; color: #fff !important;
    border: none !important; border-radius: 12px !important; padding: .9rem 1rem !important;
    font-family: 'Montserrat', sans-serif !important; font-size: clamp(.9rem, 2.5vw, 1rem) !important;
    font-weight: 800 !important; text-transform: uppercase !important;
    box-shadow: 0 4px 14px rgba(0,188,212,.35) !important; min-height: 52px !important;
}
.stButton > button:hover { background: #0097a7 !important; }

[data-testid="stDownloadButton"] button {
    width: 100% !important; background: #00897b !important; color: #fff !important;
    border: none !important; border-radius: 10px !important; padding: .8rem .8rem !important;
    font-weight: 800 !important; text-transform: uppercase !important; min-height: 48px !important;
}
[data-testid="stDownloadButton"] button:hover { background: #00695c !important; }

.info-section {
    background: #e0f2f1; border-top: 3px solid #00bcd4; padding: 1.8rem 1rem 1.5rem;
    margin-top: 2rem; display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; width: 100%;
}
.info-col { text-align: center; padding: 0 6px; }
.info-icon-wrap {
    width: 48px; height: 48px; background: #00bcd4; border-radius: 50%;
    display: flex; align-items: center; justify-content: center; margin: 0 auto 8px; font-size: 20px;
}
.info-col h4 { font-size: .65rem; font-weight: 800; text-transform: uppercase; margin-bottom: 4px; }
.info-col p { font-size: .68rem; color: #555; line-height: 1.5; }

.footer-bar { background: #00bcd4; padding: 12px 16px; text-align: center; width: 100%; }
.footer-bar p { font-size: .68rem; font-weight: 700; color: #fff; margin: 0; }
.divider { height: 1px; background: #b2ebf2; margin: 1.2rem 0; }

.option-card {
    background: #fff; border: 1.5px solid #b2ebf2; border-radius: 12px;
    padding: 1rem; margin-bottom: 1rem;
}
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

def process_single_image(uf, bg_option, add_name_date, c_name, p_date):
    """Applies Background Change and Name & Date Strip if requested."""
    uf.seek(0)
    img = Image.open(uf).convert("RGB")
    
    # 1. Background Change (AI feature)
    if bg_option != "Original Background":
        if REMBG_AVAILABLE:
            img_rgba = remove(img)
            fill_color = (255, 255, 255) if bg_option == "Plain White" else (212, 230, 241) # Light Blue
            bg_img = Image.new("RGBA", img_rgba.size, fill_color)
            bg_img.paste(img_rgba, (0, 0), img_rgba)
            img = bg_img.convert("RGB")
        else:
            st.warning("⚠️ `rembg` library install nahi hai. Original background use ho raha hai.")

    # 2. Name & Date Strip (Govt Forms)
    if add_name_date and (c_name or p_date):
        w, h = img.size
        strip_h = int(h * 0.18)
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, h - strip_h, w, h], fill="white")
        
        font_size = max(10, int(strip_h * 0.35))
        font = get_pil_font(font_size)
        text_lines = []
        if c_name:
            text_lines.append(c_name.strip().upper())
        if p_date:
            text_lines.append(f"DOP: {p_date.strip()}")
            
        full_text = "\n".join(text_lines)
        draw.multiline_text((w // 2, h - strip_h // 2), full_text, fill="black", font=font, anchor="mm", align="center")

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

def build_pdf_bytes(uploaded_files, copies, paper_choice, preset_choice, bg_option, add_name_date, c_name, p_date):
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
        img = process_single_image(uf, bg_option, add_name_date, c_name, p_date)
        img_b = ImageOps.expand(img, border=BORDER, fill="black")
        
        tf = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tf.close()
        img_b.save(tf.name, format="PNG", dpi=(300, 300))
        tmp_files.append(tf.name)

        fname = os.path.splitext(uf.name)[0]

        # Calculate brightness in bottom-left corner region
        crop_w = min(img_b.width, int(fw * 0.6))
        crop_h = min(img_b.height, int(fh * 0.2))
        crop_area = img_b.crop((0, img_b.height - crop_h, crop_w, img_b.height)).convert("L")
        pixels = list(crop_area.getdata())
        avg_brightness = sum(pixels) / max(1, len(pixels))

        for _ in range(int(copies)):
            if y - fh < margin:
                c.showPage()
                x, y = x_s, y_s
                row_max_h = 0
                photo_in_row = 0

            c.drawImage(tf.name, x, y - fh, fw, fh, preserveAspectRatio=True)
            c.setFont("Helvetica-Bold", 7)
            
            # Auto Contrast text color
            if avg_brightness < 128:
                c.setFillColorRGB(1, 1, 1)
            else:
                c.setFillColorRGB(0, 0, 0)

            c.drawString(x + 2, y - fh + 2, fname[:20])

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

def build_pil_pages(uploaded_files, copies, paper_choice, preset_choice, bg_option, add_name_date, c_name, p_date):
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
    draw = ImageDraw.Draw(current_page)

    x_s, y_s = MARGIN_PX, MARGIN_PX
    x, y = x_s, y_s
    row_max_h = 0
    photo_in_row = 0

    font_size_px = int(7.5 * SCALE)
    font = get_pil_font(font_size_px)

    for uf in uploaded_files:
        img = process_single_image(uf, bg_option, add_name_date, c_name, p_date)
        img_resized = img.resize((fw_px - 2 * BORDER_PX, fh_px - 2 * BORDER_PX), Image.Resampling.LANCZOS)
        img_b = ImageOps.expand(img_resized, border=BORDER_PX, fill="black")

        fname = os.path.splitext(uf.name)[0][:20]

        crop_w = min(img_b.width, int(fw_px * 0.6))
        crop_h = min(img_b.height, int(fh_px * 0.2))
        crop_area = img_b.crop((0, img_b.height - crop_h, crop_w, img_b.height)).convert("L")
        pixels = list(crop_area.getdata())
        avg_brightness = sum(pixels) / max(1, len(pixels))

        text_color = (255, 255, 255) if avg_brightness < 128 else (0, 0, 0)

        for _ in range(int(copies)):
            if y + fh_px > PAGE_H_PX - MARGIN_PX:
                pages.append(current_page)
                current_page = create_new_page()
                draw = ImageDraw.Draw(current_page)
                x, y = x_s, y_s
                row_max_h = 0
                photo_in_row = 0

            current_page.paste(img_b, (x, y))
            draw.text((x + int(2 * SCALE), y + fh_px - int(9 * SCALE)), fname, fill=text_color, font=font)

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
            section.page_width = Inches(4.0)
            section.page_height = Inches(6.0)
            section.top_margin = Inches(0.15)
            section.bottom_margin = Inches(0.15)
            section.left_margin = Inches(0.15)
            section.right_margin = Inches(0.15)
            img_w_in = 3.7
        else:
            section.page_width = Inches(8.27)
            section.page_height = Inches(11.69)
            section.top_margin = Inches(0.2)
            section.bottom_margin = Inches(0.2)
            section.left_margin = Inches(0.2)
            section.right_margin = Inches(0.2)
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
    <p>Multiple logon ki photos ek saath (PDF, JPG, WORD) mein arrange karo!</p>
    <div class="steps-row">
        <div class="step-pill"><span class="sn">1</span><span class="st">Upload Photos</span></div>
        <div class="step-pill"><span class="sn">2</span><span class="st">Paper & Size Chuno</span></div>
        <div class="step-pill"><span class="sn">3</span><span class="st">Generate & Download</span></div>
    </div>
</div>
<div class="content">
""",
    unsafe_allow_html=True,
)

# ── Upload ──
st.markdown('<span class="sec-lbl">📁 Photos Upload Karo</span>', unsafe_allow_html=True)
uploaded_files = st.file_uploader(
    "JPG, JPEG ya PNG — ek ya zyada photos chunno",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)

# ── Advanced Controls Section ──
st.markdown('<span class="sec-lbl">⚙️ Customization & Settings</span>', unsafe_allow_html=True)
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
        bg_option = st.selectbox("🎨 Background Color Change (AI)", ["Original Background", "Plain White", "Light Blue"], index=0)

    # Govt Forms Strip Toggle
    add_name_date = st.checkbox("📝 Name & Date Strip Add Karein? (Govt Forms Special)")
    c_name, p_date = "", ""
    if add_name_date:
        col_n, col_d = st.columns(2)
        with col_n:
            c_name = st.text_input("Candidate Name", placeholder="e.g. RAHUL SHARMA")
        with col_d:
            today_str = datetime.date.today().strftime("%d/%m/%Y")
            p_date = st.text_input("Date of Photo (DOP)", value=today_str)
            
    st.markdown('</div>', unsafe_allow_html=True)

# ── Preview ──
if uploaded_files:
    st.markdown(
        f"""
    <div style="background:#e0f7fa;border:1.5px solid #80deea;border-radius:10px;
    padding:.75rem 1rem;margin:.8rem 0;color:#006064;font-size:.88rem;font-weight:700">
        ✅ &nbsp; {len(uploaded_files)} photo(s) select ki gayi hain
    </div>
    """,
        unsafe_allow_html=True,
    )

    num_cols = min(len(uploaded_files), 4)
    cols = st.columns(num_cols)
    for i, f in enumerate(uploaded_files):
        with cols[i % num_cols]:
            st.image(f, use_container_width=True, caption=f.name.split(".")[0][:8])

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Main Generate Action ──
if st.button("⚡ Files Process & Generate Karo"):
    if not uploaded_files:
        st.error("❌ Pehle photos upload karo!")
        st.session_state.processed = False
    else:
        prog = st.progress(0)
        status = st.empty()

        def update_prog(p, msg):
            prog.progress(p, text=msg)
            status.markdown(
                f'<p style="text-align:center;color:#00838f;font-size:.82rem;font-weight:600;margin-top:.3rem">{msg}</p>',
                unsafe_allow_html=True,
            )

        update_prog(20, "📐 PDF layout tayar ho raha hai...")
        st.session_state.pdf_bytes = build_pdf_bytes(uploaded_files, copies, paper_choice, preset_choice, bg_option, add_name_date, c_name, p_date)

        update_prog(60, "🖼️ High-Res Image (JPG) layout ban raha hai...")
        st.session_state.pil_pages = build_pil_pages(uploaded_files, copies, paper_choice, preset_choice, bg_option, add_name_date, c_name, p_date)

        update_prog(85, "📝 Word Document (.docx) generate ho raha hai...")
        st.session_state.docx_bytes = build_docx_bytes(st.session_state.pil_pages, paper_choice)

        update_prog(100, "✅ Sabhi Formats Ready!")
        status.empty()
        st.session_state.processed = True

# ── DOWNLOAD BUTTONS ──
if st.session_state.get("processed", False) and uploaded_files:
    st.markdown(
        """
    <div style="background:#e0f7fa;border:2px solid #00bcd4;border-radius:12px;
    padding:.9rem 1rem;text-align:center;color:#006064;font-size:.95rem;font-weight:700;margin:1rem 0">
        🎉 Sabhi formats tayar hain! Kisi bhi format ko kitni bhi baar download karein:
    </div>
    """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            label="📄 PDF Sheet",
            data=st.session_state.pdf_bytes,
            file_name="passport_photos.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    with col2:
        pil_pages = st.session_state.pil_pages
        if len(pil_pages) == 1:
            img_byte_arr = io.BytesIO()
            pil_pages[0].save(img_byte_arr, format="JPEG", quality=100, subsampling=0, dpi=(300, 300))
            st.download_button(
                label="🖼️ JPG Image",
                data=img_byte_arr.getvalue(),
                file_name="passport_photos.jpg",
                mime="image/jpeg",
                use_container_width=True,
            )
        else:
            for idx, page_img in enumerate(pil_pages):
                img_byte_arr = io.BytesIO()
                page_img.save(img_byte_arr, format="JPEG", quality=100, subsampling=0, dpi=(300, 300))
                st.download_button(
                    label=f"🖼️ JPG (P. {idx+1})",
                    data=img_byte_arr.getvalue(),
                    file_name=f"passport_photos_page_{idx+1}.jpg",
                    mime="image/jpeg",
                    key=f"jpg_btn_{idx}",
                    use_container_width=True,
                )

    with col3:
        st.download_button(
            label="📝 Word Document",
            data=st.session_state.docx_bytes,
            file_name="passport_photos.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )

st.markdown("</div>", unsafe_allow_html=True)

# ── Info + Footer ──
st.markdown(
    """
<div class="info-section">
    <div class="info-col">
        <div class="info-icon-wrap">⚡</div>
        <div>
            <h4>Fast & Free</h4>
            <p>Koi signup nahi chahiye</p>
        </div>
    </div>
    <div class="info-col">
        <div class="info-icon-wrap">🖨️</div>
        <div>
            <h4>Multi-Format</h4>
            <p>PDF, JPG & Word Document Ready</p>
        </div>
    </div>
    <div class="info-col">
        <div class="info-icon-wrap">🔒</div>
        <div>
            <h4>100% Secure</h4>
            <p>Photos kahin save nahi hoti</p>
        </div>
    </div>
</div>
<div class="footer-bar">
    <p>PHOTOPASS PRO &nbsp;·&nbsp; FREE TO USE &nbsp;·&nbsp; NO SIGNUP REQUIRED</p>
</div>
""",
    unsafe_allow_html=True,
)
