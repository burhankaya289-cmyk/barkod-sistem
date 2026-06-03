import streamlit as st
from supabase import create_client
import random
import pandas as pd
import io

from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

from barcode import Code128
from barcode.writer import ImageWriter

# =====================
# SUPABASE
# =====================
SUPABASE_URL = "https://ujribeeceqryqowkvlmh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVqcmliZWVjZXFyeXFvd2t2bG1oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA0ODM3NzMsImV4cCI6MjA5NjA1OTc3M30.rowgU9bAJPdz6-aSpwUMUEWarsM3B-WKV_K75t-NVZA"

db = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Barkod SaaS", layout="wide")

# =====================
# SAAS UI THEME
# =====================
st.markdown("""
<style>
.main { background-color:#0b1220; color:#e5e7eb; }

section[data-testid="stSidebar"] {
    background-color:#0f172a;
}

.stButton>button {
    background:linear-gradient(135deg,#3b82f6,#2563eb);
    color:white;
    border-radius:10px;
    height:42px;
    font-weight:600;
    border:none;
}

.stTextInput>div>div>input,
.stSelectbox>div>div>div {
    background-color:#111827;
    color:white;
}

.card {
    background:#111827;
    padding:12px;
    border-radius:12px;
    border:1px solid #1f2937;
    margin-bottom:10px;
}
</style>
""", unsafe_allow_html=True)

# =====================
# STATE
# =====================
if "user" not in st.session_state:
    st.session_state.user = None

if "page" not in st.session_state:
    st.session_state.page = "dashboard"

if "basket" not in st.session_state:
    st.session_state.basket = []

# =====================
# HELPERS
# =====================
def gen_barcode():
    return "278294" + str(random.randint(10000, 99999))

def safe(t):
    try:
        return db.table(t).select("*").execute().data
    except:
        return []

def make_barcode_img(text):
    b = Code128(text, writer=ImageWriter())
    return b.save(f"/tmp/{text}")

def create_pdf(items):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(10*cm, 15*cm))

    for i in items:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(10, 420, f"BARKOD: {i['barcode']}")

        c.setFont("Helvetica", 9)
        c.drawString(10, 400, f"ŞUBE: {i.get('branch','')}")
        c.drawString(10, 385, f"ÜRÜN: {i.get('product','')}")
        c.drawString(10, 370, f"ÖLÇÜ: {i.get('w','')}x{i.get('h','')}x{i.get('l','')}")
        c.drawString(10, 355, f"AĞIRLIK: {i.get('weight','')}")

        try:
            img = ImageReader(make_barcode_img(i["barcode"]))
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
    st.title("🚀 Barkod SaaS Login")

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
# SIDEBAR (SAAS MENU)
# =====================
st.sidebar.markdown("### 🚀 Barkod SaaS")
st.sidebar.markdown("---")

pages = {
    "📊 Dashboard": "dashboard",
    "➕ Barkod": "create",
    "🏢 Şubeler": "branches",
    "📦 Ürünler": "products",
    "📋 Barkodlar": "list",
    "📥 Import": "import"
}

for k,v in pages.items():
    if st.sidebar.button(k):
        st.session_state.page = v

if st.sidebar.button("🚪 Çıkış"):
    st.session_state.user = None
    st.rerun()

# =====================
# DASHBOARD
# =====================
if st.session_state.page == "dashboard":
    st.title("📊 Dashboard")

    barcodes = safe("barcodes")
    branches = safe("branches")
    products = safe("products")

    col1,col2,col3 = st.columns(3)

    col1.metric("Toplam Barkod", len(barcodes))
    col2.metric("Şube", len(branches))
    col3.metric("Ürün", len(products))

    st.write("### Son Barkodlar")

    for b in barcodes[-5:]:
        st.markdown(f"""
        <div class="card">
            📦 {b.get('barcode')}<br>
            🏢 {b.get('branch')}<br>
            📌 {b.get('status')}
        </div>
        """, unsafe_allow_html=True)

# =====================
# CREATE BARKOD
# =====================
if st.session_state.page == "create":
    st.title("➕ Barkod Oluştur")

    branches = safe("branches")
    products = safe("products")

    branch_names = [b.get("name","") for b in branches]

    branch_input = st.text_input("Şube yaz")

    filtered = [b for b in branch_names if branch_input.lower() in b.lower()] if branch_input else branch_names
    branch = st.selectbox("Şube", filtered if filtered else branch_names)

    product = st.text_input("Ürün")

    w = h = l = weight = ""

    if product:
        match = next((p for p in products if p.get("name","").lower()==product.lower()), None)
        if match:
            w,h,l,weight = match.get("w",""),match.get("h",""),match.get("l",""),match.get("weight","")

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

    st.write("### Sepet")

    for i,b in enumerate(st.session_state.basket):
        st.markdown(f"""
        <div class="card">
            📦 {b['barcode']}<br>
            🏢 {b['branch']}<br>
            📌 {b['product']}
        </div>
        """, unsafe_allow_html=True)

    if st.button("💾 Kaydet + PDF"):
        for b in st.session_state.basket:
            try:
                db.table("barcodes").insert(b).execute()
            except:
                pass

        pdf = create_pdf(st.session_state.basket)

        st.download_button(
            "🖨 PDF İndir",
            pdf,
            file_name="barkodlar.pdf",
            mime="application/pdf"
        )

        st.session_state.basket = []
        st.success("Kaydedildi")

# =====================
# BRANCHES
# =====================
if st.session_state.page == "branches":
    st.title("🏢 Şubeler")

    name = st.text_input("Şube adı")
    code = st.text_input("Kod")
    address = st.text_input("Adres")

    if st.button("Ekle"):
        db.table("branches").insert({
            "name": name,
            "code": code,
            "address": address
        }).execute()

    for b in safe("branches"):
        st.markdown(f"<div class='card'>🏢 {b.get('name')} - {b.get('code')}</div>", unsafe_allow_html=True)

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
        st.markdown(f"<div class='card'>📦 {p.get('name')}</div>", unsafe_allow_html=True)

# =====================
# LIST + PRINT
# =====================
if st.session_state.page == "list":
    st.title("📋 Barkodlar")

    data = safe("barcodes")

    selected = []

    for i,b in enumerate(data):
        col1,col2,col3 = st.columns([1,4,2])

        with col1:
            if st.checkbox("", key=i):
                selected.append(b)

        with col2:
            st.markdown(f"<div class='card'>📦 {b.get('barcode')} - {b.get('branch')}</div>", unsafe_allow_html=True)

        with col3:
            st.write("🟢" if b.get("status")=="waiting" else "🔴")

    if selected:
        pdf = create_pdf(selected)

        st.download_button("🖨 PDF İndir", pdf, file_name="barkodlar.pdf", mime="application/pdf")

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

            st.success("Bitti")
