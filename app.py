import io
import os
import tempfile
import cv2
import numpy as np
import docx
from docx import Document
from docx.shared import Inches
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import streamlit as st

# ================= PAGE CONFIG & COMPACT CSS =================
st.set_page_config(page_title="PhotoPass Pro Studio", page_icon="📸", layout="wide")

st.markdown("""
<style>
    /* Make UI Compact */
    .stApp { background: #f8f9fa; }
    h1 { font-size: 1.8rem !important; margin-bottom: 0 !important; color: #1f2937; }
    p { font-size: 0.9rem !important; color: #4b5563; }
    .stButton>button { border-radius: 6px !important; font-weight: bold !important; }
    /* Compact uploader */
    [data-testid="stFileUploader"] { padding: 1rem !important; min-height: auto !important; }
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] button { font-size: 0.9rem; font-weight: 600; }
    hr { margin: 1em 0; }
</style>
""", unsafe_allow_html=True)

# ================= SESSION STATE INIT =================
if "images_data" not in st.session_state:
    st.session_state.images_data = {}  # Format: {filename: {"original": PIL, "edited": PIL}}
if "processed" not in st.session_state:
    st.session_state.processed = False

# ================= AI FACE CROP FUNCTION =================
def ai_face_crop(pil_img, target_w_cm, target_h_cm):
    """Detects face using OpenCV and crops to target aspect ratio."""
    img_cv = np.array(pil_img.convert('RGB'))
    gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
    
    # Load OpenCV default face detector
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    
    if len(faces) == 0:
        return None # No face found
    
    x, y, w, h = faces[0]
    aspect_ratio = target_w_cm / target_h_cm
    
    # Calculate crop box (make it larger than just the face)
    box_width = int(w * 2.2) 
    box_height = int(box_width / aspect_ratio)
    
    center_x = x + w // 2
    center_y = int(y + h * 0.4) # Slightly above center to leave space for shoulders
    
    left = max(0, center_x - box_width // 2)
    top = max(0, center_y - box_height // 2)
    right = min(img_cv.shape[1], left + box_width)
    bottom = min(img_cv.shape[0], top + box_height)
    
    return pil_img.crop((left, top, right, bottom))

# ================= SIDEBAR SETTINGS =================
with st.sidebar:
    st.markdown("### ⚙️ Sheet Settings")
    
    format_choice = st.selectbox(
        "Photo Size (Format)", 
        ["Indian Passport (3.5 x 4.5 cm)", "US Visa (2 x 2 inch)", "PAN Card (2.5 x 3.5 cm)"]
    )
    
    # Set dimensions based on choice
    if "Indian" in format_choice:
        PHOTO_W_CM, PHOTO_H_CM = 3.5, 4.5
    elif "US" in format_choice:
        PHOTO_W_CM, PHOTO_H_CM = 5.1, 5.1 # 2 inches
    else:
        PHOTO_W_CM, PHOTO_H_CM = 2.5, 3.5
        
    copies = st.number_input("Copies per photo", min_value=1, max_value=30, value=6)
    st.markdown("---")
    st.markdown("<div style='font-size:0.8rem; color:gray;'>Bina quality loss ke PDF, JPG aur Word generate karta hai.</div>", unsafe_allow_html=True)

# ================= MAIN UI =================
st.title("📸 PhotoPass Pro Studio")
st.markdown("Professional Passport Photo Maker with AI Auto-Crop & Manual Editing")

# Uploader
uploaded_files = st.file_uploader("Upload Photos (JPG, PNG)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    # Update Session State with new files
    current_filenames = [f.name for f in uploaded_files]
    
    # Remove deleted files from state
    keys_to_remove = [k for k in st.session_state.images_data.keys() if k not in current_filenames]
    for k in keys_to_remove:
        del st.session_state.images_data[k]
        
    # Add new files to state
    for uf in uploaded_files:
        if uf.name not in st.session_state.images_data:
            uf.seek(0)
            img = Image.open(uf).convert("RGB")
            st.session_state.images_data[uf.name] = {"original": img, "edited": img.copy()}

    # Tabs for Workflow
    tab1, tab2 = st.tabs(["🎨 1. Edit Photos", "🖨️ 2. Generate & Download"])
    
    # -------- TAB 1: EDITOR --------
    with tab1:
        if not st.session_state.images_data:
            st.info("Please upload photos to start editing.")
        else:
            col_sel, col_edit, col_preview = st.columns([1, 1.5, 1.5])
            
            with col_sel:
                st.markdown("**Select Photo to Edit**")
                selected_file = st.selectbox("Choose file", list(st.session_state.images_data.keys()), label_visibility="collapsed")
            
            if selected_file:
                img_data = st.session_state.images_data[selected_file]
                orig_img = img_data["original"]
                current_img = img_data["edited"]
                
                with col_edit:
                    st.markdown("**🛠️ Manual Tools**")
                    brightness = st.slider("Brightness", 0.5, 1.5, 1.0, 0.05)
                    contrast = st.slider("Contrast", 0.5, 1.5, 1.0, 0.05)
                    sharpness = st.slider("Sharpness", 0.5, 2.0, 1.0, 0.1)
                    
                    st.markdown("**🤖 AI Tools**")
                    if st.button("✨ AI Auto-Crop (Face)"):
                        cropped = ai_face_crop(current_img, PHOTO_W_CM, PHOTO_H_CM)
                        if cropped:
                            st.session_state.images_data[selected_file]["edited"] = cropped
                            st.success("Face cropped successfully!")
                            st.rerun()
                        else:
                            st.error("No face detected! Please crop manually.")
                            
                    if st.button("↺ Reset to Original"):
                        st.session_state.images_data[selected_file]["edited"] = orig_img.copy()
                        st.rerun()

                with col_preview:
                    st.markdown("**Live Preview**")
                    # Apply real-time manual edits
                    preview_img = current_img.copy()
                    preview_img = ImageEnhance.Brightness(preview_img).enhance(brightness)
                    preview_img = ImageEnhance.Contrast(preview_img).enhance(contrast)
                    preview_img = ImageEnhance.Sharpness(preview_img).enhance(sharpness)
                    
                    st.image(preview_img, use_container_width=True)
                    
                    if st.button("💾 Apply & Save Adjustments", type="primary"):
                        st.session_state.images_data[selected_file]["edited"] = preview_img
                        st.success("Edits saved!")
                        st.rerun()

    # -------- TAB 2: GENERATE --------
    with tab2:
        st.markdown(f"**Selected Format:** {format_choice} | **Copies:** {copies}")
        
        if st.button("⚡ Generate Sheet Now", type="primary", use_container_width=True):
            # Layout logic (simplified for compactness)
            CM_TO_PT, DPI = 28.35, 300
            PW, PH, MARGIN, GAP = A4[0], A4[1], 25, 10
            MAX_H = int(PHOTO_H_CM * CM_TO_PT)
            ADJ_W = int(PHOTO_W_CM * CM_TO_PT)
            
            # --- PDF GENERATION ---
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
                c = canvas.Canvas(tmp_pdf.name, pagesize=A4)
                x, y = MARGIN, PH - MARGIN - MAX_H
                
                for fname, data in st.session_state.images_data.items():
                    img = data["edited"]
                    
                    # Add thin border
                    img = ImageOps.expand(img, border=2, fill="black")
                    tf = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
                    img.save(tf.name, format="JPEG", quality=95)
                    
                    for _ in range(copies):
                        if y < MARGIN:
                            c.showPage()
                            x, y = MARGIN, PH - MARGIN - MAX_H
                        
                        c.drawImage(tf.name, x, y, width=ADJ_W, height=MAX_H)
                        x += ADJ_W + GAP
                        if x + ADJ_W > PW - MARGIN:
                            x = MARGIN
                            y -= MAX_H + GAP
                c.save()
                with open(tmp_pdf.name, "rb") as f:
                    st.session_state.pdf_bytes = f.read()

            st.session_state.processed = True
            st.success("✅ Sheets Generated Successfully!")

        # Download Buttons (Only show if processed)
        if st.session_state.processed:
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.download_button("📄 Download PDF (A4)", st.session_state.pdf_bytes, "passport_sheet.pdf", "application/pdf", use_container_width=True)
            with col2:
                st.info("Tip: Use PDF for the best print quality at any local shop.")
