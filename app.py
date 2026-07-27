import io
import os
import tempfile
import docx
from docx import Document
from docx.shared import Inches
from PIL import Image, ImageDraw, ImageFont, ImageOps
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import streamlit as st

# ================= SETTINGS =================
PAGE_W, PAGE_H = A4
MARGIN = 25
GAP = 6
BORDER = 1
PHOTOS_PER_ROW = 6
MAX_HEIGHT_CM = 4.5
CM_TO_PT = 28.35
MAX_H = int(MAX_HEIGHT_CM * CM_TO_PT)
# ============================================

st.set_page_config(
    page_title="PhotoPass Pro",
    page_icon="📷",
    layout="wide", # Changed to wide to fit multiple photos comfortably
    initial_sidebar_state="collapsed",
)

# ── Updated Design (Indigo / Modern Theme) ──
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&display=swap');

@keyframes fadeDown { from{opacity:0;transform:translateY(-16px)} to{opacity:1;transform:translateY(0)} }
@keyframes pulse    { 0%,100%{box-shadow:0 0 0 0 rgba(79,70,229,.4)} 50%{box-shadow:0 0 0 10px rgba(79,70,229,0)} }
@keyframes shimmer  { 0%{background-position:-400px 0} 100%{background-position:400px 0} }

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] {
    font-family: 'Montserrat', sans-serif !important;
    -webkit-text-size-adjust: 100%;
}
.stApp { background: #f5f7ff; }
#MainMenu, footer, header { visibility: hidden; }

/* ── Hero ── */
.hero {
    background: #ffffff;
    border-bottom: 3px solid #4f46e5;
    padding: 2.5rem 1.5rem 2rem;
    text-align: center;
    animation: fadeDown .5s ease both;
    width: 100%;
    border-radius: 0 0 20px 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    margin-bottom: 2rem;
}
.hero-icon {
    width: 70px; height: 70px;
    background: #4f46e5;
    color: white;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto .9rem;
    font-size: 30px;
    animation: pulse 2.5s ease-in-out infinite;
}
.hero h1 {
    font-size: clamp(1.6rem, 5vw, 2.6rem);
    font-weight: 900;
    color: #111827;
    letter-spacing: -.02em;
    margin-bottom: .4rem;
    line-height: 1.1;
}
.hero h1 span { color: #4f46e5; }
.hero p {
    font-size: clamp(.85rem, 2.5vw, 1rem);
    font-weight: 600;
    color: #4b5563;
    margin-bottom: 1.2rem;
    padding: 0 .5rem;
}
.steps-row {
    display: flex;
    justify-content: center;
    gap: 8px;
    flex-wrap: wrap;
    padding: 0 .5rem;
}
.step-pill {
    background: #eef2ff;
    border: 1px solid #c7d2fe;
    border-radius: 30px;
    padding: 6px 14px;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
}
.step-pill .sn {
    background: #4f46e5; color: #fff;
    font-size: 11px; font-weight: 800;
    width: 22px; height: 22px;
    border-radius: 50%;
    display: inline-flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}
.step-pill .st {
    font-size: 12px; font-weight: 700; color: #3730a3;
    white-space: nowrap;
}

/* ── Content wrapper ── */
.content {
    max-width: 900px;
    margin: 0 auto;
    padding: 1rem;
}

/* ── Section label ── */
.sec-lbl {
    font-size: .75rem; font-weight: 800;
    letter-spacing: .1em; text-transform: uppercase;
    color: #4338ca; margin-bottom: .5rem;
    display: block;
}

/* ── Upload zone ── */
[data-testid="stFileUploader"] {
    background: #ffffff !important;
    border: 2.5px dashed #6366f1 !important;
    border-radius: 14px !important;
    padding: 1.5rem 1rem !important;
    transition: all .2s !important;
    width: 100% !important;
}
[data-testid="stFileUploader"]:hover {
    background: #eef2ff !important;
}

/* ── Buttons ── */
.stButton > button {
    width: 100% !important;
    background: #4f46e5 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 12px !important;
    padding: .9rem 1rem !important;
    font-family: 'Montserrat', sans-serif !important;
    font-size: clamp(.9rem, 2.5vw, 1rem) !important;
    font-weight: 800 !important;
    letter-spacing: .05em !important;
    text-transform: uppercase !important;
    box-shadow: 0 4px 14px rgba(79,70,229,.35) !important;
    transition: all .2s !important;
    min-height: 52px !important;
}
.stButton > button:hover {
    background: #4338ca !important;
    transform: translateY(-2px) !important;
}

[data-testid="stDownloadButton"] button {
    background: #059669 !important;
    box-shadow: 0 4px 14px rgba(5,150,105,.35) !important;
    margin-bottom: 8px !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: #047857 !important;
}

/* ── Progress ── */
[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg,#4f46e5,#818cf8,#4f46e5) !important;
    background-size: 400px 100% !important;
    animation: shimmer 1.5s linear infinite !important;
    border-radius: 100px !important;
}

/* ── Edit Box ── */
div[data-testid="stExpander"] {
    background: #ffffff;
    border: 1px solid #e5e7eb !important;
    border-radius: 10px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03);
}

.divider {
    height: 1px;
    background: #c7d2fe;
    margin: 1.5rem 0;
}
</style>
""",
    unsafe_allow_html=True,
)

# ── Session State Initializer ──
if "processed" not in st.session_state:
    st.session_state.processed = False
    st.session_state.pdf_bytes = None
    st.session_state.pil_pages = []
    st.session_state.docx_bytes = None

# ── Image Editing Helper ──
def apply_edits(img, rotation, crop_left, crop_right, crop_top, crop_bottom):
    """Applies manual rotation and exact crop percentages to the PIL image."""
    # Rotate
    if rotation != 0:
        # Negative for clockwise rotation
        img = img.rotate(-rotation, expand=True, fillcolor="white")
    
    # Crop
    w, h = img.size
    left = int(w * crop_left / 100)
    right = w - int(w * crop_right / 100)
    top = int(h * crop_top / 100)
    bottom = h - int(h * crop_bottom / 100)
    
    # Safety check to prevent crashing if cropped entirely
    if left >= right or top >= bottom:
        return img 
        
    return img.crop((left, top, right, bottom))

# ── Processing Functions ──
def build_pdf_bytes(edited_data, copies):
    """Generates A4 PDF using ReportLab with edited images."""
    usable_w = PAGE_W - 2 * MARGIN - (PHOTOS_PER_ROW - 1) * GAP
    adj_w = usable_w / PHOTOS_PER_ROW

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
        pdf_path = tmp_pdf.name

    c = canvas.Canvas(pdf_path, pagesize=A4)
    x_s, y_s = MARGIN, PAGE_H - MARGIN
    x, y = x_s, y_s
    row_max_h = 0
    photo_in_row = 0
    tmp_files = []

    for data in edited_data:
        img = data["img"]
        fname = os.path.splitext(data["name"])[0]

        ow, oh = img.size
        scale = min(adj_w / ow, MAX_H / oh, 1)
        fw, fh = int(ow * scale), int(oh * scale)

        img_b = ImageOps.expand(img, border=BORDER, fill="black")
        tf = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tf.close()
        img_b.save(tf.name, format="PNG", dpi=(300, 300))
        tmp_files.append(tf.name)

        for _ in range(int(copies)):
            if y - fh < MARGIN:
                c.showPage()
                x, y = x_s, y_s
                row_max_h = 0
                photo_in_row = 0

            c.drawImage(tf.name, x, y - fh, fw, fh, preserveAspectRatio=True, mask=None)
            c.setFont("Helvetica", 6)
            c.setFillColorRGB(0, 0, 0)
            c.drawString(x + 3, y - fh + 3, fname[:20])

            row_max_h = max(row_max_h, fh)
            photo_in_row += 1
            x += fw + GAP

            if photo_in_row >= PHOTOS_PER_ROW:
                x, y = x_s, y - row_max_h - GAP
                row_max_h = 0
                photo_in_row = 0

    c.save()

    for f in tmp_files:
        if os.path.exists(f):
            os.remove(f)

    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
    os.remove(pdf_path)

    return pdf_data


def build_pil_pages(edited_data, copies):
    """Generates 300 DPI PIL Image pages with edited images."""
    DPI = 300
    SCALE = DPI / 72.0 
    PAGE_W_PX, PAGE_H_PX = int(PAGE_W * SCALE), int(PAGE_H * SCALE)
    MARGIN_PX, GAP_PX = int(MARGIN * SCALE), int(GAP * SCALE)
    BORDER_PX = max(1, int(BORDER * SCALE))
    MAX_H_PX = int(MAX_H * SCALE)

    usable_w = PAGE_W_PX - 2 * MARGIN_PX - (PHOTOS_PER_ROW - 1) * GAP_PX
    adj_w = usable_w / PHOTOS_PER_ROW

    pages = []

    def create_new_page():
        return Image.new("RGB", (PAGE_W_PX, PAGE_H_PX), "white")

    current_page = create_new_page()
    draw = ImageDraw.Draw(current_page)
    x_s, y_s = MARGIN_PX, MARGIN_PX
    x, y = x_s, y_s
    row_max_h, photo_in_row = 0, 0

    try:
        font = ImageFont.truetype("arial.ttf", int(7 * SCALE))
    except OSError:
        font = ImageFont.load_default()

    for data in edited_data:
        img = data["img"]
        fname = os.path.splitext(data["name"])[0][:20]
        ow, oh = img.size

        scale = min(adj_w / ow, MAX_H_PX / oh, 1.0)
        fw, fh = int(ow * scale), int(oh * scale)

        img_b = ImageOps.expand(img, border=BORDER_PX, fill="black")
        img_b = img_b.resize((fw, fh), Image.Resampling.LANCZOS)

        for _ in range(int(copies)):
            if y + fh > PAGE_H_PX - MARGIN_PX:
                pages.append(current_page)
                current_page = create_new_page()
                draw = ImageDraw.Draw(current_page)
                x, y = x_s, y_s
                row_max_h, photo_in_row = 0, 0

            current_page.paste(img_b, (x, y))
            draw.text((x + int(4 * SCALE), y + fh - int(10 * SCALE)), fname, fill="black", font=font)

            row_max_h = max(row_max_h, fh)
            photo_in_row += 1
            x += fw + GAP_PX

            if photo_in_row >= PHOTOS_PER_ROW:
                x, y = x_s, y + row_max_h + GAP_PX
                row_max_h = 0
                photo_in_row = 0

    pages.append(current_page)
    return pages


def build_docx_bytes(pil_pages):
    """Embeds edited images into MS Word Document."""
    doc = Document()
    for section in doc.sections:
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)
        section.top_margin = Inches(0.2)
        section.bottom_margin = Inches(0.2)
        section.left_margin = Inches(0.2)
        section.right_margin = Inches(0.2)

    for i, page_img in enumerate(pil_pages):
        if i > 0:
            doc.add_page_break()

        img_io = io.BytesIO()
        page_img.save(img_io, format="JPEG", quality=95)
        img_io.seek(0)
        doc.add_picture(img_io, width=Inches(7.87))

    doc_io = io.BytesIO()
    doc.save(doc_io)
    return doc_io.getvalue()


# ── Hero ──
st.markdown(
    """
<div class="hero">
    <div class="hero-icon">📷</div>
    <h1>Photo<span>Pass</span> Pro</h1>
    <p>Upload karo, Manual Edit karo, aur PDF/JPG/WORD generate karo!</p>
    <div class="steps-row">
        <div class="step-pill"><span class="sn">1</span><span class="st">Upload Photos</span></div>
        <div class="step-pill"><span class="sn">2</span><span class="st">Manual Crop & Rotate</span></div>
        <div class="step-pill"><span class="sn">3</span><span class="st">Generate Files</span></div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="content">', unsafe_allow_html=True)

# ── Upload ──
st.markdown('<span class="sec-lbl">📁 Photos Upload Karo</span>', unsafe_allow_html=True)
uploaded_files = st.file_uploader(
    "JPG, JPEG ya PNG — Sab screen par dikhengi",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)

# ── Copies Input ──
st.markdown('<span class="sec-lbl">🔢 Har Photo Ki Copies</span>', unsafe_allow_html=True)
copies = st.number_input("copies", min_value=1, max_value=20, value=2, step=1, label_visibility="collapsed")
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Preview & Manual Edit (All Photos Displayed) ──
final_edited_data = []

if uploaded_files:
    st.markdown(
        f"""
    <div style="background:#eef2ff;border:1.5px solid #c7d2fe;border-radius:10px;
    padding:.75rem 1rem;margin-bottom:1.5rem;color:#3730a3;font-size:.9rem;font-weight:700">
        ✅ &nbsp; {len(uploaded_files)} photo(s) selected. Niche manual crop/rotate adjust karein.
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Use 3 columns to display all uploaded photos neatly
    cols = st.columns(3)
    
    for i, f in enumerate(uploaded_files):
        with cols[i % 3]:
            f.seek(0)
            orig_img = Image.open(f).convert("RGB")
            
            with st.container():
                # Edit Controls within an expander for cleanliness
                with st.expander(f"🛠️ Edit: {f.name[:12]}", expanded=True):
                    rot = st.slider("Rotate 🔄", -180, 180, 0, key=f"rot_{i}")
                    
                    colA, colB = st.columns(2)
                    with colA:
                        cl = st.slider("Crop Left %", 0, 45, 0, key=f"cl_{i}")
                        ct = st.slider("Crop Top %", 0, 45, 0, key=f"ct_{i}")
                    with colB:
                        cr = st.slider("Crop Right %", 0, 45, 0, key=f"cr_{i}")
                        cb = st.slider("Crop Bottom %", 0, 45, 0, key=f"cb_{i}")
                
                # Apply Edits in Real Time
                edited_img = apply_edits(orig_img, rot, cl, cr, ct, cb)
                final_edited_data.append({"name": f.name, "img": edited_img})
                
                # Show Preview exactly how it will be generated
                st.image(edited_img, use_container_width=True, caption=f"Preview: {f.name[:10]}")
                st.markdown("<br>", unsafe_allow_html=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Generate Action ──
if st.button("⚡ Process & Generate Final Files"):
    if not uploaded_files:
        st.error("❌ Pehle photos upload karo!")
        st.session_state.processed = False
    else:
        prog = st.progress(0)
        status = st.empty()

        def update_prog(p, msg):
            prog.progress(p, text=msg)
            status.markdown(
                f'<p style="text-align:center;color:#4338ca;font-size:.85rem;'
                f'font-weight:700;margin-top:.3rem">{msg}</p>',
                unsafe_allow_html=True,
            )

        update_prog(20, "📐 Apply ho raha hai & PDF ban raha hai...")
        st.session_state.pdf_bytes = build_pdf_bytes(final_edited_data, copies)

        update_prog(60, "🖼️ High-Res Image (JPG) layout ban raha hai...")
        st.session_state.pil_pages = build_pil_pages(final_edited_data, copies)

        update_prog(85, "📝 Word Document (.docx) generate ho raha hai...")
        st.session_state.docx_bytes = build_docx_bytes(st.session_state.pil_pages)

        update_prog(100, "✅ Sabhi Formats Ready!")
        status.empty()
        st.session_state.processed = True

# ── DOWNLOAD BUTTONS (STAYS ACTIVE) ──
if st.session_state.get("processed", False) and uploaded_files:
    st.markdown(
        """
    <div style="background:#ecfdf5;border:2px solid #059669;border-radius:12px;
    padding:.9rem 1rem;text-align:center;color:#064e3b;font-size:.95rem;
    font-weight:700;margin:1rem 0">
        🎉 Sabhi formats tayar hain! Apni pasand ka format download karein:
    </div>
    """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            label="📄 Download PDF",
            data=st.session_state.pdf_bytes,
            file_name="passport_photos.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    with col2:
        pil_pages = st.session_state.pil_pages
        if len(pil_pages) == 1:
            img_byte_arr = io.BytesIO()
            pil_pages[0].save(img_byte_arr, format="JPEG", quality=95)
            st.download_button(
                label="🖼️ Download JPG",
                data=img_byte_arr.getvalue(),
                file_name="passport_photos.jpg",
                mime="image/jpeg",
                use_container_width=True,
            )
        else:
            for idx, page_img in enumerate(pil_pages):
                img_byte_arr = io.BytesIO()
                page_img.save(img_byte_arr, format="JPEG", quality=95)
                st.download_button(
                    label=f"🖼️ JPG (Page {idx+1})",
                    data=img_byte_arr.getvalue(),
                    file_name=f"passport_photos_page_{idx+1}.jpg",
                    mime="image/jpeg",
                    key=f"jpg_btn_{idx}",
                    use_container_width=True,
                )

    with col3:
        st.download_button(
            label="📝 Download WORD",
            data=st.session_state.docx_bytes,
            file_name="passport_photos.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )

st.markdown("</div>", unsafe_allow_html=True)
