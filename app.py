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
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500&display=swap');

@keyframes fadeSlideUp {
    from { opacity: 0; transform: translateY(28px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
    from { opacity: 0; }
    to   { opacity: 1; }
}
@keyframes pulse-ring {
    0%   { box-shadow: 0 0 0 0 rgba(99,102,241,0.35); }
    70%  { box-shadow: 0 0 0 10px rgba(99,102,241,0); }
    100% { box-shadow: 0 0 0 0 rgba(99,102,241,0); }
}
@keyframes shimmer {
    0%   { background-position: -400px 0; }
    100% { background-position: 400px 0; }
}
@keyframes float {
    0%,100% { transform: translateY(0px); }
    50%      { transform: translateY(-6px); }
}

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #f5f3ef; color: #1c1917; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 0rem; padding-bottom: 3rem; max-width: 700px; }

.hero-wrap {
    background: linear-gradient(160deg, #1e1b4b 0%, #312e81 45%, #4338ca 100%);
    border-radius: 0 0 32px 32px;
    padding: 3.5rem 2rem 3rem;
    margin: -1rem -1rem 2.5rem;
    text-align: center;
    animation: fadeSlideUp 0.7s ease both;
    position: relative;
    overflow: hidden;
}
.hero-wrap::before {
    content: '';
    position: absolute;
    top: -60px; left: -60px;
    width: 200px; height: 200px;
    background: rgba(255,255,255,0.04);
    border-radius: 50%;
}
.hero-icon {
    font-size: 3.2rem;
    display: inline-block;
    animation: float 3s ease-in-out infinite;
    margin-bottom: 0.8rem;
}
.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: clamp(2.4rem, 6vw, 3.8rem);
    font-weight: 900;
    color: #ffffff;
    letter-spacing: -0.02em;
    line-height: 1.1;
    margin-bottom: 0.6rem;
}
.hero-title span { color: #a5b4fc; }
.hero-sub {
    font-family: 'DM Sans', sans-serif;
    font-size: 1rem;
    color: rgba(255,255,255,0.65);
    font-weight: 300;
}

.steps-wrap {
    display: flex;
    gap: 12px;
    margin: 0 0 2rem;
    animation: fadeSlideUp 0.7s 0.15s ease both;
    flex-wrap: wrap;
}
.step {
    flex: 1;
    min-width: 130px;
    background: #ffffff;
    border: 1px solid #e7e5e4;
    border-radius: 16px;
    padding: 1.1rem 0.9rem;
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
}
.step:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,0.08); }
.step-num {
    font-family: 'Playfair Display', serif;
    font-size: 1.8rem;
    font-weight: 700;
    color: #6366f1;
    line-height: 1;
}
.step-txt { font-size: 0.76rem; color: #78716c; margin-top: 0.3rem; }

.sec-label {
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #a8a29e;
    margin-bottom: 0.5rem;
}

[data-testid="stFileUploader"] {
    background: #ffffff !important;
    border: 2px dashed #c7d2fe !important;
    border-radius: 16px !important;
    padding: 1.8rem !important;
    transition: all 0.25s !important;
    animation: fadeSlideUp 0.7s 0.25s ease both;
}
[data-testid="stFileUploader"]:hover {
    border-color: #6366f1 !important;
    background: #f5f3ff !important;
}

[data-testid="stNumberInput"] input {
    background: #ffffff !important;
    border: 1px solid #e7e5e4 !important;
    color: #1c1917 !important;
    border-radius: 12px !important;
    font-family: 'Playfair Display', serif !important;
    font-size: 1.2rem !important;
    font-weight: 700 !important;
}
[data-testid="stNumberInput"] button {
    background: #f5f3ef !important;
    border-color: #e7e5e4 !important;
    color: #6366f1 !important;
}

[data-testid="stImage"] img {
    border-radius: 12px !important;
    border: 2px solid #e7e5e4 !important;
    transition: transform 0.2s !important;
}
[data-testid="stImage"] img:hover { transform: scale(1.04) !important; }

.stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 0.9rem 2rem !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 1rem !important;
    font-weight: 500 !important;
    cursor: pointer !important;
    transition: all 0.2s !important;
    animation: pulse-ring 2.5s ease-out infinite !important;
    box-shadow: 0 4px 20px rgba(99,102,241,0.3) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 30px rgba(99,102,241,0.45) !important;
    animation: none !important;
}

[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg, #6366f1, #a78bfa, #6366f1) !important;
    background-size: 400px 100% !important;
    animation: shimmer 1.5s linear infinite !important;
    border-radius: 100px !important;
}
[data-testid="stProgress"] {
    background: #e7e5e4 !important;
    border-radius: 100px !important;
}

[data-testid="stDownloadButton"] button {
    width: 100%;
    background: linear-gradient(135deg, #059669 0%, #10b981 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 0.9rem 2rem !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 1rem !important;
    font-weight: 500 !important;
    box-shadow: 0 4px 20px rgba(16,185,129,0.3) !important;
    transition: all 0.2s !important;
}
[data-testid="stDownloadButton"] button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 30px rgba(16,185,129,0.45) !important;
}

.footer {
    text-align: center;
    color: #a8a29e;
    font-size: 0.76rem;
    margin-top: 3rem;
    border-top: 1px solid #e7e5e4;
    padding-top: 1.5rem;
    letter-spacing: 0.04em;
}

@media (max-width: 600px) {
    .hero-wrap { padding: 2.5rem 1.2rem 2rem; border-radius: 0 0 24px 24px; }
    .steps-wrap { gap: 8px; }
    .step { min-width: 100px; padding: 0.8rem 0.5rem; }
    .block-container { padding: 0 0.5rem 2rem; }
}
</style>
""", unsafe_allow_html=True)

# ── Hero ──
st.markdown("""
<div class="hero-wrap">
    <div class="hero-icon">📷</div>
    <div class="hero-title">Photo<span>Pass</span> Pro</div>
    <div class="hero-sub">Multiple passport photos — ek saath A4 PDF mein</div>
</div>
""", unsafe_allow_html=True)

# ── Steps ──
st.markdown("""
<div class="steps-wrap">
    <div class="step"><div class="step-num">01</div><div class="step-txt">Photos Upload karo</div></div>
    <div class="step"><div class="step-num">02</div><div class="step-txt">Copies chunno</div></div>
    <div class="step"><div class="step-num">03</div><div class="step-txt">PDF Generate karo</div></div>
    <div class="step"><div class="step-num">04</div><div class="step-txt">Download karo</div></div>
</div>
""", unsafe_allow_html=True)

# ── Upload ──
st.markdown('<div class="sec-label">📁 Photos Upload karo</div>', unsafe_allow_html=True)
uploaded_files = st.file_uploader(
    "JPG, JPEG ya PNG — ek ya zyada photos chunno",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
    label_visibility="collapsed"
)

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# ── Copies ──
st.markdown('<div class="sec-label">🔢 Har photo ki copies</div>', unsafe_allow_html=True)
copies = st.number_input(
    "copies", min_value=1, max_value=20, value=2, step=1,
    label_visibility="collapsed"
)

# ── Preview ──
if uploaded_files:
    st.markdown(f"""
    <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;
    padding:0.7rem 1rem;margin:1rem 0;color:#166534;font-size:0.9rem;
    animation:fadeSlideUp 0.4s ease both">
        ✅ &nbsp;<strong>{len(uploaded_files)}</strong> photo(s) select ki gayi
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(min(len(uploaded_files), 6))
    for i, file in enumerate(uploaded_files):
        with cols[i % 6]:
            st.image(file, use_container_width=True, caption=file.name.split(".")[0][:10])

st.markdown('<div style="height:1px;background:#e7e5e4;margin:1.5rem 0"></div>', unsafe_allow_html=True)

# ── Generate ──
if st.button("🖨️  PDF Generate Karo"):
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
                f'<p style="text-align:center;color:#78716c;font-size:0.85rem;margin-top:0.3rem">{msg}</p>',
                unsafe_allow_html=True
            )

        advance("📐 Canvas tayar ho raha hai...")

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
            advance(f"🖼️ Photo {idx+1}/{len(uploaded_files)} — {uploaded_file.name[:18]}...")

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

        progress_bar.progress(100, text="✅ Taiyar!")
        status.empty()

        st.markdown("""
        <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:14px;
        padding:1rem 1.2rem;text-align:center;color:#166534;font-size:1rem;
        margin:1rem 0;animation:fadeSlideUp 0.4s ease both">
            🎉 PDF successfully ban gayi! Neeche se download karo.
        </div>
        """, unsafe_allow_html=True)

        st.download_button(
            label="⬇️  PDF Download Karo",
            data=pdf_data,
            file_name="passport_photos.pdf",
            mime="application/pdf"
        )

# ── Footer ──
st.markdown("""
<div class="footer">
    Made with ❤️ &nbsp;·&nbsp; PhotoPass Pro &nbsp;·&nbsp; Free to use
</div>
""", unsafe_allow_html=True)
