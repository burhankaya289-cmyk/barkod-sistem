import streamlit as st
from supabase import create_client
import random
import pandas as pd

# =========================
# SUPABASE
# =========================
SUPABASE_URL = "https://ujribeeceqryqowkvlmh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVqcmliZWVjZXFyeXFvd2t2bG1oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA0ODM3NzMsImV4cCI6MjA5NjA1OTc3M30.rowgU9bAJPdz6-aSpwUMUEWarsM3B-WKV_K75t-NVZA"

db = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Barkod Panel", layout="wide")

# =========================
# LOGIN STATE
# =========================
if "user" not in st.session_state:
    st.session_state.user = None

if "page" not in st.session_state:
    st.session_state.page = "login"

if "temp" not in st.session_state:
    st.session_state.temp = []

# =========================
# BARCODE GEN
# =========================
def gen_barcode():
    return "278294" + str(random.randint(10000, 99999))

# =========================
# LOGIN
# =========================
if not st.session_state.user:

    st.title("🔐 Giriş")

    u = st.text_input("Kullanıcı")
    p = st.text_input("Şifre", type="password")

    if st.button("Giriş"):
        users = db.table("users").select("*").execute().data

        found = None
        for x in users:
            if x["username"] == u and x["password"] == p:
                found = x

        if found:
            st.session_state.user = found
            st.rerun()
        else:
            st.error("Hatalı giriş")

    st.stop()

user = st.session_state.user

# =========================
# SIDEBAR
# =========================
st.sidebar.title("📦 PANEL")

if st.sidebar.button("➕ Barkod Oluştur"):
    st.session_state.page = "create"

if st.sidebar.button("📥 Import"):
    st.session_state.page = "import"

if st.sidebar.button("📋 Barkodlar"):
    st.session_state.page = "list"

if st.sidebar.button("🚪 Çıkış"):
    st.session_state.user = None
    st.rerun()

# =========================
# PAGE: CREATE
# =========================
if st.session_state.page == "create":

    st.title("➕ Barkod Oluştur")

    # SHUBELER
    branches = db.table("branches").select("*").execute().data
    branch_names = [b["name"] for b in branches]

    q = st.text_input("Şube ara")

    filtered = [b for b in branch_names if q.lower() in b.lower()] if q else branch_names

    branch = st.selectbox("Şube", filtered if filtered else branch_names)

    product = st.text_input("Ürün içeriği")

    w = h = l = weight = ""

    # PRODUCT AUTO
    if product:
        products = db.table("products").select("*").execute().data

        for p in products:
            if p["name"].lower() == product.lower():
                w = p.get("w", "")
                h = p.get("h", "")
                l = p.get("l", "")
                weight = p.get("weight", "")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        w = st.text_input("En", value=w)
    with col2:
        h = st.text_input("Boy", value=h)
    with col3:
        l = st.text_input("Yükseklik", value=l)
    with col4:
        weight = st.text_input("Ağırlık", value=weight)

    if st.button("➕ Kutu Ekle"):
        st.session_state.temp.append({
            "barcode": gen_barcode(),
            "branch_name": branch,
            "product": product,
            "w": w,
            "h": h,
            "l": l,
            "weight": weight,
            "status": "waiting",
            "created_by": user["username"]
        })

    st.markdown("### 📦 Bekleyenler")

    for i, t in enumerate(st.session_state.temp):
        st.write(i+1, t["branch_name"], t["product"], t["barcode"])

    if st.button("💾 Kaydet"):
        for t in st.session_state.temp:
            db.table("barcodes").insert(t).execute()

        st.session_state.temp = []
        st.success("Kaydedildi")

# =========================
# PAGE: IMPORT
# =========================
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
                    "branch_name": r.get("branch_name", ""),
                    "product": r.get("product", ""),
                    "status": "waiting",
                    "created_by": user["username"]
                }).execute()

            st.success("Import tamam")

# =========================
# PAGE: LIST
# =========================
if st.session_state.page == "list":

    st.title("📋 Barkodlar")

    data = db.table("barcodes").select("*").execute().data

    for d in data:
        st.write(
            d.get("barcode"),
            d.get("branch_name"),
            d.get("product"),
            d.get("status")
        )
