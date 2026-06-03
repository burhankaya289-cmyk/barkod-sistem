st.write(db.table("users").select("*").execute())
st.stop()
import streamlit as st
from supabase import create_client
import random
import pandas as pd

# =======================
# SUPABASE
# =======================
SUPABASE_URL = "https://ujribeeceqryqowkvlmh.supabase.co"
SUPABASE_KEY = "BURAYA_ANON_KEY"

db = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Barkod Sistem", layout="wide")

# =======================
# STATE
# =======================
if "user" not in st.session_state:
    st.session_state.user = None

if "page" not in st.session_state:
    st.session_state.page = "login"

if "temp_barcodes" not in st.session_state:
    st.session_state.temp_barcodes = []

# =======================
# BARCODE
# =======================
def gen_barcode():
    return "278294" + str(random.randint(10000, 99999))

# =======================
# LOGIN
# =======================
if not st.session_state.user:
    st.title("🔐 Giriş")

    username = st.text_input("Kullanıcı")
    password = st.text_input("Şifre", type="password")

    if st.button("Giriş"):
        try:
            users = db.table("users").select("*").execute().data
        except:
            st.error("Supabase users tablosu okunamadı (RLS / tablo kontrol et)")
            st.stop()

        found = None
        for u in users:
            if u.get("username") == username and u.get("password") == password:
                found = u

        if found:
            st.session_state.user = found
            st.rerun()
        else:
            st.error("Hatalı giriş")

    st.stop()

user = st.session_state.user

# =======================
# SIDEBAR
# =======================
st.sidebar.title("📦 MENÜ")

if st.sidebar.button("➕ Barkod"):
    st.session_state.page = "create"

if st.sidebar.button("🏢 Şubeler"):
    st.session_state.page = "branches"

if st.sidebar.button("📦 Ürünler"):
    st.session_state.page = "products"

if st.sidebar.button("📋 Liste"):
    st.session_state.page = "list"

if st.sidebar.button("📥 Import"):
    st.session_state.page = "import"

if st.sidebar.button("🚪 Çıkış"):
    st.session_state.user = None
    st.rerun()

# =======================
# PAGE: CREATE
# =======================
if st.session_state.page == "create":
    st.title("➕ Barkod Oluştur")

    # SHUBELER
    try:
        branches = db.table("branches").select("*").execute().data
    except:
        branches = []

    branch_names = [b.get("name", "") for b in branches]

    q = st.text_input("Şube ara")

    filtered = [b for b in branch_names if q.lower() in b.lower()] if q else branch_names

    branch = st.selectbox("Şube", filtered if filtered else branch_names)

    # ÜRÜN
    product = st.text_input("Ürün içeriği")

    w = h = l = weight = ""

    if product:
        try:
            products = db.table("products").select("*").execute().data
        except:
            products = []

        for p in products:
            if p.get("name", "").lower() == product.lower():
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
        st.session_state.temp_barcodes.append({
            "barcode": gen_barcode(),
            "branch_name": branch,
            "product": product,
            "w": w,
            "h": h,
            "l": l,
            "weight": weight,
            "status": "waiting",
            "created_by": user.get("username")
        })

    st.subheader("📦 Bekleyenler")

    for i, t in enumerate(st.session_state.temp_barcodes):
        st.write(i+1, t["branch_name"], t["product"], t["barcode"])

    if st.button("💾 Kaydet"):
        for t in st.session_state.temp_barcodes:
            try:
                db.table("barcodes").insert(t).execute()
            except Exception as e:
                st.error(f"Hata: {e}")

        st.session_state.temp_barcodes = []
        st.success("Kaydedildi")

# =======================
# PAGE: BRANCHES
# =======================
if st.session_state.page == "branches":
    st.title("🏢 Şubeler")

    code = st.text_input("Kod")
    name = st.text_input("Şube Adı")
    address = st.text_input("Adres")

    if st.button("Şube Ekle"):
        db.table("branches").insert({
            "code": code,
            "name": name,
            "address": address
        }).execute()
        st.success("Eklendi")

    st.divider()

    try:
        branches = db.table("branches").select("*").execute().data
    except:
        branches = []

    for b in branches:
        st.write(b.get("code"), b.get("name"), b.get("address"))

# =======================
# PAGE: PRODUCTS
# =======================
if st.session_state.page == "products":
    st.title("📦 Ürünler")

    name = st.text_input("Ürün adı")
    w = st.text_input("En")
    h = st.text_input("Boy")
    l = st.text_input("Yükseklik")
    weight = st.text_input("Ağırlık")

    if st.button("Ürün Ekle"):
        db.table("products").insert({
            "name": name,
            "w": w,
            "h": h,
            "l": l,
            "weight": weight
        }).execute()
        st.success("Eklendi")

    st.divider()

    try:
        products = db.table("products").select("*").execute().data
    except:
        products = []

    for p in products:
        st.write(p.get("name"), p.get("w"), p.get("h"), p.get("l"), p.get("weight"))

# =======================
# PAGE: LIST
# =======================
if st.session_state.page == "list":
    st.title("📋 Barkodlar")

    try:
        data = db.table("barcodes").select("*").execute().data
    except:
        data = []

    for d in data:
        st.write(
            d.get("barcode"),
            d.get("branch_name"),
            d.get("product"),
            d.get("status")
        )

# =======================
# PAGE: IMPORT
# =======================
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
                    "created_by": user.get("username")
                }).execute()

            st.success("Import tamam")
