import streamlit as st
from supabase import create_client
import random
import pandas as pd

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

def safe_query(table):
    try:
        return db.table(table).select("*").execute().data
    except:
        return []

# =====================
# LOGIN
# =====================
if not st.session_state.user:
    st.title("🔐 Giriş")

    u = st.text_input("Kullanıcı")
    p = st.text_input("Şifre", type="password")

    if st.button("Giriş"):
        users = safe_query("users")

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

if st.sidebar.button("Barkod Oluştur"):
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
# CREATE BARKOD
# =====================
if st.session_state.page == "create":
    st.title("➕ Barkod Oluştur")

    branches = safe_query("branches")
    products = safe_query("products")

    branch_names = [b.get("name","") for b in branches]

    q = st.text_input("Şube ara")
    filtered = [b for b in branch_names if q.lower() in b.lower()] if q else branch_names

    branch = st.selectbox("Şube", filtered if filtered else branch_names)

    product_name = st.text_input("Ürün")

    w = h = l = weight = ""

    if product_name:
        match = next((p for p in products if p.get("name","").lower()==product_name.lower()), None)
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
            "branch_name": branch,
            "product": product_name,
            "w": w,
            "h": h,
            "l": l,
            "weight": weight,
            "status": "waiting",
            "created_by": user["username"]
        })

    st.write("## Bekleyenler")
    for i,b in enumerate(st.session_state.basket):
        st.write(i+1, b["barcode"], b["branch_name"], b["product"])

    if st.button("💾 Kaydet"):
        for b in st.session_state.basket:
            try:
                db.table("barcodes").insert(b).execute()
            except:
                pass
        st.session_state.basket = []
        st.success("Kaydedildi")

# =====================
# BRANCHES
# =====================
if st.session_state.page == "branches":
    st.title("🏢 Şubeler")

    name = st.text_input("Şube Adı")
    code = st.text_input("Kod")
    address = st.text_input("Adres")

    if st.button("Ekle"):
        db.table("branches").insert({
            "name": name,
            "code": code,
            "address": address
        }).execute()

    st.write("## Liste")
    for b in safe_query("branches"):
        st.write(b.get("name"), b.get("code"), b.get("address"))

# =====================
# PRODUCTS
# =====================
if st.session_state.page == "products":
    st.title("📦 Ürünler")

    name = st.text_input("Ürün Adı")
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

    st.write("## Liste")
    for p in safe_query("products"):
        st.write(p.get("name"), p.get("w"), p.get("h"), p.get("l"), p.get("weight"))

# =====================
# LIST
# =====================
if st.session_state.page == "list":
    st.title("📋 Barkodlar")

    for b in safe_query("barcodes"):
        st.write(b.get("barcode"), b.get("branch_name"), b.get("status"))

# =====================
# IMPORT
# =====================
if st.session_state.page == "import":
    st.title("📥 Excel Import")

    file = st.file_uploader("Excel", type=["xlsx"])

    if file:
        df = pd.read_excel(file)
        st.dataframe(df)

        if st.button("Aktar"):
            for _, r in df.iterrows():
                db.table("barcodes").insert({
                    "barcode": gen_barcode(),
                    "branch_name": r.get("branch_name",""),
                    "product": r.get("product",""),
                    "status":"waiting",
                    "created_by": user["username"]
                }).execute()

            st.success("Bitti")
