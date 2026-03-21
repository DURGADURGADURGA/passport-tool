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
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
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

/* ── Generate button ── */
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
.stButton > button:active {
    transform: translateY(0) !important;
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

/* ── Download button ── */
[data-testid="stDownloadButton"] button {
    width: 100% !important;
    background: #00897b !important;
    color: #fff !important;
    border: none !important;
    border-radius: 12px !important;
    padding: .9rem 1rem !important;
    font-family: 'Montserrat', sans-serif !important;
    font-size: clamp(.9rem, 2.5vw, 1rem) !important;
    font-weight: 800 !important;
    letter-spacing: .05em !important;
    text-transform: uppercase !important;
    min-height: 52px !important;
    touch-action: manipulation !important;
    transition: all .2s !important;
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

/* ══════════════════════════════
   MOBILE — max 600px
══════════════════════════════ */
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

/* ══════════════════════════════
   TABLET — 601px to 900px
══════════════════════════════ */
@media (min-width: 601px) and (max-width: 900px) {
    .content { padding: 1.5rem 1.2rem 2rem; }
    .info-section { grid-template-columns: repeat(3, 1fr); }
}

/* ══════════════════════════════
   PC — min 901px
══════════════════════════════ */
@media (min-width: 901px) {
    .content { padding: 2rem 2rem 3rem; }
    .hero { padding: 3rem 2rem 2.2rem; }
    .info-section { padding: 2rem 2rem 1.8rem; gap: 16px; }
}
</style>
""", unsafe_allow_html=True)

# ── Hero ──
st.markdown("""
<div class="hero">
    <div class="hero-icon">📷</div>
    <h1>Photo<span>Pass</span> Pro</h1>
    <p>Multiple logon ki photos ek saath A4 PDF mein arrange karo!</p>
    <div class="steps-row">
        <div class="step-pill"><span class="sn">1</span><span class="st">Upload Photos</span></div>
        <div class="step-pill"><span class="sn">2</span><span class="st">Copies Chuno</span></div>
        <div class="step-pill"><span class="sn">3</span><span class="st">PDF Banao</span></div>
        <div class="step-pill"><span class="sn">4</span><span class="st">Download Karo</span></div>
    </div>
</div>
<div class="content">
""", unsafe_allow_html=True)

# ── Upload ──
st.markdown('<span class="sec-lbl">📁 Photos Upload Karo</span>', unsafe_allow_html=True)
uploaded_files = st.file_uploader(
    "JPG, JPEG ya PNG — ek ya zyada photos chunno",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
    label_visibility="collapsed"
)

st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)

# ── Copies ──
st.markdown('<span class="sec-lbl">🔢 Har Photo Ki Copies</span>', unsafe_allow_html=True)
copies = st.number_input(
    "copies", min_value=1, max_value=20, value=2, step=1,
    label_visibility="collapsed"
)

# ── Preview ──
if uploaded_files:
    st.markdown(f"""
    <div style="background:#e0f7fa;border:1.5px solid #80deea;border-radius:10px;
    padding:.75rem 1rem;margin:.8rem 0;color:#006064;font-size:.88rem;font-weight:700">
        ✅ &nbsp; {len(uploaded_files)} photo(s) select ki gayi hain
    </div>
    """, unsafe_allow_html=True)

    num_cols = min(len(uploaded_files), 4)
    cols = st.columns(num_cols)
    for i, f in enumerate(uploaded_files):
        with cols[i % num_cols]:
            st.image(f, use_container_width=True, caption=f.name.split(".")[0][:8])

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Generate Button ──
if st.button("🖨️   PDF Generate Karo"):
    if not uploaded_files:
        st.error("❌ Pehle photos upload karo!")
    else:
        total = len(uploaded_files) + 3
        prog = st.progress(0)
        status = st.empty()
        step = [0]

        def adv(msg, n=1):
            step[0] += n
            prog.progress(min(int(step[0]/total*100), 95), text=msg)
            status.markdown(
                f'<p style="text-align:center;color:#00838f;font-size:.82rem;'
                f'font-weight:600;margin-top:.3rem">{msg}</p>',
                unsafe_allow_html=True)

        adv("📐 PDF canvas tayar ho raha hai...")

        usable_w = PAGE_W - 2*MARGIN - (PHOTOS_PER_ROW-1)*GAP
        adj_w = usable_w / PHOTOS_PER_ROW

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
            pdf_path = tmp_pdf.name

        c = canvas.Canvas(pdf_path, pagesize=A4)
        x_s, y_s = MARGIN, PAGE_H - MARGIN
        x, y = x_s, y_s
        row_max_h = 0
        photo_in_row = 0
        tmp_files = []

        for idx, uf in enumerate(uploaded_files):
            adv(f"🖼️ Photo {idx+1}/{len(uploaded_files)} process ho rahi hai...")

            img = Image.open(uf).convert("RGB")
            ow, oh = img.size
            scale = min(adj_w/ow, MAX_H/oh, 1)
            fw, fh = int(ow*scale), int(oh*scale)

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

                c.drawImage(tf.name, x, y-fh, fw, fh, preserveAspectRatio=True, mask=None)
                c.setFont("Helvetica", 6)
                c.setFillColorRGB(0, 0, 0)
                c.drawString(x+3, y-fh+3, fname[:20])

                row_max_h = max(row_max_h, fh)
                photo_in_row += 1
                x += fw + GAP

                if photo_in_row >= PHOTOS_PER_ROW:
                    x, y = x_s, y - row_max_h - GAP
                    row_max_h = 0
                    photo_in_row = 0

        adv("💾 PDF save ho raha hai...", n=1)
        c.save()

        for f in tmp_files:
            os.remove(f)
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()
        os.remove(pdf_path)

        prog.progress(100, text="✅ PDF Ready!")
        status.empty()

        st.markdown("""
        <div style="background:#e0f7fa;border:2px solid #00bcd4;border-radius:12px;
        padding:.9rem 1rem;text-align:center;color:#006064;font-size:.95rem;
        font-weight:700;margin:1rem 0">
            🎉 PDF ready hai — print ke liye bilkul taiyar!
        </div>
        """, unsafe_allow_html=True)

        st.download_button(
            label="⬇️   PDF Download Karo",
            data=pdf_data,
            file_name="passport_photos.pdf",
            mime="application/pdf"
        )

st.markdown("</div>", unsafe_allow_html=True)

# ── Info + Footer ──
st.markdown("""
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
            <h4>A4 PDF Ready</h4>
            <p>Print ke liye bilkul taiyar</p>
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
""", unsafe_allow_html=True)
