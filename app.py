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
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&display=swap');

/* ── Animations ── */
@keyframes fadeDown {
    from { opacity: 0; transform: translateY(-20px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(0,188,212,0.4); }
    50%       { box-shadow: 0 0 0 10px rgba(0,188,212,0); }
}
@keyframes shimmer {
    0%   { background-position: -600px 0; }
    100% { background-position: 600px 0; }
}

/* ── Global ── */
html, body, [class*="css"] {
    font-family: 'Montserrat', sans-serif !important;
}
.stApp { background: #f0fafb; }
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding-top: 0 !important;
    padding-bottom: 3rem;
    max-width: 720px;
}

/* ── Hero Banner ── */
.hero {
    background: #ffffff;
    border-bottom: 3px solid #00bcd4;
    padding: 2.8rem 1.5rem 2rem;
    text-align: center;
    margin: -1rem -1rem 2rem;
    animation: fadeDown 0.6s ease both;
}
.hero-icon-wrap {
    width: 72px;
    height: 72px;
    background: #00bcd4;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 1rem;
    font-size: 32px;
    animation: pulse 2.5s ease-in-out infinite;
}
.hero h1 {
    font-size: clamp(1.8rem, 5vw, 2.8rem);
    font-weight: 900;
    color: #0d0d0d;
    letter-spacing: -0.02em;
    margin-bottom: 0.5rem;
}
.hero h1 span { color: #00bcd4; }
.hero p {
    font-size: 1rem;
    font-weight: 600;
    color: #555;
    margin-bottom: 1.5rem;
}

/* ── Step Pills ── */
.steps-row {
    display: flex;
    justify-content: center;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 0.5rem;
}
.step-pill {
    background: #e0f7fa;
    border-radius: 30px;
    padding: 7px 16px;
    display: inline-flex;
    align-items: center;
    gap: 7px;
}
.step-pill .sn {
    background: #00bcd4;
    color: #fff;
    font-size: 11px;
    font-weight: 800;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}
.step-pill .st {
    font-size: 12px;
    font-weight: 700;
    color: #007b8a;
}

/* ── Section Labels ── */
.sec-lbl {
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #00838f;
    margin-bottom: 0.5rem;
    animation: fadeUp 0.5s ease both;
}

/* ── Upload Zone ── */
[data-testid="stFileUploader"] {
    background: #ffffff !important;
    border: 2.5px dashed #00bcd4 !important;
    border-radius: 16px !important;
    padding: 2rem !important;
    text-align: center !important;
    transition: all 0.2s !important;
    animation: fadeUp 0.5s 0.1s ease both;
}
[data-testid="stFileUploader"]:hover {
    background: #e0f7fa !important;
    border-color: #0097a7 !important;
}
[data-testid="stFileUploader"] label {
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 600 !important;
    color: #555 !important;
}

/* ── Number Input ── */
[data-testid="stNumberInput"] input {
    background: #ffffff !important;
    border: 2px solid #b2ebf2 !important;
    color: #0d0d0d !important;
    border-radius: 10px !important;
    font-family: 'Montserrat', sans-serif !important;
    font-size: 1.3rem !important;
    font-weight: 900 !important;
    text-align: center !important;
}
[data-testid="stNumberInput"] input:focus {
    border-color: #00bcd4 !important;
}
[data-testid="stNumberInput"] button {
    background: #00bcd4 !important;
    border: none !important;
    color: #fff !important;
    border-radius: 8px !important;
    font-weight: 900 !important;
    font-size: 1.1rem !important;
}

/* ── Preview images ── */
[data-testid="stImage"] img {
    border-radius: 10px !important;
    border: 2px solid #b2ebf2 !important;
    transition: transform 0.2s, box-shadow 0.2s !important;
}
[data-testid="stImage"] img:hover {
    transform: scale(1.05) !important;
    box-shadow: 0 6px 20px rgba(0,188,212,0.25) !important;
}

/* ── Generate Button ── */
.stButton > button {
    width: 100% !important;
    background: #00bcd4 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 1rem 2rem !important;
    font-family: 'Montserrat', sans-serif !important;
    font-size: 1rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    cursor: pointer !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 16px rgba(0,188,212,0.35) !important;
}
.stButton > button:hover {
    background: #0097a7 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px rgba(0,188,212,0.45) !important;
}

/* ── Progress Bar ── */
[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg, #00bcd4, #4dd0e1, #00bcd4) !important;
    background-size: 600px 100% !important;
    animation: shimmer 1.5s linear infinite !important;
    border-radius: 100px !important;
}
[data-testid="stProgress"] {
    background: #b2ebf2 !important;
    border-radius: 100px !important;
}

/* ── Download Button ── */
[data-testid="stDownloadButton"] button {
    width: 100% !important;
    background: #00897b !important;
    color: #fff !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 1rem 2rem !important;
    font-family: 'Montserrat', sans-serif !important;
    font-size: 1rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    box-shadow: 0 4px 16px rgba(0,137,123,0.35) !important;
    transition: all 0.2s !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: #00695c !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px rgba(0,137,123,0.45) !important;
}

/* ── Info Cards ── */
.info-section {
    background: #e0f2f1;
    border-top: 3px solid #00bcd4;
    border-radius: 0 0 16px 16px;
    padding: 2rem 1rem 1.5rem;
    margin: 2rem -1rem -1rem;
    display: flex;
    gap: 0;
}
.info-col {
    flex: 1;
    text-align: center;
    padding: 0 10px;
    border-right: 1px solid #b2dfdb;
}
.info-col:last-child { border-right: none; }
.info-icon-wrap {
    width: 52px;
    height: 52px;
    background: #00bcd4;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 10px;
    font-size: 22px;
}
.info-col h4 {
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #0d0d0d;
    margin-bottom: 5px;
}
.info-col p {
    font-size: 0.72rem;
    color: #555;
    font-weight: 500;
    line-height: 1.6;
}

/* ── Footer Bar ── */
.footer-bar {
    background: #00bcd4;
    margin: 0 -1rem;
    padding: 12px 20px;
    text-align: center;
    border-radius: 0 0 16px 16px;
}
.footer-bar p {
    font-size: 0.7rem;
    font-weight: 700;
    color: #fff;
    letter-spacing: 0.12em;
}

/* ── White card wrapper ── */
.content-card {
    background: #ffffff;
    border-radius: 16px;
    padding: 1.5rem 1.5rem;
    margin-bottom: 1.2rem;
    border: 1.5px solid #b2ebf2;
    animation: fadeUp 0.5s ease both;
}

/* ── Mobile ── */
@media (max-width: 600px) {
    .hero { padding: 2rem 1rem 1.5rem; }
    .info-section { flex-direction: column; gap: 1.2rem; }
    .info-col { border-right: none; border-bottom: 1px solid #b2dfdb; padding-bottom: 1rem; }
    .info-col:last-child { border-bottom: none; }
    .steps-row { gap: 6px; }
    .step-pill { padding: 5px 10px; }
}
</style>
""", unsafe_allow_html=True)

# ── Hero ──
st.markdown("""
<div class="hero">
    <div class="hero-icon-wrap">📷</div>
    <h1>Photo<span>Pass</span> Pro</h1>
    <p>Multiple logon ki photos ek saath A4 PDF mein arrange karo!</p>
    <div class="steps-row">
        <div class="step-pill"><span class="sn">1</span><span class="st">Upload Photos</span></div>
        <div class="step-pill"><span class="sn">2</span><span class="st">Copies Chuno</span></div>
        <div class="step-pill"><span class="sn">3</span><span class="st">PDF Banao</span></div>
        <div class="step-pill"><span class="sn">4</span><span class="st">Download Karo</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Upload ──
st.markdown('<div class="sec-lbl">📁 Photos Upload Karo</div>', unsafe_allow_html=True)
uploaded_files = st.file_uploader(
    "JPG, JPEG ya PNG — ek ya zyada photos chunno",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
    label_visibility="collapsed"
)

st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)

# ── Copies ──
st.markdown('<div class="sec-lbl">🔢 Har Photo Ki Copies</div>', unsafe_allow_html=True)
copies = st.number_input(
    "copies", min_value=1, max_value=20, value=2, step=1,
    label_visibility="collapsed"
)

# ── Preview ──
if uploaded_files:
    st.markdown(f"""
    <div style="background:#e0f7fa;border:1.5px solid #80deea;border-radius:12px;
    padding:0.8rem 1.2rem;margin:1rem 0;color:#006064;font-size:0.9rem;font-weight:700;
    animation:fadeUp 0.4s ease both">
        ✅ &nbsp; {len(uploaded_files)} photo(s) select ki gayi hain
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(min(len(uploaded_files), 6))
    for i, file in enumerate(uploaded_files):
        with cols[i % 6]:
            st.image(file, use_container_width=True, caption=file.name.split(".")[0][:10])

st.markdown('<div style="height:1px;background:#b2ebf2;margin:1.5rem 0"></div>', unsafe_allow_html=True)

# ── Generate ──
if st.button("🖨️   PDF Generate Karo"):
    if not uploaded_files:
        st.error("❌ Pehle photos upload karo!")
    else:
        progress_bar = st.progress(0, text="Shuru ho raha hai...")
        status = st.empty()
        total = len(uploaded_files) + 3
        step = [0]

        def advance(msg):
            step[0] += 1
            pct = min(int((step[0] / total) * 100), 95)
            progress_bar.progress(pct, text=msg)
            status.markdown(
                f'<p style="text-align:center;color:#00838f;font-size:0.85rem;'
                f'font-weight:600;margin-top:0.4rem">{msg}</p>',
                unsafe_allow_html=True
            )

        advance("📐 PDF canvas tayar ho raha hai...")

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
            advance(f"🖼️ Photo {idx+1}/{len(uploaded_files)} process ho rahi hai...")

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

        advance("💾 PDF save ho raha hai...")
        c.save()

        for f in temp_files:
            os.remove(f)

        with open(pdf_path, "rb") as f:
            pdf_data = f.read()
        os.remove(pdf_path)

        progress_bar.progress(100, text="✅ PDF Taiyar Hai!")
        status.empty()

        st.markdown("""
        <div style="background:#e0f7fa;border:2px solid #00bcd4;border-radius:14px;
        padding:1rem 1.2rem;text-align:center;color:#006064;font-size:1rem;
        font-weight:700;margin:1rem 0;animation:fadeUp 0.4s ease both">
            🎉 &nbsp; PDF successfully ban gayi! Neeche se download karo.
        </div>
        """, unsafe_allow_html=True)

        st.download_button(
            label="⬇️   PDF Download Karo",
            data=pdf_data,
            file_name="passport_photos.pdf",
            mime="application/pdf"
        )

# ── Info Section ──
st.markdown("""
<div class="info-section">
    <div class="info-col">
        <div class="info-icon-wrap">⚡</div>
        <h4>Fast & Free</h4>
        <p>Koi signup<br>nahi chahiye</p>
    </div>
    <div class="info-col">
        <div class="info-icon-wrap">🖨️</div>
        <h4>A4 PDF Ready</h4>
        <p>Print ke liye<br>bilkul taiyar</p>
    </div>
    <div class="info-col">
        <div class="info-icon-wrap">🔒</div>
        <h4>100% Secure</h4>
        <p>Photos kahin<br>save nahi hoti</p>
    </div>
</div>
<div class="footer-bar">
    <p>PHOTOPASS PRO &nbsp;·&nbsp; FREE TO USE &nbsp;·&nbsp; NO SIGNUP REQUIRED</p>
</div>
""", unsafe_allow_html=True)
