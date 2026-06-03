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

st.set_page_config(page_title="Barkod Panel", layout="wide")

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

# =====================
# LOGIN
# =====================
if not st.session_state.user:
    st.title("🔐 Login")

    u = st.text_input("User")
    p = st.text_input("Pass", type="password")

    if st.button("Giriş"):
        users = safe("users")

        user = next((x for x in users if x.get("username")==u and x.get("password")==p), None)

        if user:
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Hatalı")

    st.stop()

user = st.session_state.user

# =====================
# SIDEBAR
# =====================
st.sidebar.title("PANEL")

menu = [
    ("Barkod", "create"),
    ("Şubeler", "branches"),
    ("Ürünler", "products"),
    ("Barkodlar", "list"),
    ("Import", "import"),
]

for label, key in menu:
    if st.sidebar.button(label):
        st.session_state.page = key

if st.sidebar.button("Çıkış"):
    st.session_state.user = None
    st.rerun()

# =====================
# BARKOD OLUŞTUR
# =====================
if st.session_state.page == "create":
    st.title("➕ Barkod")

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

    st.write("## Liste")

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

    for b in safe("barcodes"):
        st.write(b.get("barcode"), b.get("branch"), b.get("status"))

# =====================
# IMPORT
# =====================
if st.session_state.page == "import":
    st.title("📥 Excel")

    file = st.file_uploader("xlsx", type=["xlsx"])

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

            st.success("OK")
