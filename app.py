import streamlit as st
from supabase import create_client
import random
import pandas as pd

# ======================
# SUPABASE
# ======================
SUPABASE_URL = "https://ujribeeceqryqowkvlmh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVqcmliZWVjZXFyeXFvd2t2bG1oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA0ODM3NzMsImV4cCI6MjA5NjA1OTc3M30.rowgU9bAJPdz6-aSpwUMUEWarsM3B-WKV_K75t-NVZA"

db = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Barkod Panel", layout="wide")

# ======================
# LOGIN
# ======================
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.title("🔐 Giriş")

    u = st.text_input("Kullanıcı")
    p = st.text_input("Şifre", type="password")

    if st.button("Giriş"):
        res = db.table("users").select("*").execute().data

        user_match = None
        for r in res:
            if r["username"] == u and r["password"] == p:
                user_match = r

        if user_match:
            st.session_state.user = user_match
            st.rerun()
        else:
            st.error("Hatalı giriş")

    st.stop()

user = st.session_state.user

# ======================
# STATE
# ======================
if "page" not in st.session_state:
    st.session_state.page = "create"

if "draft_list" not in st.session_state:
    st.session_state.draft_list = []

# ======================
# BARCODE GEN
# ======================
def generate_barcode():
    return "278294" + str(random.randint(10000, 99999))

# ======================
# SIDEBAR (İKONLU)
# ======================
st.sidebar.title("📦 PANEL")

if st.sidebar.button("➕ Barkod Oluştur"):
    st.session_state.page = "create"

if st.sidebar.button("📥 Barkod Import"):
    st.session_state.page = "import"

if st.sidebar.button("📋 Oluşturulan Barkodlar"):
    st.session_state.page = "list"

if st.sidebar.button("🏢 Şubeler"):
    st.session_state.page = "branches"

if st.sidebar.button("📦 Ürünler"):
    st.session_state.page = "products"

# ======================
# PAGE: CREATE
# ======================
if st.session_state.page == "create":
    st.title("➕ Tekli Barkod Oluşturma")

    # ŞUBE SABİT KALSIN
    if "selected_branch" not in st.session_state:
        st.session_state.selected_branch = ""

    branch = st.text_input("Şube adı / kod", value=st.session_state.selected_branch)
    st.session_state.selected_branch = branch

    product_name = st.text_input("Ürün içeriği")

    # Ürün otomatik veri çekme
    weight = ""
    w = ""
    h = ""
    l = ""

    if product_name:
        res = db.table("products").select("*").execute().data

        for p in res:
            if p["name"].lower() == product_name.lower():
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
        barcode = generate_barcode()

        st.session_state.draft_list.append({
            "barcode": barcode,
            "branch": branch,
            "product": product_name,
            "w": w,
            "h": h,
            "l": l,
            "weight": weight,
            "status": "waiting",
            "created_by": user["username"]
        })

        st.success(f"Eklendi: {barcode}")

    st.markdown("### 📦 Geçici Liste")
    for i, item in enumerate(st.session_state.draft_list):
        st.write(i+1, item["branch"], item["product"], item["barcode"])

    if st.button("💾 Kaydet"):
        for item in st.session_state.draft_list:
            db.table("barcodes").insert(item).execute()

        st.session_state.draft_list = []
        st.success("Tüm barkodlar kaydedildi")

# ======================
# PAGE: IMPORT
# ======================
if st.session_state.page == "import":
    st.title("📥 Barkod Import")

    file = st.file_uploader("Excel yükle", type=["xlsx"])

    if file:
        df = pd.read_excel(file)
        st.dataframe(df)

        if st.button("Aktar"):
            for _, row in df.iterrows():
                db.table("barcodes").insert({
                    "barcode": generate_barcode(),
                    "branch": row.get("branch", ""),
                    "product": row.get("product", ""),
                    "status": "waiting",
                    "created_by": user["username"]
                }).execute()

            st.success("Import tamam")

# ======================
# PAGE: LIST
# ======================
if st.session_state.page == "list":
    st.title("📋 Oluşturulan Barkodlar")

    data = db.table("barcodes").select("*").execute().data

    for d in data:
        st.write(
            d.get("barcode"),
            d.get("branch"),
            d.get("product"),
            d.get("status"),
            d.get("created_by")
        )

# ======================
# PAGE: BRANCHES
# ======================
if st.session_state.page == "branches":
    st.title("🏢 Şubeler")

    code = st.text_input("Kod")
    name = st.text_input("Şube adı")
    address = st.text_input("Adres")

    if st.button("Ekle"):
        db.table("branches").insert({
            "code": code,
            "name": name,
            "address": address
        }).execute()

        st.success("Şube eklendi")

# ======================
# PAGE: PRODUCTS
# ======================
if st.session_state.page == "products":
    st.title("📦 Ürünler")

    name = st.text_input("Ürün adı")
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

        st.success("Ürün eklendi")
