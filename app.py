import streamlit as st
from supabase import create_client
import random
import pandas as pd
import io

# =====================
# REPORTLAB (DOĞRU IMPORT)
# =====================
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

# =====================
# BARCODE
# =====================
from barcode import Code128
from barcode.writer import ImageWriter

# =====================
# SUPABASE
# =====================
SUPABASE_URL = "https://ujribeeceqryqowkvlmh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVqcmliZWVjZXFyeXFvd2t2bG1oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA0ODM3NzMsImV4cCI6MjA5NjA1OTc3M30.rowgU9bAJPdz6-aSpwUMUEWarsM3B-WKV_K75t-NVZA"

db = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Barkod Sistem", layout="wide")

# =====================
# STATE
# =====================
if "user" not in st.session_state:
    st.session_state.user = None

if "page" not in st.session_state:
    st.session_state.page = "login"

if "basket" not in st.session_state:
    st.session_state.basket = []

# =====================
# HELPERS
# =====================
def gen_barcode():
    return "278294" + str(random.randint(10000, 99999))

def safe(table):
    try:
        return db.table(table).select("*").execute().data
    except:
        return []

def create_barcode_image(text):
    barcode = Code128(text, writer=ImageWriter())
    path = f"/tmp/{text}"
    return barcode.save(path)

def create_pdf(items):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(10*cm, 15*cm))

    for item in items:

        c.setFont("Helvetica-Bold", 10)
        c.drawString(10, 420, f"BARKOD: {item['barcode']}")

        c.setFont("Helvetica", 9)
        c.drawString(10, 400, f"ŞUBE: {item.get('branch','')}")
        c.drawString(10, 385, f"ÜRÜN: {item.get('product','')}")
        c.drawString(10, 370, f"ÖLÇÜ: {item.get('w','')}x{item.get('h','')}x{item.get('l','')}")
        c.drawString(10, 355, f"AĞIRLIK: {item.get('weight','')}")

        try:
            img_path = create_barcode_image(item["barcode"])
            img = ImageReader(img_path)
            c.drawImage(img, 10, 220, width=250, height=80)
        except:
            pass

        c.showPage()

    c.save()
    buffer.seek(0)
    return buffer

# =====================
# LOGIN
# =====================
if not st.session_state.user:
    st.title("🔐 Giriş")

    u = st.text_input("Kullanıcı")
    p = st.text_input("Şifre", type="password")

    if st.button("Giriş"):
        users = safe("users")

        user = next((x for x in users if x.get("username")==u and x.get("password")==p), None)

        if user:
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Hatalı giriş")

    st.stop()

user = st.session_state.user

# =====================
# SIDEBAR
# =====================
st.sidebar.title("📦 PANEL")

if st.sidebar.button("Barkod"):
    st.session_state.page = "create"

if st.sidebar.button("Şubeler"):
    st.session_state.page = "branches"

if st.sidebar.button("Ürünler"):
    st.session_state.page = "products"

if st.sidebar.button("Barkodlar"):
    st.session_state.page = "list"

if st.sidebar.button("Import"):
    st.session_state.page = "import"

if st.sidebar.button("Çıkış"):
    st.session_state.user = None
    st.rerun()

# =====================
# CREATE
# =====================
if st.session_state.page == "create":
    st.title("➕ Barkod Oluştur")

    branches = safe("branches")
    products = safe("products")

    branch_names = [b.get("name","") for b in branches]

    branch = st.selectbox("Şube", branch_names)

    product = st.text_input("Ürün")

    w = h = l = weight = ""

    if product:
        match = next((p for p in products if p.get("name","").lower()==product.lower()), None)
        if match:
            w, h, l, weight = match.get("w",""), match.get("h",""), match.get("l",""), match.get("weight","")

    c1,c2,c3,c4 = st.columns(4)
    with c1: w = st.text_input("En", value=w)
    with c2: h = st.text_input("Boy", value=h)
    with c3: l = st.text_input("Yükseklik", value=l)
    with c4: weight = st.text_input("Ağırlık", value=weight)

    if st.button("➕ Ekle"):
        st.session_state.basket.append({
            "barcode": gen_barcode(),
            "branch": branch,
            "product": product,
            "w": w,
            "h": h,
            "l": l,
            "weight": weight,
            "status": "waiting",
            "user": user["username"]
        })

    st.write("## Sepet")

    for i,b in enumerate(st.session_state.basket):
        st.write(i+1, b["barcode"], b["branch"], b["product"])

    if st.button("💾 Kaydet"):
        for b in st.session_state.basket:
            try:
                db.table("barcodes").insert(b).execute()
            except:
                pass

        pdf = create_pdf(st.session_state.basket)
        st.download_button("PDF İndir", pdf, file_name="barkod.pdf", mime="application/pdf")

        st.session_state.basket = []
        st.success("Kaydedildi")

# =====================
# BRANCHES
# =====================
if st.session_state.page == "branches":
    st.title("🏢 Şubeler")

    name = st.text_input("Şube")
    code = st.text_input("Kod")
    address = st.text_input("Adres")

    if st.button("Ekle"):
        db.table("branches").insert({
            "name": name,
            "code": code,
            "address": address
        }).execute()

    for b in safe("branches"):
        st.write(b.get("name"), b.get("code"), b.get("address"))

# =====================
# PRODUCTS
# =====================
if st.session_state.page == "products":
    st.title("📦 Ürünler")

    name = st.text_input("Ürün")
    w = st.text_input("En")
    h = st.text_input("Boy")
    l = st.text_input("Yükseklik")
    weight = st.text_input("Ağırlık")

    if st.button("Ekle"):
        db.table("products").insert({
            "name": name,
            "w": w,
            "h": h,
            "l": l,
            "weight": weight
        }).execute()

    for p in safe("products"):
        st.write(p.get("name"), p.get("w"), p.get("h"), p.get("l"))

# =====================
# LIST
# =====================
if st.session_state.page == "list":
    st.title("📋 Barkodlar")

    data = safe("barcodes")

    selected = []

    for i,b in enumerate(data):
        col1,col2,col3,col4 = st.columns([1,3,3,2])

        with col1:
            if st.checkbox("", key=i):
                selected.append(b)

        with col2:
            st.write(b.get("barcode"))

        with col3:
            st.write(b.get("branch"))

        with col4:
            st.write("🟢" if b.get("status")=="waiting" else "🔴")

    if selected:
        pdf = create_pdf(selected)

        st.download_button(
            "🖨 PDF İndir",
            pdf,
            file_name="barkodlar.pdf",
            mime="application/pdf"
        )

    if st.button("✔ Yazdırıldı"):
        for s in selected:
            try:
                db.table("barcodes").update({"status":"printed"}).eq("barcode", s["barcode"]).execute()
            except:
                pass

# =====================
# IMPORT
# =====================
if st.session_state.page == "import":
    st.title("📥 Import")

    file = st.file_uploader("Excel", type=["xlsx"])

    if file:
        df = pd.read_excel(file)
        st.dataframe(df)

        if st.button("Aktar"):
            for _, r in df.iterrows():
                db.table("barcodes").insert({
                    "barcode": gen_barcode(),
                    "branch": r.get("branch",""),
                    "product": r.get("product",""),
                    "status":"waiting",
                    "user": user["username"]
                }).execute()

            st.success("Tamam")
