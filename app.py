import streamlit as st
import sqlite3
from config import init_db

# ==========================================
# 1. KONFIGURASI HALAMAN (Wajib di bagian paling atas)
# ==========================================
st.set_page_config(
    page_title="Laporan Terpadu Amil Desa", 
    page_icon="🕌", 
    layout="wide"
)

# Jalankan inisialisasi database
init_db()

# Impor semua modul halaman pendukung
from modul import dashboard, penerimaan, distribusi, master, qurban, majlis, arsip, cetak, pengaturan, admin, cetak_kecamatan, infak, distribusi_infaq
# ==========================================
# 2. SISTEM MANAJEMEN SESI (SESSION STATE)
# ==========================================
if "login_sukses" not in st.session_state:
    st.session_state["login_sukses"] = False
    st.session_state["username"] = ""
    st.session_state["role"] = ""
    st.session_state["desa_tugas"] = ""

def proses_login(username_input, password_input):
    conn = sqlite3.connect("database_upz_desa.db")
    c = conn.cursor()
    c.execute("SELECT role, nama_desa FROM pengguna WHERE username=? AND password=?", (username_input, password_input))
    res = c.fetchone()
    conn.close()
    
    if res:
        st.session_state["login_sukses"] = True
        st.session_state["username"] = username_input
        st.session_state["role"] = res[0]
        st.session_state["desa_tugas"] = res[1]
        return True
    return False

# ==========================================
# 3. ANTARMUKA HALAMAN LOGIN
# ==========================================
if not st.session_state["login_sukses"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    
    with col_l2:
        st.markdown("<h2 style='text-align: center; color: #02723A;'>🕌 SISTEM LAPORAN INTEGRASI AMIL</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Masuk menggunakan akun BAZNAS / UPZ Desa Anda</p>", unsafe_allow_html=True)
        
        with st.container(border=True):
            user_in = st.text_input("Username:")
            pass_in = st.text_input("Password Secure:", type="password")
            
            if st.button("🔑 MASUK KE SISTEM", width="stretch"):
                if proses_login(user_in.strip().lower(), pass_in):
                    st.success("Login Berhasil! Memuat Dashboard...")
                    st.rerun()
                else:
                    st.error("Gagal! Username atau Password tidak sesuai.")
    st.stop()  # Hentikan baris kode di bawah jika status belum login

# ==========================================
# 4. AREA APLIKASI UTAMA (SETELAH LOGIN)
# ==========================================

# Menampilkan Profil Pengguna Aktif di Atas Sidebar
st.sidebar.markdown(f"👤 Pengguna: **{st.session_state['username'].upper()}**")
st.sidebar.caption(f"Hak Akses: {st.session_state['role'].upper()} ({st.session_state['desa_tugas']})")

if st.sidebar.button("🚪 Keluar dari Sistem", type="primary", key="btn_logout", width="stretch"):
    st.session_state["login_sukses"] = False
    st.session_state["username"] = ""
    st.session_state["role"] = ""
    st.session_state["desa_tugas"] = ""
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.title("🕌 Menu Navigasi")

# Pembatasan Hak Akses Menu Berdasarkan Peran (Role-Based Menu)
if st.session_state["role"] == "admin":
    # Menu khusus Admin Kecamatan (Ditambahkan tombol Cetak Gabungan Kecamatan)
    daftar_menu = [
        "📊 Dashboard Utama",
        "⚙️ Panel Admin & Password",
        "🖨️ Cetak Rekap Kecamatan",
        "📁 Arsip Data Lama"
    ]
else:
    # Menu khusus User Amil Desa
    daftar_menu = [
        "📊 Dashboard Utama",
        "📥 Penerimaan Zakat",
        "💸 Infaq & Sedekah",
        "📤 Distribusi UPZ",
        "📤 Distribusi Infaq (Guru)",
        "🐄 Data Qurban",
        "🕌 Data Majlis Ta'lim",
        "📂 Kelola Data Master",
        "🖨️ Cetak Laporan PDF",
        "⚙️ Pengaturan Profil Desa"
    ]

pilihan_menu = st.sidebar.radio("Pilih Halaman:", daftar_menu)

# ==========================================
# 5. ROUTING ALUR HALAMAN MENU
# ==========================================
if pilihan_menu == "📊 Dashboard Utama":
    dashboard.render()
elif pilihan_menu == "⚙️ Panel Admin & Password":
    admin.render()
elif pilihan_menu == "🖨️ Cetak Rekap Kecamatan":
    cetak_kecamatan.render()
elif pilihan_menu == "📥 Penerimaan Zakat":
    penerimaan.render()
elif pilihan_menu == "📤 Distribusi UPZ":
    distribusi.render()
elif pilihan_menu == "📂 Kelola Data Master":
    master.render()
elif pilihan_menu == "🐄 Data Qurban":
    qurban.render()
elif pilihan_menu == "🕌 Data Majlis Ta'lim":
    majlis.render()
elif pilihan_menu == "🖨️ Cetak Laporan PDF":
    cetak.render()
elif pilihan_menu == "📁 Arsip Data Lama":
    arsip.render()
elif pilihan_menu == "⚙️ Pengaturan Profil Desa":
    pengaturan.render()
elif pilihan_menu == "💸 Infaq & Sedekah":
    infak.render()
elif pilihan_menu == "📤 Distribusi Infaq (Guru)":
    distribusi_infaq.render()