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
from streamlit_cropper import st_cropper  # VISUAL CROP TOOL

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
    layout="centered", # Wapas chota kar diya (Centered Layout)
    initial_sidebar_state="collapsed",
)

# ── Updated Design (Compact) ──
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Montserrat', sans-serif !important;
}
.stApp { background: #f8fafc; }
#MainMenu, footer, header { visibility: hidden; }

/* ── Hero Compact ── */
.hero {
    background: #ffffff;
    border-bottom: 3px solid #3b82f6;
    padding: 1.5rem 1rem 1rem;
    text-align: center;
    width: 100%;
    border-radius: 0 0 16px 16px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    margin-bottom: 1.5rem;
}
.hero-icon {
    width: 50px; height: 50px;
    background: #3b82f6;
    color: white;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto .5rem;
    font-size: 24px;
}
.hero h1 {
    font-size: 1.8rem;
    font-weight: 900;
    color: #0f172a;
    margin-bottom: .2rem;
}
.hero h1 span { color: #3b82f6; }
.hero p {
    font-size: 0.85rem;
    font-weight: 600;
    color: #475569;
    margin-bottom: 0;
}

/* ── Content wrapper ── */
.content {
    max-width: 650px;
    margin: 0 auto;
    padding: 0.5rem;
}

.sec-lbl {
    font-size: .75rem; font-weight: 800;
    letter-spacing: .1em; text-transform: uppercase;
    color: #1d4ed8; margin-bottom: .5rem;
    display: block;
}

/* ── Upload & Buttons ── */
[data-testid="stFileUploader"] {
    border: 2px dashed #3b82f6 !important;
    border-radius: 12px !important;
    padding: 1rem !important;
}

.stButton > button {
    width: 100% !important;
    border-radius: 8px !important;
    font-weight: 800 !important;
    text-transform: uppercase !important;
}

/* Edit Button Specific */
.edit-btn > button {
    background: #e2e8f0 !important;
    color: #0f172a !important;
    border: 1px solid #cbd5e1 !important;
    padding: 0.3rem !important;
    font-size: 0.75rem !important;
    min-height: 32px !important;
}
.edit-btn > button:hover {
    background: #cbd5e1 !important;
}

/* Main Generate Button */
.gen-btn > button {
    background: #3b82f6 !important;
    color: #fff !important;
    padding: .8rem !important;
    box-shadow: 0 4px 10px rgba(59,130,246,.3) !important;
}
.gen-btn > button:hover { background: #2563eb !important; }

/* Download Buttons */
[data-testid="stDownloadButton"] button {
    background: #10b981 !important;
    color: white !important;
    font-size: 0.8rem !important;
    padding: 0.6rem !important;
}

.divider {
    height: 1px;
    background: #e2e8f0;
    margin: 1.2rem 0;
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

if "edited_images" not in st.session_state:
    st.session_state.edited_images = {}

# ── Popup Editor Dialog ──
@st.dialog("✂️ Photo Editor (Crop & Rotate)", width="large")
def photo_editor_dialog(file_name, file_obj):
    st.write("🔄 **1. Rotate Image (Agar zaroorat ho):**")
    rot = st.slider("Rotate Angle", -180, 180, 0, label_visibility="collapsed")
    
    # Original load karke rotate karna
    file_obj.seek(0)
    img_to_edit = Image.open(file_obj).convert("RGB")
    if rot != 0:
        img_to_edit = img_to_edit.rotate(-rot, expand=True, fillcolor="white")
        
    st.write("✂️ **2. Box banakar crop karein:**")
    # Streamlit cropper for visual selection
    cropped_img = st_cropper(
        img_to_edit, 
        realtime_update=True, 
        box_color='#3b82f6', 
        aspect_ratio=None # Free crop
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("✅ Done & Save", type="primary", use_container_width=True):
        # Save to session state and close dialog
        st.session_state.edited_images[file_name] = cropped_img
        st.rerun()

# ── Processing Functions ──
def build_pdf_bytes(edited_data, copies):
    usable_w = PAGE_W - 2 * MARGIN - (PHOTOS_PER_ROW - 1) * GAP
    adj_w = usable_w / PHOTOS_PER_ROW
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
        pdf_path = tmp_pdf.name
    c = canvas.Canvas(pdf_path, pagesize=A4)
    x_s, y_s = MARGIN, PAGE_H - MARGIN
    x, y = x_s, y_s
    row_max_h, photo_in_row = 0, 0
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
                row_max_h, photo_in_row = 0, 0

            c.drawImage(tf.name, x, y - fh, fw, fh, preserveAspectRatio=True, mask=None)
            c.setFont("Helvetica", 6)
            c.setFillColorRGB(0, 0, 0)
            c.drawString(x + 3, y - fh + 3, fname[:20])

            row_max_h = max(row_max_h, fh)
            photo_in_row += 1
            x += fw + GAP
            if photo_in_row >= PHOTOS_PER_ROW:
                x, y = x_s, y - row_max_h - GAP
                row_max_h, photo_in_row = 0, 0
    c.save()
    for f in tmp_files:
        if os.path.exists(f): os.remove(f)
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
    os.remove(pdf_path)
    return pdf_data

def build_pil_pages(edited_data, copies):
    DPI = 300
    SCALE = DPI / 72.0 
    PAGE_W_PX, PAGE_H_PX = int(PAGE_W * SCALE), int(PAGE_H * SCALE)
    MARGIN_PX, GAP_PX = int(MARGIN * SCALE), int(GAP * SCALE)
    BORDER_PX = max(1, int(BORDER * SCALE))
    MAX_H_PX = int(MAX_H * SCALE)

    usable_w = PAGE_W_PX - 2 * MARGIN_PX - (PHOTOS_PER_ROW - 1) * GAP_PX
    adj_w = usable_w / PHOTOS_PER_ROW
    pages = []
    def create_new_page(): return Image.new("RGB", (PAGE_W_PX, PAGE_H_PX), "white")
    current_page = create_new_page()
    draw = ImageDraw.Draw(current_page)
    x_s, y_s = MARGIN_PX, MARGIN_PX
    x, y = x_s, y_s
    row_max_h, photo_in_row = 0, 0

    try: font = ImageFont.truetype("arial.ttf", int(7 * SCALE))
    except OSError: font = ImageFont.load_default()

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
                row_max_h, photo_in_row = 0, 0

    pages.append(current_page)
    return pages

def build_docx_bytes(pil_pages):
    doc = Document()
    for section in doc.sections:
        section.page_width, section.page_height = Inches(8.27), Inches(11.69)
        section.top_margin = section.bottom_margin = Inches(0.2)
        section.left_margin = section.right_margin = Inches(0.2)
    for i, page_img in enumerate(pil_pages):
        if i > 0: doc.add_page_break()
        img_io = io.BytesIO()
        page_img.save(img_io, format="JPEG", quality=95)
        img_io.seek(0)
        doc.add_picture(img_io, width=Inches(7.87))
    doc_io = io.BytesIO()
    doc.save(doc_io)
    return doc_io.getvalue()


# ── UI ──
st.markdown(
    """
<div class="hero">
    <div class="hero-icon">📷</div>
    <h1>Photo<span>Pass</span> Pro</h1>
    <p>Compact layout. Popup Crop/Rotate edit. All Formats Ready.</p>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="content">', unsafe_allow_html=True)

# ── Upload ──
st.markdown('<span class="sec-lbl">📁 Photos Upload Karo</span>', unsafe_allow_html=True)
uploaded_files = st.file_uploader(
    "JPG/PNG files choose karein",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
st.markdown('<span class="sec-lbl">🔢 Har Photo Ki Copies</span>', unsafe_allow_html=True)
copies = st.number_input("copies", min_value=1, max_value=20, value=2, step=1, label_visibility="collapsed")
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)


final_edited_data = []

# ── Display & Edit Images ──
if uploaded_files:
    # 1. Update Session state with new images, remove deleted ones
    current_names = [f.name for f in uploaded_files]
    keys_to_remove = [k for k in st.session_state.edited_images.keys() if k not in current_names]
    for k in keys_to_remove:
        del st.session_state.edited_images[k]
        
    for f in uploaded_files:
        if f.name not in st.session_state.edited_images:
            f.seek(0)
            st.session_state.edited_images[f.name] = Image.open(f).convert("RGB")
    
    st.markdown('<span class="sec-lbl">🖼️ Photo Preview & Edit (Click to Crop)</span>', unsafe_allow_html=True)
    
    # 2. Display in smaller columns
    cols = st.columns(3)
    for i, f in enumerate(uploaded_files):
        with cols[i % 3]:
            # Show the currently saved state of the image
            display_img = st.session_state.edited_images[f.name]
            st.image(display_img, use_container_width=True)
            
            # Button opens Dialog
            st.markdown('<div class="edit-btn">', unsafe_allow_html=True)
            if st.button("✏️ Edit Photo", key=f"edit_{f.name}", use_container_width=True):
                photo_editor_dialog(f.name, f)
            st.markdown('</div><br>', unsafe_allow_html=True)
            
            final_edited_data.append({"name": f.name, "img": display_img})

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Generate Buttons ──
st.markdown('<div class="gen-btn">', unsafe_allow_html=True)
if st.button("⚡ Generate Files (PDF / JPG / WORD)"):
    if not uploaded_files:
        st.error("❌ Pehle photos upload karo!")
        st.session_state.processed = False
    else:
        prog = st.progress(0)
        status = st.empty()
        
        prog.progress(20, text="📐 PDF ban raha hai...")
        st.session_state.pdf_bytes = build_pdf_bytes(final_edited_data, copies)

        prog.progress(60, text="🖼️ High-Res Image ban rahi hai...")
        st.session_state.pil_pages = build_pil_pages(final_edited_data, copies)

        prog.progress(85, text="📝 Word Document ban raha hai...")
        st.session_state.docx_bytes = build_docx_bytes(st.session_state.pil_pages)

        prog.progress(100, text="✅ Sabhi Formats Ready!")
        st.session_state.processed = True
st.markdown('</div>', unsafe_allow_html=True)


# ── Downloads ──
if st.session_state.get("processed", False) and uploaded_files:
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)

    with c1:
        st.download_button(
            label="📄 PDF",
            data=st.session_state.pdf_bytes,
            file_name="passport_photos.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    with c2:
        pil_pages = st.session_state.pil_pages
        if len(pil_pages) == 1:
            img_byte_arr = io.BytesIO()
            pil_pages[0].save(img_byte_arr, format="JPEG", quality=95)
            st.download_button(
                label="🖼️ JPG",
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
                    label=f"🖼️ JPG (P{idx+1})",
                    data=img_byte_arr.getvalue(),
                    file_name=f"passport_photos_page_{idx+1}.jpg",
                    mime="image/jpeg",
                    key=f"jpg_btn_{idx}",
                    use_container_width=True,
                )

    with c3:
        st.download_button(
            label="📝 WORD",
            data=st.session_state.docx_bytes,
            file_name="passport_photos.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )

st.markdown("</div>", unsafe_allow_html=True)
