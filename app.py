import os
import tempfile
import streamlit as st
from PIL import Image, ImageOps
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

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
    layout="centered"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Inter:wght@300;400;500&display=swap');

    /* ── Global Reset ── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: #0a0a0f;
        color: #e8e8f0;
    }

    /* Hide default streamlit elements */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 720px;
    }

    /* ── Hero Header ── */
    .hero {
        text-align: center;
        padding: 3rem 1rem 2rem;
        position: relative;
    }
    .hero-badge {
        display: inline-block;
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 1px solid #2a2a4a;
        color: #7c83fd;
        font-family: 'Inter', sans-serif;
        font-size: 0.72rem;
        font-weight: 500;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        padding: 0.4rem 1rem;
        border-radius: 100px;
        margin-bottom: 1.2rem;
    }
    .hero-title {
        font-family: 'Syne', sans-serif;
        font-size: clamp(2.2rem, 6vw, 3.4rem);
        font-weight: 800;
        line-height: 1.1;
        background: linear-gradient(135deg, #ffffff 0%, #a8b4ff 50%, #7c83fd 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.8rem;
    }
    .hero-sub {
        font-size: 1rem;
        color: #6b7280;
        font-weight: 300;
        letter-spacing: 0.01em;
    }

    /* ── Divider ── */
    .custom-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #2a2a4a, transparent);
        margin: 2rem 0;
    }

    /* ── Step Cards ── */
    .steps-row {
        display: flex;
        gap: 1rem;
        margin: 1.5rem 0;
        flex-wrap: wrap;
    }
    .step-card {
        flex: 1;
        min-width: 140px;
        background: #111118;
        border: 1px solid #1e1e30;
        border-radius: 14px;
        padding: 1.2rem 1rem;
        text-align: center;
        transition: border-color 0.2s;
    }
    .step-card:hover { border-color: #3a3a6a; }
    .step-num {
        font-family: 'Syne', sans-serif;
        font-size: 1.6rem;
        font-weight: 800;
        color: #7c83fd;
        line-height: 1;
    }
    .step-label {
        font-size: 0.78rem;
        color: #6b7280;
        margin-top: 0.4rem;
        font-weight: 400;
    }

    /* ── Upload Zone ── */
    [data-testid="stFileUploader"] {
        background: #111118 !important;
        border: 2px dashed #2a2a4a !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        transition: border-color 0.2s !important;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #7c83fd !important;
    }
    [data-testid="stFileUploader"] label {
        color: #9ca3af !important;
        font-size: 0.9rem !important;
    }

    /* ── Number Input ── */
    .section-label {
        font-family: 'Syne', sans-serif;
        font-size: 0.82rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #4b5563;
        margin-bottom: 0.5rem;
    }
    [data-testid="stNumberInput"] input {
        background: #111118 !important;
        border: 1px solid #2a2a4a !important;
        color: #e8e8f0 !important;
        border-radius: 10px !important;
        font-family: 'Syne', sans-serif !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
    }
    [data-testid="stNumberInput"] button {
        background: #1a1a2e !important;
        border-color: #2a2a4a !important;
        color: #7c83fd !important;
    }

    /* ── Preview Images ── */
    .preview-header {
        font-family: 'Syne', sans-serif;
        font-size: 0.82rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #4b5563;
        margin: 1.5rem 0 0.8rem;
    }
    [data-testid="stImage"] img {
        border-radius: 10px !important;
        border: 1px solid #1e1e30 !important;
    }

    /* ── Success Alert ── */
    [data-testid="stAlert"] {
        background: #0d1f0d !important;
        border: 1px solid #1a3a1a !important;
        border-radius: 12px !important;
        color: #4ade80 !important;
    }

    /* ── Generate Button ── */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #4f46e5, #7c83fd) !important;
        color: white !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 0.85rem 2rem !important;
        font-family: 'Syne', sans-serif !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.03em !important;
        cursor: pointer !important;
        transition: all 0.2s !important;
        box-shadow: 0 4px 24px rgba(124, 131, 253, 0.25) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 32px rgba(124, 131, 253, 0.4) !important;
    }
    .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* ── Progress Bar ── */
    [data-testid="stProgress"] > div > div {
        background: linear-gradient(90deg, #4f46e5, #7c83fd) !important;
        border-radius: 100px !important;
    }
    [data-testid="stProgress"] {
        background: #1a1a2e !important;
        border-radius: 100px !important;
    }

    /* ── Spinner ── */
    .stSpinner > div {
        border-top-color: #7c83fd !important;
    }

    /* ── Download Button ── */
    [data-testid="stDownloadButton"] button {
        width: 100%;
        background: linear-gradient(135deg, #065f46, #059669) !important;
        color: white !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 0.85rem 2rem !important;
        font-family: 'Syne', sans-serif !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.03em !important;
        box-shadow: 0 4px 24px rgba(5, 150, 105, 0.25) !important;
        transition: all 0.2s !important;
    }
    [data-testid="stDownloadButton"] button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 32px rgba(5, 150, 105, 0.4) !important;
    }

    /* ── Footer ── */
    .custom-footer {
        text-align: center;
        color: #374151;
        font-size: 0.75rem;
        margin-top: 3rem;
        padding-top: 1.5rem;
        border-top: 1px solid #1a1a2e;
        letter-spacing: 0.05em;
    }

    /* ── Mobile Responsive ── */
    @media (max-width: 640px) {
        .block-container { padding: 1rem 0.75rem 2rem; }
        .hero { padding: 1.5rem 0.5rem 1rem; }
        .steps-row { gap: 0.6rem; }
        .step-card { padding: 0.9rem 0.6rem; min-width: 100px; }
    }
</style>
""", unsafe_allow_html=True)

# ── Hero ──
st.markdown("""
<div class="hero">
    <div class="hero-badge">📷 Passport Photo Tool</div>
    <div class="hero-title">PhotoPass Pro</div>
    <div class="hero-sub">Multiple logon ki photos ek saath A4 PDF mein — fast & free</div>
</div>
""", unsafe_allow_html=True)

# ── Steps ──
st.markdown("""
<div class="steps-row">
    <div class="step-card"><div class="step-num">01</div><div class="step-label">Photos Upload karo</div></div>
    <div class="step-card"><div class="step-num">02</div><div class="step-label">Copies chunno</div></div>
    <div class="step-card"><div class="step-num">03</div><div class="step-label">PDF Generate karo</div></div>
    <div class="step-card"><div class="step-num">04</div><div class="step-label">Download karo</div></div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

# ── Upload ──
st.markdown('<div class="section-label">📁 Photos Upload karo</div>', unsafe_allow_html=True)
uploaded_files = st.file_uploader(
    "JPG, JPEG ya PNG — ek ya zyada photos",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
    label_visibility="collapsed"
)

st.markdown('<div style="height:1.2rem"></div>', unsafe_allow_html=True)

# ── Copies ──
st.markdown('<div class="section-label">🔢 Har photo ki copies</div>', unsafe_allow_html=True)
copies = st.number_input(
    "copies",
    min_value=1, max_value=20, value=2, step=1,
    label_visibility="collapsed"
)

# ── Preview ──
if uploaded_files:
    st.markdown(f'<div class="preview-header">✅ {len(uploaded_files)} photo(s) selected</div>', unsafe_allow_html=True)
    cols = st.columns(min(len(uploaded_files), 6))
    for i, file in enumerate(uploaded_files):
        with cols[i % 6]:
            st.image(file, use_container_width=True, caption=file.name.split(".")[0][:8])

st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

# ── Generate ──
if st.button("🖨️  PDF Generate Karo"):
    if not uploaded_files:
        st.error("❌ Pehle photos upload karo!")
    else:
        progress_bar = st.progress(0, text="Taiyari ho rahi hai...")
        status = st.empty()

        total_steps = len(uploaded_files) + 3
        step = 0

        def advance(msg):
            global step
            step += 1
            pct = min(int((step / total_steps) * 100), 95)
            progress_bar.progress(pct, text=msg)
            status.markdown(f'<p style="color:#6b7280;font-size:0.85rem;text-align:center">{msg}</p>', unsafe_allow_html=True)

        advance("PDF canvas tayar ho raha hai...")

        usable_width = PAGE_W - 2 * MARGIN - (PHOTOS_PER_ROW - 1) * GAP
        adjusted_w = usable_width / PHOTOS_PER_ROW

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as pdf_tmp:
            pdf_path = pdf_tmp.name

        c = canvas.Canvas(pdf_path, pagesize=A4)
        x_start = MARGIN
        y_start = PAGE_H - MARGIN
        x, y = x_start, y_start
        row_max_height = 0
        photo_in_row = 0
        temp_files = []

        for idx, uploaded_file in enumerate(uploaded_files):
            advance(f"Photo {idx+1}/{len(uploaded_files)} process ho rahi hai: {uploaded_file.name[:20]}...")

            img = Image.open(uploaded_file).convert("RGB")
            orig_w, orig_h = img.size
            scale = min(adjusted_w / orig_w, MAX_H / orig_h, 1)
            final_w = int(orig_w * scale)
            final_h = int(orig_h * scale)

            img_with_border = ImageOps.expand(img, border=BORDER, fill="black")
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            tmp.close()
            img_with_border.save(tmp.name, format="PNG", dpi=(300, 300))
            temp_files.append(tmp.name)

            file_name = os.path.splitext(uploaded_file.name)[0]

            for _ in range(int(copies)):
                if y - final_h < MARGIN:
                    c.showPage()
                    x, y = x_start, y_start
                    row_max_height = 0
                    photo_in_row = 0

                c.drawImage(tmp.name, x, y - final_h, final_w, final_h,
                            preserveAspectRatio=True, mask=None)
                c.setFont("Helvetica", 6)
                c.setFillColorRGB(0, 0, 0)
                c.drawString(x + 3, y - final_h + 3, file_name)

                row_max_height = max(row_max_height, final_h)
                photo_in_row += 1
                x += final_w + GAP

                if photo_in_row >= PHOTOS_PER_ROW:
                    x = x_start
                    y -= row_max_height + GAP
                    row_max_height = 0
                    photo_in_row = 0

        advance("PDF save ho raha hai...")
        c.save()

        for f in temp_files:
            os.remove(f)

        with open(pdf_path, "rb") as f:
            pdf_data = f.read()
        os.remove(pdf_path)

        progress_bar.progress(100, text="✅ PDF ready hai!")
        status.empty()

        st.success("🎉 PDF successfully ban gayi!")
        st.download_button(
            label="⬇️  PDF Download Karo",
            data=pdf_data,
            file_name="passport_photos.pdf",
            mime="application/pdf"
        )

# ── Footer ──
st.markdown("""
<div class="custom-footer">
    Made with ❤️ &nbsp;·&nbsp; PhotoPass Pro &nbsp;·&nbsp; Free to use
</div>
""", unsafe_allow_html=True)
