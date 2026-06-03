import streamlit as st
from supabase import create_client
import random

SUPABASE_URL = "BURAYA_SUPABASE_URL"
SUPABASE_KEY = "BURAYA_SUPABASE_KEY"

db = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(layout="wide")

# LOGIN
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.title("Giriş")

    u = st.text_input("Kullanıcı")
    p = st.text_input("Şifre", type="password")

    if st.button("Giriş"):
        res = db.table("users").select("*").eq("username", u).eq("password", p).execute()

        if res.data:
            st.session_state.user = res.data[0]
            st.rerun()

    st.stop()

user = st.session_state.user

menu = st.sidebar.selectbox("Menü", [
    "Barkod Oluştur",
    "Barkodlar",
    "Şubeler",
    "Ürünler"
])

if menu == "Barkod Oluştur":
    st.title("Barkod Oluştur")

    branches = db.table("branches").select("*").execute().data
    branch_names = [b["name"] for b in branches] if branches else []

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

if menu == "Barkodlar":
    st.title("Barkodlar")

    data = db.table("barcodes").select("*").execute().data

    for d in data:
        st.write(d["branch_name"], d["product"], d["barcode"], d["status"])

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
