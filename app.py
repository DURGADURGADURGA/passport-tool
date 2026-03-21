import os
import io
import tempfile
import numpy as np
import streamlit as st
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
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

PASSPORT_SIZES = {
    "🇮🇳 India  (35×45 mm)": (35, 45),
    "🇺🇸 USA    (51×51 mm)": (51, 51),
    "🇬🇧 UK     (35×45 mm)": (35, 45),
    "🇦🇪 UAE    (40×60 mm)": (40, 60),
    "🇪🇺 Europe (35×45 mm)": (35, 45),
    "Custom": None,
}
MM_TO_PX_300DPI = 300 / 25.4
# ============================================

st.set_page_config(page_title="PhotoPass Pro", page_icon="📷", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&display=swap');

@keyframes fadeDown { from{opacity:0;transform:translateY(-20px)} to{opacity:1;transform:translateY(0)} }
@keyframes fadeUp   { from{opacity:0;transform:translateY(20px)}  to{opacity:1;transform:translateY(0)} }
@keyframes pulse    { 0%,100%{box-shadow:0 0 0 0 rgba(0,188,212,.4)} 50%{box-shadow:0 0 0 12px rgba(0,188,212,0)} }
@keyframes shimmer  { 0%{background-position:-600px 0} 100%{background-position:600px 0} }

html,body,[class*="css"]{ font-family:'Montserrat',sans-serif !important; }
.stApp{ background:#f0fafb; }
#MainMenu,footer,header{ visibility:hidden; }
.block-container{ padding-top:0 !important; padding-bottom:3rem; max-width:740px; }

.hero{ background:#fff; border-bottom:3px solid #00bcd4; padding:2.8rem 1.5rem 2rem;
  margin:-1rem -1rem 2rem; text-align:center; animation:fadeDown .6s ease both; }
.hero-icon{ width:76px;height:76px;background:#00bcd4;border-radius:50%;
  display:flex;align-items:center;justify-content:center;margin:0 auto 1rem;font-size:34px;
  animation:pulse 2.5s ease-in-out infinite; }
.hero h1{ font-size:clamp(1.8rem,5vw,2.8rem);font-weight:900;color:#0d0d0d;
  letter-spacing:-.02em;margin-bottom:.5rem; }
.hero h1 span{ color:#00bcd4; }
.hero p{ font-size:1rem;font-weight:600;color:#555;margin-bottom:1.4rem; }
.ai-badge{ display:inline-flex;align-items:center;gap:6px;background:#e0f7fa;
  border:1.5px solid #00bcd4;border-radius:20px;padding:5px 14px;
  font-size:.78rem;font-weight:700;color:#006064; }

.steps-row{ display:flex;justify-content:center;gap:8px;flex-wrap:wrap;margin-top:1rem; }
.step-pill{ background:#e0f7fa;border-radius:30px;padding:7px 16px;
  display:inline-flex;align-items:center;gap:7px; }
.step-pill .sn{ background:#00bcd4;color:#fff;font-size:11px;font-weight:800;
  width:22px;height:22px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center; }
.step-pill .st{ font-size:12px;font-weight:700;color:#007b8a; }

.sec-lbl{ font-size:.75rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;
  color:#00838f;margin-bottom:.5rem; }

[data-testid="stFileUploader"]{ background:#fff !important;border:2.5px dashed #00bcd4 !important;
  border-radius:16px !important;padding:2rem !important;transition:all .2s !important; }
[data-testid="stFileUploader"]:hover{ background:#e0f7fa !important; }

[data-testid="stNumberInput"] input{ background:#fff !important;border:2px solid #b2ebf2 !important;
  color:#0d0d0d !important;border-radius:10px !important;
  font-family:'Montserrat',sans-serif !important;font-size:1.3rem !important;
  font-weight:900 !important;text-align:center !important; }
[data-testid="stNumberInput"] button{ background:#00bcd4 !important;border:none !important;
  color:#fff !important;border-radius:8px !important;font-weight:900 !important; }

[data-testid="stSelectbox"]>div>div{ background:#fff !important;
  border:2px solid #b2ebf2 !important;border-radius:10px !important;
  font-family:'Montserrat',sans-serif !important;font-weight:700 !important; }

[data-testid="stImage"] img{ border-radius:10px !important;
  border:2px solid #b2ebf2 !important;transition:transform .2s !important; }
[data-testid="stImage"] img:hover{ transform:scale(1.05) !important; }

.stButton>button{ width:100% !important;background:#00bcd4 !important;color:#fff !important;
  border:none !important;border-radius:12px !important;padding:1rem 2rem !important;
  font-family:'Montserrat',sans-serif !important;font-size:1rem !important;
  font-weight:800 !important;letter-spacing:.06em !important;text-transform:uppercase !important;
  box-shadow:0 4px 16px rgba(0,188,212,.35) !important;transition:all .2s !important; }
.stButton>button:hover{ background:#0097a7 !important;transform:translateY(-2px) !important; }

[data-testid="stProgress"]>div>div{
  background:linear-gradient(90deg,#00bcd4,#4dd0e1,#00bcd4) !important;
  background-size:600px 100% !important;animation:shimmer 1.5s linear infinite !important;
  border-radius:100px !important; }
[data-testid="stProgress"]{ background:#b2ebf2 !important;border-radius:100px !important; }

[data-testid="stDownloadButton"] button{ width:100% !important;background:#00897b !important;
  color:#fff !important;border:none !important;border-radius:12px !important;
  padding:1rem 2rem !important;font-family:'Montserrat',sans-serif !important;
  font-size:1rem !important;font-weight:800 !important;letter-spacing:.06em !important;
  text-transform:uppercase !important;transition:all .2s !important; }
[data-testid="stDownloadButton"] button:hover{ background:#00695c !important;transform:translateY(-2px) !important; }

.info-section{ background:#e0f2f1;border-top:3px solid #00bcd4;padding:2rem 1rem 1.5rem;
  margin:2rem -1rem -1rem;display:flex;gap:0; }
.info-col{ flex:1;text-align:center;padding:0 10px;border-right:1px solid #b2dfdb; }
.info-col:last-child{ border-right:none; }
.info-icon-wrap{ width:52px;height:52px;background:#00bcd4;border-radius:50%;
  display:flex;align-items:center;justify-content:center;margin:0 auto 10px;font-size:22px; }
.info-col h4{ font-size:.68rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase;
  color:#0d0d0d;margin-bottom:5px; }
.info-col p{ font-size:.72rem;color:#555;font-weight:500;line-height:1.6; }

.footer-bar{ background:#00bcd4;margin:0 -1rem;padding:12px 20px;text-align:center; }
.footer-bar p{ font-size:.7rem;font-weight:700;color:#fff;letter-spacing:.12em; }

@media(max-width:600px){
  .hero{padding:2rem 1rem 1.5rem;}
  .info-section{flex-direction:column;gap:1.2rem;}
  .info-col{border-right:none;border-bottom:1px solid #b2dfdb;padding-bottom:1rem;}
  .info-col:last-child{border-bottom:none;}
}
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════
#  PROCESSING FUNCTIONS (Pillow only)
# ════════════════════════════════════

def smart_crop(img: Image.Image, target_w_mm: float, target_h_mm: float) -> Image.Image:
    """Smart center crop maintaining passport aspect ratio."""
    target_w_px = int(target_w_mm * MM_TO_PX_300DPI)
    target_h_px = int(target_h_mm * MM_TO_PX_300DPI)
    ratio = target_w_px / target_h_px

    w, h = img.size
    if w / h > ratio:
        new_w = int(h * ratio)
        x = (w - new_w) // 2
        img = img.crop((x, 0, x + new_w, h))
    else:
        new_h = int(w / ratio)
        # Shift crop slightly up — face is usually in upper portion
        y = max(0, int((h - new_h) * 0.25))
        img = img.crop((0, y, w, y + new_h))

    return img.resize((target_w_px, target_h_px), Image.LANCZOS)


def make_white_background(img: Image.Image) -> Image.Image:
    """Replace background with white using edge-based segmentation (Pillow only)."""
    img_rgba = img.convert("RGBA")
    data = np.array(img_rgba, dtype=np.float32)

    r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]

    # Simple background detection: corners are usually background
    h, w = r.shape
    corner_size = max(10, min(h, w) // 10)
    corners = np.concatenate([
        data[:corner_size, :corner_size].reshape(-1, 4),
        data[:corner_size, -corner_size:].reshape(-1, 4),
        data[-corner_size:, :corner_size].reshape(-1, 4),
        data[-corner_size:, -corner_size:].reshape(-1, 4),
    ])
    bg_color = corners[:, :3].mean(axis=0)

    # Mask pixels similar to background color
    diff = np.sqrt(((data[:,:,:3] - bg_color) ** 2).sum(axis=2))
    threshold = 60
    mask = diff < threshold

    # Apply white background
    result = data.copy()
    result[mask, 0] = 255
    result[mask, 1] = 255
    result[mask, 2] = 255

    return Image.fromarray(result.astype(np.uint8)).convert("RGB")


def enhance_hd(img: Image.Image) -> Image.Image:
    """Enhance photo quality for HD print output."""
    img = ImageEnhance.Sharpness(img).enhance(2.0)
    img = ImageEnhance.Contrast(img).enhance(1.2)
    img = ImageEnhance.Brightness(img).enhance(1.05)
    img = ImageEnhance.Color(img).enhance(1.1)
    img = img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=150, threshold=3))
    return img


def process_photo(img: Image.Image, target_w_mm: float, target_h_mm: float,
                  do_bg: bool, do_enhance: bool) -> tuple:
    log = []
    img = img.convert("RGB")
    log.append("✅ Photo loaded")

    img = smart_crop(img, target_w_mm, target_h_mm)
    log.append("✅ Smart crop — sahi ratio mein")

    if do_bg:
        img = make_white_background(img)
        log.append("✅ White background applied")

    if do_enhance:
        img = enhance_hd(img)
        log.append("✅ HD enhancement done — 300 DPI ready")

    tw = int(target_w_mm * MM_TO_PX_300DPI)
    th = int(target_h_mm * MM_TO_PX_300DPI)
    img = img.resize((tw, th), Image.LANCZOS)
    log.append(f"✅ Final: {tw}×{th}px @ 300 DPI")

    return img, log


# ════════════════════
#  UI
# ════════════════════

st.markdown("""
<div class="hero">
    <div class="hero-icon">📷</div>
    <h1>Photo<span>Pass</span> Pro</h1>
    <p>Upload karo — baaki sab automatic!</p>
    <div class="ai-badge">✨ Smart Crop · White BG · HD Quality · PDF Ready</div>
    <div class="steps-row">
        <div class="step-pill"><span class="sn">1</span><span class="st">Upload</span></div>
        <div class="step-pill"><span class="sn">2</span><span class="st">Auto Process</span></div>
        <div class="step-pill"><span class="sn">3</span><span class="st">PDF Banao</span></div>
        <div class="step-pill"><span class="sn">4</span><span class="st">Download</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

# Settings
col1, col2 = st.columns([2, 1])
with col1:
    st.markdown('<div class="sec-lbl">🌍 Country / Size</div>', unsafe_allow_html=True)
    size_choice = st.selectbox("size", list(PASSPORT_SIZES.keys()), label_visibility="collapsed")
with col2:
    st.markdown('<div class="sec-lbl">🔢 Copies</div>', unsafe_allow_html=True)
    copies = st.number_input("copies", min_value=1, max_value=20, value=2, step=1, label_visibility="collapsed")

if size_choice == "Custom":
    c1, c2 = st.columns(2)
    with c1:
        custom_w = st.number_input("Width (mm)", min_value=20, max_value=100, value=35)
    with c2:
        custom_h = st.number_input("Height (mm)", min_value=20, max_value=100, value=45)
    target_w_mm, target_h_mm = float(custom_w), float(custom_h)
else:
    target_w_mm, target_h_mm = PASSPORT_SIZES[size_choice]

# Options
st.markdown('<div class="sec-lbl" style="margin-top:.8rem">⚙️ Processing Options</div>', unsafe_allow_html=True)
col_a, col_b = st.columns(2)
with col_a:
    do_bg = st.checkbox("🎨 White Background", value=True)
with col_b:
    do_enhance = st.checkbox("⚡ HD Enhancement", value=True)

st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)

# Upload
st.markdown('<div class="sec-lbl">📁 Photos Upload Karo</div>', unsafe_allow_html=True)
uploaded_files = st.file_uploader(
    "Koi bhi photo chalegi — auto process hogi!",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
    label_visibility="collapsed"
)

if uploaded_files:
    st.markdown(f"""
    <div style="background:#e0f7fa;border:1.5px solid #80deea;border-radius:12px;
    padding:.8rem 1.2rem;margin:1rem 0;color:#006064;font-size:.9rem;font-weight:700">
        ✅ &nbsp; {len(uploaded_files)} photo(s) ready — process hogi!
    </div>
    """, unsafe_allow_html=True)
    cols = st.columns(min(len(uploaded_files), 6))
    for i, f in enumerate(uploaded_files):
        with cols[i % 6]:
            st.image(f, use_container_width=True, caption="Original")

st.markdown('<div style="height:1px;background:#b2ebf2;margin:1.5rem 0"></div>', unsafe_allow_html=True)

if st.button("✨   Process + PDF Generate Karo"):
    if not uploaded_files:
        st.error("❌ Pehle photos upload karo!")
    else:
        total = len(uploaded_files) * 3 + 3
        prog = st.progress(0)
        status = st.empty()
        step = [0]

        def adv(msg, n=1):
            step[0] += n
            prog.progress(min(int(step[0]/total*100), 95), text=msg)
            status.markdown(
                f'<p style="text-align:center;color:#00838f;font-size:.85rem;font-weight:600;margin-top:.3rem">{msg}</p>',
                unsafe_allow_html=True)

        adv("🚀 Processing shuru...")
        processed = []
        all_logs = []

        for idx, uf in enumerate(uploaded_files):
            adv(f"✂️ Photo {idx+1}/{len(uploaded_files)} process ho rahi hai...")
            raw = Image.open(uf)
            pimg, logs = process_photo(raw, target_w_mm, target_h_mm, do_bg, do_enhance)
            processed.append((pimg, os.path.splitext(uf.name)[0]))
            all_logs += [f"Photo {idx+1}: {l}" for l in logs]
            adv(f"✅ Photo {idx+1} ready!", n=2)

        # Preview processed
        st.markdown('<div class="sec-lbl" style="margin-top:1rem">✅ Processed Photos</div>', unsafe_allow_html=True)
        pcols = st.columns(min(len(processed), 6))
        for i, (pimg, pname) in enumerate(processed):
            with pcols[i % 6]:
                st.image(pimg, use_container_width=True, caption="Processed")

        with st.expander("📋 Processing Log"):
            for l in all_logs:
                st.markdown(f"<small style='color:#00838f'>{l}</small>", unsafe_allow_html=True)

        adv("📄 PDF ban raha hai...", n=1)

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

        for pimg, pname in processed:
            ow, oh = pimg.size
            scale = min(adj_w/ow, MAX_H/oh, 1)
            fw, fh = int(ow*scale), int(oh*scale)

            bordered = ImageOps.expand(pimg, border=BORDER, fill="black")
            tf = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            tf.close()
            bordered.save(tf.name, format="PNG", dpi=(300, 300))
            tmp_files.append(tf.name)

            for _ in range(int(copies)):
                if y - fh < MARGIN:
                    c.showPage()
                    x, y = x_s, y_s
                    row_max_h = 0
                    photo_in_row = 0

                c.drawImage(tf.name, x, y-fh, fw, fh, preserveAspectRatio=True, mask=None)
                c.setFont("Helvetica", 6)
                c.setFillColorRGB(0, 0, 0)
                c.drawString(x+3, y-fh+3, pname[:20])

                row_max_h = max(row_max_h, fh)
                photo_in_row += 1
                x += fw + GAP

                if photo_in_row >= PHOTOS_PER_ROW:
                    x, y = x_s, y - row_max_h - GAP
                    row_max_h = 0
                    photo_in_row = 0

        c.save()
        for f in tmp_files:
            os.remove(f)

        with open(pdf_path, "rb") as f:
            pdf_data = f.read()
        os.remove(pdf_path)

        prog.progress(100, text="✅ PDF Ready!")
        status.empty()

        st.markdown("""
        <div style="background:#e0f7fa;border:2px solid #00bcd4;border-radius:14px;
        padding:1rem 1.2rem;text-align:center;color:#006064;font-size:1rem;
        font-weight:700;margin:1rem 0">
            🎉 PDF ready hai — HD print ke liye bilkul taiyar!
        </div>
        """, unsafe_allow_html=True)

        st.download_button(
            label="⬇️   HD PDF Download Karo",
            data=pdf_data,
            file_name="photopass_pro.pdf",
            mime="application/pdf"
        )

st.markdown("""
<div class="info-section">
    <div class="info-col">
        <div class="info-icon-wrap">✂️</div>
        <h4>Smart Crop</h4>
        <p>Auto sahi ratio<br>mein crop</p>
    </div>
    <div class="info-col">
        <div class="info-icon-wrap">🎨</div>
        <h4>White BG</h4>
        <p>Background auto<br>white ho jaata</p>
    </div>
    <div class="info-col">
        <div class="info-icon-wrap">⚡</div>
        <h4>HD 300 DPI</h4>
        <p>Print bilkul<br>sharp aata</p>
    </div>
    <div class="info-col">
        <div class="info-icon-wrap">🌍</div>
        <h4>5 Countries</h4>
        <p>India, USA, UK<br>UAE, Europe</p>
    </div>
</div>
<div class="footer-bar">
    <p>PHOTOPASS PRO &nbsp;·&nbsp; FREE TO USE &nbsp;·&nbsp; NO SIGNUP REQUIRED</p>
</div>
""", unsafe_allow_html=True)
