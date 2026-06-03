import streamlit as st
from supabase import create_client
import random
import pandas as pd

# =========================
# SUPABASE
# =========================
SUPABASE_URL = "https://ujribeeceqryqowkvlmh.supabase.co"
SUPABASE_KEY = "BURAYA_ANON_KEY"

db = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Barkod Panel", layout="wide")

# =========================
# LOGIN
# =========================
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.title("🔐 Giriş")

    u = st.text_input("Kullanıcı")
    p = st.text_input("Şifre", type="password")

    if st.button("Giriş"):
        users = db.table("users").select("*").execute().data

        match = None
        for x in users:
            if x["username"] == u and x["password"] == p:
                match = x

        if match:
            st.session_state.user = match
            st.rerun()
        else:
            st.error("Hatalı giriş")

    st.stop()

user = st.session_state.user

# =========================
# STATE
# =========================
if "page" not in st.session_state:
    st.session_state.page = "create"

if "temp_list" not in st.session_state:
    st.session_state.temp_list = []

# =========================
# BARCODE
# =========================
def generate_barcode():
    return "278294" + str(random.randint(10000, 99999))

# =========================
# SIDEBAR
# =========================
st.sidebar.title("📦 MENÜ")

if st.sidebar.button("➕ Barkod Oluştur"):
    st.session_state.page = "create"

if st.sidebar.button("📥 Import"):
    st.session_state.page = "import"

if st.sidebar.button("📋 Barkodlar"):
    st.session_state.page = "list"

# =========================
# PAGE: CREATE
# =========================
if st.session_state.page == "create":
    st.title("➕ Barkod Oluştur")

    # --- ŞUBE AUTOCOMPLETE ---
    branches = db.table("branches").select("*").execute().data
    branch_names = [b["name"] for b in branches]

    q = st.text_input("Şube adı / kod yaz")

    filtered = [b for b in branch_names if q.lower() in b.lower()] if q else branch_names

    branch = st.selectbox("Şube seç", filtered if filtered else branch_names)

    # --- ÜRÜN ---
    product = st.text_input("Ürün içeriği")

    # ürün auto
    w = h = l = weight = ""

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

    # --- KUTU EKLE ---
    if st.button("➕ Kutu Ekle"):
        st.session_state.temp_list.append({
            "barcode": generate_barcode(),
            "branch_name": branch,
            "product": product,
            "w": w,
            "h": h,
            "l": l,
            "weight": weight,
            "status": "waiting",
            "created_by": user["username"]
        })

        st.success("Eklendi")

    # --- GEÇİCİ LİSTE ---
    st.markdown("### 📦 Bekleyenler")

    for i, x in enumerate(st.session_state.temp_list):
        st.write(i+1, x["branch_name"], x["product"], x["barcode"])

    # --- KAYDET ---
    if st.button("💾 Kaydet"):
        for item in st.session_state.temp_list:
            db.table("barcodes").insert({
                "barcode": item["barcode"],
                "branch_name": item["branch_name"],
                "product": item["product"],
                "w": item["w"],
                "h": item["h"],
                "l": item["l"],
                "weight": item["weight"],
                "status": "waiting",
                "created_by": item["created_by"]
            }).execute()

        st.session_state.temp_list = []
        st.success("Kaydedildi")

# =========================
# PAGE: IMPORT
# =========================
if st.session_state.page == "import":
    st.title("📥 Import")

    file = st.file_uploader("Excel yükle", type=["xlsx"])

    if file:
        df = pd.read_excel(file)
        st.dataframe(df)

        if st.button("Aktar"):
            for _, r in df.iterrows():
                db.table("barcodes").insert({
                    "barcode": generate_barcode(),
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
        st.write(d["barcode"], d["branch_name"], d["product"], d["status"])
