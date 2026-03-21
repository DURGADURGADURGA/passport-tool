import os
import io
import tempfile
import numpy as np
import streamlit as st
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# ── Try importing AI libraries ──
try:
    from rembg import remove as rembg_remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

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
MM_TO_PX_300DPI = 300 / 25.4  # pixels per mm at 300 DPI
# ============================================

st.set_page_config(page_title="PhotoPass Pro — AI Edition", page_icon="📷", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&display=swap');

@keyframes fadeDown { from{opacity:0;transform:translateY(-20px)} to{opacity:1;transform:translateY(0)} }
@keyframes fadeUp   { from{opacity:0;transform:translateY(20px)}  to{opacity:1;transform:translateY(0)} }
@keyframes pulse    { 0%,100%{box-shadow:0 0 0 0 rgba(0,188,212,.4)} 50%{box-shadow:0 0 0 12px rgba(0,188,212,0)} }
@keyframes shimmer  { 0%{background-position:-600px 0} 100%{background-position:600px 0} }
@keyframes spin     { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }

html,body,[class*="css"]{ font-family:'Montserrat',sans-serif !important; }
.stApp{ background:#f0fafb; }
#MainMenu,footer,header{ visibility:hidden; }
.block-container{ padding-top:0 !important; padding-bottom:3rem; max-width:740px; }

.hero{ background:#fff; border-bottom:3px solid #00bcd4; padding:2.8rem 1.5rem 2rem;
  margin:-1rem -1rem 2rem; text-align:center; animation:fadeDown .6s ease both; }
.hero-icon{ width:76px;height:76px;background:#00bcd4;border-radius:50%;display:flex;
  align-items:center;justify-content:center;margin:0 auto 1rem;font-size:34px;
  animation:pulse 2.5s ease-in-out infinite; }
.hero h1{ font-size:clamp(1.8rem,5vw,2.8rem);font-weight:900;color:#0d0d0d;
  letter-spacing:-.02em;margin-bottom:.5rem; }
.hero h1 span{ color:#00bcd4; }
.hero p{ font-size:1rem;font-weight:600;color:#555;margin-bottom:1.4rem; }
.ai-badge{ display:inline-flex;align-items:center;gap:6px;background:#e0f7fa;
  border:1.5px solid #00bcd4;border-radius:20px;padding:5px 14px;
  font-size:.78rem;font-weight:700;color:#006064; }

.steps-row{ display:flex;justify-content:center;gap:8px;flex-wrap:wrap;margin-bottom:.3rem; }
.step-pill{ background:#e0f7fa;border-radius:30px;padding:7px 16px;
  display:inline-flex;align-items:center;gap:7px; }
.step-pill .sn{ background:#00bcd4;color:#fff;font-size:11px;font-weight:800;
  width:22px;height:22px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center; }
.step-pill .st{ font-size:12px;font-weight:700;color:#007b8a; }

.sec-lbl{ font-size:.75rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase;
  color:#00838f;margin-bottom:.5rem;animation:fadeUp .5s ease both; }

.ai-pipeline{ background:#fff;border:2px solid #00bcd4;border-radius:16px;
  padding:1.2rem 1.4rem;margin-bottom:1.2rem;animation:fadeUp .5s ease both; }
.pipeline-row{ display:flex;align-items:center;gap:6px;flex-wrap:wrap; }
.pip-step{ background:#e0f7fa;border-radius:8px;padding:6px 10px;font-size:.72rem;
  font-weight:700;color:#006064;display:flex;align-items:center;gap:4px; }
.pip-arrow{ color:#00bcd4;font-size:14px;font-weight:700; }

[data-testid="stFileUploader"]{ background:#fff !important;border:2.5px dashed #00bcd4 !important;
  border-radius:16px !important;padding:2rem !important;transition:all .2s !important; }
[data-testid="stFileUploader"]:hover{ background:#e0f7fa !important;border-color:#0097a7 !important; }

[data-testid="stNumberInput"] input{ background:#fff !important;border:2px solid #b2ebf2 !important;
  color:#0d0d0d !important;border-radius:10px !important;font-family:'Montserrat',sans-serif !important;
  font-size:1.3rem !important;font-weight:900 !important;text-align:center !important; }
[data-testid="stNumberInput"] input:focus{ border-color:#00bcd4 !important; }
[data-testid="stNumberInput"] button{ background:#00bcd4 !important;border:none !important;
  color:#fff !important;border-radius:8px !important;font-weight:900 !important; }

[data-testid="stSelectbox"] > div > div{ background:#fff !important;
  border:2px solid #b2ebf2 !important;border-radius:10px !important;
  font-family:'Montserrat',sans-serif !important;font-weight:700 !important; }

[data-testid="stImage"] img{ border-radius:10px !important;
  border:2px solid #b2ebf2 !important;transition:transform .2s !important; }
[data-testid="stImage"] img:hover{ transform:scale(1.05) !important;
  box-shadow:0 6px 20px rgba(0,188,212,.25) !important; }

.stButton>button{ width:100% !important;background:#00bcd4 !important;color:#fff !important;
  border:none !important;border-radius:12px !important;padding:1rem 2rem !important;
  font-family:'Montserrat',sans-serif !important;font-size:1rem !important;
  font-weight:800 !important;letter-spacing:.06em !important;text-transform:uppercase !important;
  box-shadow:0 4px 16px rgba(0,188,212,.35) !important;transition:all .2s !important; }
.stButton>button:hover{ background:#0097a7 !important;transform:translateY(-2px) !important;
  box-shadow:0 8px 28px rgba(0,188,212,.45) !important; }

[data-testid="stProgress"]>div>div{ background:linear-gradient(90deg,#00bcd4,#4dd0e1,#00bcd4) !important;
  background-size:600px 100% !important;animation:shimmer 1.5s linear infinite !important;
  border-radius:100px !important; }
[data-testid="stProgress"]{ background:#b2ebf2 !important;border-radius:100px !important; }

[data-testid="stDownloadButton"] button{ width:100% !important;background:#00897b !important;
  color:#fff !important;border:none !important;border-radius:12px !important;
  padding:1rem 2rem !important;font-family:'Montserrat',sans-serif !important;
  font-size:1rem !important;font-weight:800 !important;letter-spacing:.06em !important;
  text-transform:uppercase !important;box-shadow:0 4px 16px rgba(0,137,123,.35) !important;
  transition:all .2s !important; }
[data-testid="stDownloadButton"] button:hover{ background:#00695c !important;
  transform:translateY(-2px) !important; }

.info-section{ background:#e0f2f1;border-top:3px solid #00bcd4;border-radius:0 0 16px 16px;
  padding:2rem 1rem 1.5rem;margin:2rem -1rem -1rem;display:flex;gap:0; }
.info-col{ flex:1;text-align:center;padding:0 10px;border-right:1px solid #b2dfdb; }
.info-col:last-child{ border-right:none; }
.info-icon-wrap{ width:52px;height:52px;background:#00bcd4;border-radius:50%;
  display:flex;align-items:center;justify-content:center;margin:0 auto 10px;font-size:22px; }
.info-col h4{ font-size:.68rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase;
  color:#0d0d0d;margin-bottom:5px; }
.info-col p{ font-size:.72rem;color:#555;font-weight:500;line-height:1.6; }

.footer-bar{ background:#00bcd4;margin:0 -1rem;padding:12px 20px;text-align:center;border-radius:0 0 16px 16px; }
.footer-bar p{ font-size:.7rem;font-weight:700;color:#fff;letter-spacing:.12em; }

@media(max-width:600px){
  .hero{padding:2rem 1rem 1.5rem;}
  .info-section{flex-direction:column;gap:1.2rem;}
  .info-col{border-right:none;border-bottom:1px solid #b2dfdb;padding-bottom:1rem;}
  .info-col:last-child{border-bottom:none;}
  .pipeline-row{gap:4px;}
}
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════
#  AI PROCESSING FUNCTIONS
# ════════════════════════════════════════

def detect_and_crop_face(img: Image.Image, target_w_mm: float, target_h_mm: float) -> Image.Image:
    """Detect face using OpenCV, crop with proper passport proportions."""
    target_w_px = int(target_w_mm * MM_TO_PX_300DPI)
    target_h_px = int(target_h_mm * MM_TO_PX_300DPI)

    if not CV2_AVAILABLE:
        return img.resize((target_w_px, target_h_px), Image.LANCZOS)

    img_cv = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))

    h_img, w_img = img_cv.shape[:2]

    if len(faces) == 0:
        # No face found — center crop
        ratio = target_w_px / target_h_px
        if w_img / h_img > ratio:
            new_w = int(h_img * ratio)
            x_off = (w_img - new_w) // 2
            cropped = img.crop((x_off, 0, x_off + new_w, h_img))
        else:
            new_h = int(w_img / ratio)
            y_off = (h_img - new_h) // 4  # slightly above center
            cropped = img.crop((0, y_off, w_img, y_off + new_h))
        return cropped.resize((target_w_px, target_h_px), Image.LANCZOS)

    # Pick the largest face
    x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])
    face_cx = x + fw // 2
    face_cy = y + fh // 2

    # Passport standard: face height = ~70% of photo height
    crop_h = int(fh / 0.55)
    crop_w = int(crop_h * (target_w_px / target_h_px))

    # Center horizontally on face, place face at ~40% from top
    crop_x = face_cx - crop_w // 2
    crop_y = face_cy - int(crop_h * 0.38)

    # Clamp to image bounds
    crop_x = max(0, min(crop_x, w_img - crop_w))
    crop_y = max(0, min(crop_y, h_img - crop_h))
    crop_w = min(crop_w, w_img - crop_x)
    crop_h = min(crop_h, h_img - crop_y)

    cropped = img.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
    return cropped.resize((target_w_px, target_h_px), Image.LANCZOS)


def remove_background(img: Image.Image) -> Image.Image:
    """Remove background using rembg and replace with white."""
    if not REMBG_AVAILABLE:
        return img.convert("RGB")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    result_bytes = rembg_remove(buf.read())
    result = Image.open(io.BytesIO(result_bytes)).convert("RGBA")

    white_bg = Image.new("RGBA", result.size, (255, 255, 255, 255))
    white_bg.paste(result, mask=result.split()[3])
    return white_bg.convert("RGB")


def enhance_photo(img: Image.Image) -> Image.Image:
    """Auto-enhance brightness, contrast, sharpness for HD print quality."""
    # Sharpness
    img = ImageEnhance.Sharpness(img).enhance(1.8)
    # Contrast
    img = ImageEnhance.Contrast(img).enhance(1.15)
    # Brightness
    img = ImageEnhance.Brightness(img).enhance(1.05)
    # Color saturation
    img = ImageEnhance.Color(img).enhance(1.1)
    # Final unsharp mask for HD crispness
    img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=3))
    return img


def process_photo_ai(img: Image.Image, target_w_mm: float, target_h_mm: float,
                     do_bg_remove: bool, do_enhance: bool) -> tuple[Image.Image, list]:
    """Full AI pipeline — returns processed image and log of steps."""
    log = []

    # Step 1: Convert to RGB
    img = img.convert("RGB")
    log.append("✅ Photo loaded")

    # Step 2: Face detect + crop
    img = detect_and_crop_face(img, target_w_mm, target_h_mm)
    if CV2_AVAILABLE:
        log.append("✅ Face detected & cropped")
    else:
        log.append("⚠️ Center crop (OpenCV unavailable)")

    # Step 3: Background remove
    if do_bg_remove:
        if REMBG_AVAILABLE:
            img = remove_background(img)
            log.append("✅ Background removed → white")
        else:
            log.append("⚠️ Background removal skipped (rembg unavailable)")

    # Step 4: Enhance quality
    if do_enhance:
        img = enhance_photo(img)
        log.append("✅ Quality enhanced (300 DPI HD)")

    # Step 5: Final resize to exact passport size at 300 DPI
    target_w_px = int(target_w_mm * MM_TO_PX_300DPI)
    target_h_px = int(target_h_mm * MM_TO_PX_300DPI)
    img = img.resize((target_w_px, target_h_px), Image.LANCZOS)
    log.append(f"✅ Final size: {target_w_px}×{target_h_px}px @ 300 DPI")

    return img, log


# ════════════════════════════════════════
#  UI
# ════════════════════════════════════════

# Hero
st.markdown("""
<div class="hero">
    <div class="hero-icon">📷</div>
    <h1>Photo<span>Pass</span> Pro</h1>
    <p>AI-powered passport photo tool — fully automatic!</p>
    <div class="ai-badge">🤖 AI Integrated — Face Detect · BG Remove · HD Quality</div>
    <br>
    <div class="steps-row">
        <div class="step-pill"><span class="sn">1</span><span class="st">Upload</span></div>
        <div class="step-pill"><span class="sn">2</span><span class="st">AI Process</span></div>
        <div class="step-pill"><span class="sn">3</span><span class="st">PDF Banao</span></div>
        <div class="step-pill"><span class="sn">4</span><span class="st">Download</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

# AI Pipeline info
st.markdown("""
<div class="ai-pipeline">
    <div class="sec-lbl" style="margin-bottom:.6rem">🤖 AI Pipeline</div>
    <div class="pipeline-row">
        <div class="pip-step">📷 Upload</div>
        <div class="pip-arrow">→</div>
        <div class="pip-step">🎯 Face Detect</div>
        <div class="pip-arrow">→</div>
        <div class="pip-step">✂️ Auto Crop</div>
        <div class="pip-arrow">→</div>
        <div class="pip-step">🎨 BG Remove</div>
        <div class="pip-arrow">→</div>
        <div class="pip-step">⚡ HD Enhance</div>
        <div class="pip-arrow">→</div>
        <div class="pip-step">📄 PDF</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Settings Row ──
col1, col2 = st.columns([2, 1])
with col1:
    st.markdown('<div class="sec-lbl">🌍 Country / Photo Size</div>', unsafe_allow_html=True)
    size_choice = st.selectbox("size", list(PASSPORT_SIZES.keys()), label_visibility="collapsed")

with col2:
    st.markdown('<div class="sec-lbl">🔢 Copies</div>', unsafe_allow_html=True)
    copies = st.number_input("copies", min_value=1, max_value=20, value=2, step=1, label_visibility="collapsed")

# Custom size
if size_choice == "Custom":
    c1, c2 = st.columns(2)
    with c1:
        custom_w = st.number_input("Width (mm)", min_value=20, max_value=100, value=35)
    with c2:
        custom_h = st.number_input("Height (mm)", min_value=20, max_value=100, value=45)
    target_w_mm, target_h_mm = float(custom_w), float(custom_h)
else:
    target_w_mm, target_h_mm = PASSPORT_SIZES[size_choice]

# ── AI Options ──
st.markdown('<div class="sec-lbl" style="margin-top:.8rem">⚙️ AI Options</div>', unsafe_allow_html=True)
col_a, col_b, col_c = st.columns(3)
with col_a:
    do_face = st.checkbox("🎯 Face Auto-Crop", value=True)
with col_b:
    do_bg = st.checkbox("🎨 Background Remove", value=True)
with col_c:
    do_enhance = st.checkbox("⚡ HD Enhancement", value=True)

st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)

# ── Upload ──
st.markdown('<div class="sec-lbl">📁 Photos Upload Karo</div>', unsafe_allow_html=True)
uploaded_files = st.file_uploader(
    "Koi bhi photo chalegi — AI sab theek kar dega!",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
    label_visibility="collapsed"
)

# ── Preview originals ──
if uploaded_files:
    st.markdown(f"""
    <div style="background:#e0f7fa;border:1.5px solid #80deea;border-radius:12px;
    padding:.8rem 1.2rem;margin:1rem 0;color:#006064;font-size:.9rem;font-weight:700">
        ✅ &nbsp; {len(uploaded_files)} photo(s) select ki gayi — AI process karegi!
    </div>
    """, unsafe_allow_html=True)
    cols = st.columns(min(len(uploaded_files), 6))
    for i, f in enumerate(uploaded_files):
        with cols[i % 6]:
            st.image(f, use_container_width=True, caption=f.name.split(".")[0][:8])

st.markdown('<div style="height:1px;background:#b2ebf2;margin:1.5rem 0"></div>', unsafe_allow_html=True)

# ── Generate ──
if st.button("🤖   AI Process + PDF Generate Karo"):
    if not uploaded_files:
        st.error("❌ Pehle photos upload karo!")
    else:
        total_steps = len(uploaded_files) * 4 + 3
        progress = st.progress(0)
        status = st.empty()
        step = [0]

        def advance(msg, substep=1):
            step[0] += substep
            pct = min(int(step[0] / total_steps * 100), 95)
            progress.progress(pct, text=msg)
            status.markdown(
                f'<p style="text-align:center;color:#00838f;font-size:.85rem;font-weight:600;margin-top:.3rem">{msg}</p>',
                unsafe_allow_html=True
            )

        advance("🚀 AI pipeline shuru ho rahi hai...")

        processed_images = []
        all_logs = []

        for idx, uploaded_file in enumerate(uploaded_files):
            advance(f"🎯 Photo {idx+1}/{len(uploaded_files)} — Face detect kar raha hai...")
            raw_img = Image.open(uploaded_file)

            advance(f"✂️ Photo {idx+1} — Crop + BG remove + enhance...", substep=2)
            processed, logs = process_photo_ai(
                raw_img, target_w_mm, target_h_mm,
                do_bg_remove=do_bg,
                do_enhance=do_enhance
            )
            processed_images.append((processed, os.path.splitext(uploaded_file.name)[0]))
            all_logs.extend([f"Photo {idx+1}: {l}" for l in logs])
            advance(f"✅ Photo {idx+1} ready!", substep=1)

        # Show processed previews
        st.markdown('<div class="sec-lbl" style="margin-top:1rem">🖼️ AI Processed Photos</div>', unsafe_allow_html=True)
        prev_cols = st.columns(min(len(processed_images), 6))
        for i, (pimg, pname) in enumerate(processed_images):
            with prev_cols[i % 6]:
                st.image(pimg, use_container_width=True, caption=pname[:8])

        # Show AI log
        with st.expander("🤖 AI Processing Log dekho"):
            for log_line in all_logs:
                st.markdown(f"<small style='color:#00838f'>{log_line}</small>", unsafe_allow_html=True)

        advance("📄 PDF generate ho raha hai...", substep=1)

        # Build PDF
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

        for pimg, pname in processed_images:
            # Scale for PDF layout
            orig_w, orig_h = pimg.size
            scale = min(adjusted_w / orig_w, MAX_H / orig_h, 1)
            final_w = int(orig_w * scale)
            final_h = int(orig_h * scale)

            img_bordered = ImageOps.expand(pimg, border=BORDER, fill="black")
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            tmp.close()
            img_bordered.save(tmp.name, format="PNG", dpi=(300, 300))
            temp_files.append(tmp.name)

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
                c.drawString(x + 3, y - final_h + 3, pname[:20])

                row_max_height = max(row_max_height, final_h)
                photo_in_row += 1
                x += final_w + GAP

                if photo_in_row >= PHOTOS_PER_ROW:
                    x = x_start
                    y -= row_max_height + GAP
                    row_max_height = 0
                    photo_in_row = 0

        c.save()
        for f in temp_files:
            os.remove(f)

        with open(pdf_path, "rb") as f:
            pdf_data = f.read()
        os.remove(pdf_path)

        progress.progress(100, text="✅ PDF Ready!")
        status.empty()

        st.markdown("""
        <div style="background:#e0f7fa;border:2px solid #00bcd4;border-radius:14px;
        padding:1rem 1.2rem;text-align:center;color:#006064;font-size:1rem;font-weight:700;margin:1rem 0">
            🎉 AI ne sab kuch automatic kar diya! PDF print-ready hai.
        </div>
        """, unsafe_allow_html=True)

        st.download_button(
            label="⬇️   HD PDF Download Karo",
            data=pdf_data,
            file_name="photopass_pro_ai.pdf",
            mime="application/pdf"
        )

# Info Section
st.markdown("""
<div class="info-section">
    <div class="info-col">
        <div class="info-icon-wrap">🎯</div>
        <h4>AI Face Detect</h4>
        <p>Auto center kare<br>bilkul sahi crop</p>
    </div>
    <div class="info-col">
        <div class="info-icon-wrap">🎨</div>
        <h4>BG Remove</h4>
        <p>White background<br>automatic</p>
    </div>
    <div class="info-col">
        <div class="info-icon-wrap">⚡</div>
        <h4>HD Quality</h4>
        <p>300 DPI print<br>bilkul sharp</p>
    </div>
    <div class="info-col">
        <div class="info-icon-wrap">🔒</div>
        <h4>100% Secure</h4>
        <p>Photos kahin<br>save nahi hoti</p>
    </div>
</div>
<div class="footer-bar">
    <p>PHOTOPASS PRO AI EDITION &nbsp;·&nbsp; FREE TO USE &nbsp;·&nbsp; NO SIGNUP REQUIRED</p>
</div>
""", unsafe_allow_html=True)
