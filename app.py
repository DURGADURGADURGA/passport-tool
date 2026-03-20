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

st.set_page_config(page_title="Passport Photo Tool", page_icon="📷", layout="centered")

st.markdown("""
    <style>
        .main { background-color: #f0f4f8; }
        h1 { color: #1a365d; }
        .stButton>button {
            background-color: #2b6cb0;
            color: white;
            border-radius: 8px;
            padding: 0.5em 2em;
            font-size: 16px;
        }
        .stButton>button:hover { background-color: #2c5282; }
    </style>
""", unsafe_allow_html=True)

st.title("📷 Passport Photo Tool")
st.markdown("**Multiple logon ki photos ek saath A4 PDF mein arrange karo!**")
st.divider()

# Upload photos
uploaded_files = st.file_uploader(
    "📁 Photos Upload karo (ek ya zyada)",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

copies = st.number_input("🔢 Har photo ki kitni copies chahiye?", min_value=1, max_value=20, value=2, step=1)

if uploaded_files:
    st.success(f"✅ {len(uploaded_files)} photo(s) select ki gayi hain")

    cols = st.columns(min(len(uploaded_files), 6))
    for i, file in enumerate(uploaded_files):
        with cols[i % 6]:
            st.image(file, use_container_width=True, caption=file.name.split(".")[0])

st.divider()

if st.button("🖨️ PDF Generate Karo"):
    if not uploaded_files:
        st.error("❌ Pehle photos upload karo!")
    else:
        with st.spinner("PDF ban raha hai... thoda ruko ⏳"):

            usable_width = PAGE_W - 2 * MARGIN - (PHOTOS_PER_ROW - 1) * GAP
            adjusted_w = usable_width / PHOTOS_PER_ROW

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as pdf_tmp:
                pdf_path = pdf_tmp.name

            c = canvas.Canvas(pdf_path, pagesize=A4)
            x_start = MARGIN
            y_start = PAGE_H - MARGIN
            x = x_start
            y = y_start
            row_max_height = 0
            photo_in_row = 0

            temp_files = []

            for uploaded_file in uploaded_files:
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
                        x = x_start
                        y = y_start
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

            c.save()

            for f in temp_files:
                os.remove(f)

            with open(pdf_path, "rb") as f:
                pdf_data = f.read()
            os.remove(pdf_path)

        st.success("✅ PDF Ready hai!")
        st.download_button(
            label="⬇️ PDF Download Karo",
            data=pdf_data,
            file_name="passport_photos.pdf",
            mime="application/pdf"
        )
