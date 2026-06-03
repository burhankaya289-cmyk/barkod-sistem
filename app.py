import streamlit as st
from supabase import create_client
import random

# =====================
# SUPABASE BAĞLANTI
# =====================
SUPABASE_URL = "https://ujribeeceqryqowkvlmh.supabase.co"

SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVqcmliZWVjZXFyeXFvd2t2bG1oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA0ODM3NzMsImV4cCI6MjA5NjA1OTc3M30.rowgU9bAJPdz6-aSpwUMUEWarsM3B-WKV_K75t-NVZA"

if SUPABASE_URL == "" or SUPABASE_KEY == "" or "BURAYA" in SUPABASE_KEY:
    st.error("Supabase ayarları eksik!")
    st.stop()

db = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(layout="wide")

# =====================
# LOGIN
# =====================
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.title("Giriş")

    u = st.text_input("Kullanıcı")
    p = st.text_input("Şifre", type="password")

    if st.button("Giriş"):
        try:
            res = db.table("users").select("*").eq("username", u).eq("password", p).execute()
            if res.data:
                st.session_state.user = res.data[0]
                st.rerun()
            else:
                st.error("Hatalı giriş")
        except Exception as e:
            st.error(f"DB hata: {e}")

    st.stop()

user = st.session_state.user

# =====================
# MENU
# =====================
menu = st.sidebar.selectbox("Menü", [
    "Barkod Oluştur",
    "Barkodlar",
    "Şubeler",
    "Ürünler"
])

# =====================
# BARKOD OLUŞTUR
# =====================
if menu == "Barkod Oluştur":
    st.title("Barkod Oluştur")

    try:
        branches = db.table("branches").select("*").execute().data
        branch_names = [b["name"] for b in branches] if branches else []
    except:
        branch_names = []

    branch = st.selectbox("Şube", branch_names) if branch_names else st.text_input("Şube")
    product = st.text_input("Ürün")

    if st.button("Kutu Ekle"):
        barcode = str(random.randint(1000000000, 9999999999))

        db.table("barcodes").insert({
            "barcode": barcode,
            "branch_name": branch,
            "product": product,
            "status": "waiting",
            "created_by": user["username"]
        }).execute()

        st.success("Barkod oluşturuldu")

# =====================
# BARKOD LİSTE
# =====================
if menu == "Barkodlar":
    st.title("Barkodlar")

    try:
        data = db.table("barcodes").select("*").execute().data
        for d in data:
            st.write(d["branch_name"], d["product"], d["barcode"], d["status"])
    except Exception as e:
        st.error(f"Hata: {e}")

# =====================
# ŞUBE
# =====================
if menu == "Şubeler":
    st.title("Şube Ekle")

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

# =====================
# ÜRÜN
# =====================
if menu == "Ürünler":
    st.title("Ürün Ekle")

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
