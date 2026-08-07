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

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] {
    font-family: 'Montserrat', sans-serif !important;
    -webkit-text-size-adjust: 100%;
}
.stApp { background: #f0fafb; }
#MainMenu, footer, header { visibility: hidden; }

/* ── Layout ── */
.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}
.main > div {
    padding: 0 !important;
}

/* ── Hero ── */
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
    display: flex;
    justify-content: center;
    gap: 6px;
    flex-wrap: wrap;
    padding: 0 .5rem;
}
.step-pill {
    background: #e0f7fa;
    border-radius: 30px;
    padding: 6px 12px;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 4px;
}
.step-pill .sn {
    background: #00bcd4; color: #fff;
    font-size: 10px; font-weight: 800;
    width: 20px; height: 20px;
    border-radius: 50%;
    display: inline-flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}
.step-pill .st {
    font-size: 11px; font-weight: 700; color: #007b8a;
    white-space: nowrap;
}

/* ── Content wrapper ── */
.content {
    max-width: 700px;
    margin: 0 auto;
    padding: 1.5rem 1rem 2rem;
}

/* ── Section label ── */
.sec-lbl {
    font-size: .72rem; font-weight: 800;
    letter-spacing: .1em; text-transform: uppercase;
    color: #00838f; margin-bottom: .5rem;
    display: block;
}

/* ── Upload zone ── */
[data-testid="stFileUploader"] {
    background: #fff !important;
    border: 2.5px dashed #00bcd4 !important;
    border-radius: 14px !important;
    padding: 1.5rem 1rem !important;
    transition: all .2s !important;
    width: 100% !important;
}
[data-testid="stFileUploader"]:hover {
    background: #e0f7fa !important;
}
[data-testid="stFileUploader"] label {
    font-size: clamp(.8rem, 2vw, .95rem) !important;
    font-weight: 600 !important;
}

/* ── Number input ── */
[data-testid="stNumberInput"] {
    width: 100% !important;
}
[data-testid="stNumberInput"] input {
    background: #fff !important;
    border: 2px solid #b2ebf2 !important;
    color: #0d0d0d !important;
    border-radius: 10px !important;
    font-family: 'Montserrat', sans-serif !important;
    font-size: clamp(1rem, 3vw, 1.3rem) !important;
    font-weight: 900 !important;
    text-align: center !important;
    width: 100% !important;
    min-height: 44px !important;
}
[data-testid="stNumberInput"] button {
    background: #00bcd4 !important;
    border: none !important;
    color: #fff !important;
    border-radius: 8px !important;
    font-weight: 900 !important;
    min-width: 36px !important;
    min-height: 36px !important;
}

/* ── Preview images ── */
[data-testid="stImage"] img {
    border-radius: 8px !important;
    border: 2px solid #b2ebf2 !important;
    width: 100% !important;
    height: auto !important;
    display: block !important;
}

/* ── Primary Action Button ── */
.stButton > button {
    width: 100% !important;
    background: #00bcd4 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 12px !important;
    padding: .9rem 1rem !important;
    font-family: 'Montserrat', sans-serif !important;
    font-size: clamp(.9rem, 2.5vw, 1rem) !important;
    font-weight: 800 !important;
    letter-spacing: .05em !important;
    text-transform: uppercase !important;
    box-shadow: 0 4px 14px rgba(0,188,212,.35) !important;
    transition: all .2s !important;
    min-height: 52px !important;
    touch-action: manipulation !important;
}
.stButton > button:hover {
    background: #0097a7 !important;
    transform: translateY(-1px) !important;
}

/* ── Progress ── */
[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg,#00bcd4,#4dd0e1,#00bcd4) !important;
    background-size: 400px 100% !important;
    animation: shimmer 1.5s linear infinite !important;
    border-radius: 100px !important;
}
[data-testid="stProgress"] {
    background: #b2ebf2 !important;
    border-radius: 100px !important;
}

/* ── Download buttons ── */
[data-testid="stDownloadButton"] button {
    width: 100% !important;
    background: #00897b !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    padding: .8rem .8rem !important;
    font-family: 'Montserrat', sans-serif !important;
    font-size: clamp(.8rem, 2.2vw, .9rem) !important;
    font-weight: 800 !important;
    letter-spacing: .03em !important;
    text-transform: uppercase !important;
    min-height: 48px !important;
    touch-action: manipulation !important;
    transition: all .2s !important;
    margin-bottom: 8px !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: #00695c !important;
}

/* ── Info cards ── */
.info-section {
    background: #e0f2f1;
    border-top: 3px solid #00bcd4;
    padding: 1.8rem 1rem 1.5rem;
    margin-top: 2rem;
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    width: 100%;
}
.info-col {
    text-align: center;
    padding: 0 6px;
}
.info-icon-wrap {
    width: 48px; height: 48px;
    background: #00bcd4;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 8px;
    font-size: 20px;
}
.info-col h4 {
    font-size: .65rem; font-weight: 800;
    letter-spacing: .07em; text-transform: uppercase;
    color: #0d0d0d; margin-bottom: 4px;
}
.info-col p {
    font-size: .68rem; color: #555;
    font-weight: 500; line-height: 1.5;
}

/* ── Footer ── */
.footer-bar {
    background: #00bcd4;
    padding: 12px 16px;
    text-align: center;
    width: 100%;
}
.footer-bar p {
    font-size: .68rem; font-weight: 700;
    color: #fff; letter-spacing: .1em;
    margin: 0;
}

/* ── Divider ── */
.divider {
    height: 1px;
    background: #b2ebf2;
    margin: 1.2rem 0;
}

/* MOBILE — max 600px */
@media (max-width: 600px) {
    .hero { padding: 1.8rem 1rem 1.5rem; }
    .hero-icon { width: 60px; height: 60px; font-size: 26px; }
    .content { padding: 1.2rem .8rem 2rem; }
    .info-section { grid-template-columns: 1fr; gap: 8px; }
    .info-col {
        border-bottom: 1px solid #b2dfdb;
        padding-bottom: 10px;
        display: flex; align-items: center; gap: 12px;
        text-align: left;
    }
    .info-col:last-child { border-bottom: none; }
    .info-icon-wrap { flex-shrink: 0; margin: 0; }
    .info-col h4 { margin-bottom: 2px; }
    .info-col p { margin: 0; }
    .step-pill { padding: 5px 10px; }
    .step-pill .st { font-size: 10px; }
    .footer-bar p { font-size: .62rem; letter-spacing: .06em; }
}

@media (min-width: 601px) and (max-width: 900px) {
    .content { padding: 1.5rem 1.2rem 2rem; }
    .info-section { grid-template-columns: repeat(3, 1fr); }
}

@media (min-width: 901px) {
    .content { padding: 2rem 2rem 3rem; }
    .hero { padding: 3rem 2rem 2.2rem; }
    .info-section { padding: 2rem 2rem 1.8rem; gap: 16px; }
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

# ── Helper for Robust Font Loading ──
def get_pil_font(size):
    """Loads a sharp TrueType font across Windows, Mac, Linux, and Cloud environments."""
    font_names = [
        "arial.ttf",
        "DejaVuSans.ttf",
        "LiberationSans-Regular.ttf",
        "FreeSans.ttf",
        "Helvetica.ttf",
    ]
    for fn in font_names:
        try:
            return ImageFont.truetype(fn, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()

# ── Processing Functions ──

def build_pdf_bytes(uploaded_files, copies):
    """Generates A4 PDF using ReportLab."""
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

    for uf in uploaded_files:
        uf.seek(0)
        img = Image.open(uf).convert("RGB")
        ow, oh = img.size
        scale = min(adj_w / ow, MAX_H / oh, 1)
        fw, fh = int(ow * scale), int(oh * scale)

        img_b = ImageOps.expand(img, border=BORDER, fill="black")
        tf = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tf.close()
        img_b.save(tf.name, format="PNG", dpi=(300, 300))
        tmp_files.append(tf.name)

        fname = os.path.splitext(uf.name)[0]

        for _ in range(int(copies)):
            if y - fh < MARGIN:
                c.showPage()
                x, y = x_s, y_s
                row_max_h = 0
                photo_in_row = 0

            c.drawImage(
                tf.name,
                x,
                y - fh,
                fw,
                fh,
                preserveAspectRatio=True,
                mask=None,
            )
            c.setFont("Helvetica-Bold", 7)
            c.setFillColorRGB(0, 0, 0)
            # Bottom-left corner text placement
            c.drawString(x + 2, y - fh + 2, fname[:20])

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


def build_pil_pages(uploaded_files, copies):
    """Generates High-Res 300 DPI PIL Image pages matching A4 layout."""
    DPI = 300
    SCALE = DPI / 72.0  # Convert points to pixels

    PAGE_W_PX = int(PAGE_W * SCALE)
    PAGE_H_PX = int(PAGE_H * SCALE)
    MARGIN_PX = int(MARGIN * SCALE)
    GAP_PX = int(GAP * SCALE)
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
    row_max_h = 0
    photo_in_row = 0

    # High quality dynamic scaled font
    font_size_px = int(7.5 * SCALE)
    font = get_pil_font(font_size_px)

    for uf in uploaded_files:
        uf.seek(0)
        img = Image.open(uf).convert("RGB")
        ow, oh = img.size

        scale = min(adj_w / ow, MAX_H_PX / oh, 1.0)
        fw, fh = int(ow * scale), int(oh * scale)

        # Resize image cleanly first, then add crisp border
        img_resized = img.resize((fw - 2 * BORDER_PX, fh - 2 * BORDER_PX), Image.Resampling.LANCZOS)
        img_b = ImageOps.expand(img_resized, border=BORDER_PX, fill="black")

        fname = os.path.splitext(uf.name)[0][:20]

        for _ in range(int(copies)):
            if y + fh > PAGE_H_PX - MARGIN_PX:
                pages.append(current_page)
                current_page = create_new_page()
                draw = ImageDraw.Draw(current_page)
                x, y = x_s, y_s
                row_max_h = 0
                photo_in_row = 0

            current_page.paste(img_b, (x, y))
            
            # Bottom-left corner text placement
            text_x = x + int(2 * SCALE)
            text_y = y + fh - int(9 * SCALE)
            draw.text(
                (text_x, text_y),
                fname,
                fill="black",
                font=font,
            )

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
    """Embeds A4 PIL images into MS Word Document with exact margins."""
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
        page_img.save(img_io, format="JPEG", quality=100, subsampling=0, dpi=(300, 300))
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
    <p>Multiple logon ki photos ek saath A4 Sheet (PDF, JPG, WORD) mein arrange karo!</p>
    <div class="steps-row">
        <div class="step-pill"><span class="sn">1</span><span class="st">Upload Photos</span></div>
        <div class="step-pill"><span class="sn">2</span><span class="st">Copies Chuno</span></div>
        <div class="step-pill"><span class="sn">3</span><span class="st">Generate Karo</span></div>
        <div class="step-pill"><span class="sn">4</span><span class="st">Direct Download</span></div>
    </div>
</div>
<div class="content">
""",
    unsafe_allow_html=True,
)

# ── Upload ──
st.markdown(
    '<span class="sec-lbl">📁 Photos Upload Karo</span>', unsafe_allow_html=True
)
uploaded_files = st.file_uploader(
    "JPG, JPEG ya PNG — ek ya zyada photos chunno",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)

# ── Copies Input ──
st.markdown(
    '<span class="sec-lbl">🔢 Har Photo Ki Copies</span>', unsafe_allow_html=True
)
copies = st.number_input(
    "copies",
    min_value=1,
    max_value=20,
    value=2,
    step=1,
    label_visibility="collapsed",
)

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
            st.image(
                f, use_container_width=True, caption=f.name.split(".")[0][:8]
            )

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
                f'<p style="text-align:center;color:#00838f;font-size:.82rem;'
                f'font-weight:600;margin-top:.3rem">{msg}</p>',
                unsafe_allow_html=True,
            )

        update_prog(20, "📐 PDF layout tayar ho raha hai...")
        st.session_state.pdf_bytes = build_pdf_bytes(uploaded_files, copies)

        update_prog(60, "🖼️ High-Res Image (JPG) layout ban raha hai...")
        st.session_state.pil_pages = build_pil_pages(uploaded_files, copies)

        update_prog(85, "📝 Word Document (.docx) generate ho raha hai...")
        st.session_state.docx_bytes = build_docx_bytes(st.session_state.pil_pages)

        update_prog(100, "✅ Sabhi Formats Ready!")
        status.empty()
        st.session_state.processed = True

# ── SEPARATE DOWNLOAD BUTTONS (STAYS ACTIVE IN SESSION) ──
if st.session_state.get("processed", False) and uploaded_files:
    st.markdown(
        """
    <div style="background:#e0f7fa;border:2px solid #00bcd4;border-radius:12px;
    padding:.9rem 1rem;text-align:center;color:#006064;font-size:.95rem;
    font-weight:700;margin:1rem 0">
        🎉 Sabhi formats tayar hain! Kisi bhi format ko kitni bhi baar download karein:
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<span class="sec-lbl" style="text-align:center; font-size:0.85rem;">⬇️ Download Buttons</span>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    # 1. PDF Download
    with col1:
        st.download_button(
            label="📄 PDF Sheet",
            data=st.session_state.pdf_bytes,
            file_name="passport_photos.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    # 2. JPG Download (Ultra HD 300 DPI Export)
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

    # 3. Word Document Download
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
