import streamlit as st
import sqlite3
import pandas as pd
from config import DB_NAME

def render():
    # Mengambil informasi sesi pengguna yang sedang login dari app.py
    role = st.session_state.get("role", "amil_desa")
    desa_tugas = st.session_state.get("desa_tugas", "")
    username = st.session_state.get("username", "user")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # =========================================================================
    # KONDISI 1: TAMPILAN DASHBOARD UNTUK ADMIN KECAMATAN
    # =========================================================================
    if role == "admin":
        st.title("📊 DASHBOARD UTAMA - KECAMATAN")
        st.markdown(f"Selamat datang **{username.upper()}**. Mengawal rekapitulasi data zakat dan infaq tingkat kecamatan.")
        st.markdown("---")

        # 1. Mengambil Akumulasi Data Keseluruhan Se-Kecamatan
        c.execute("""
            SELECT 
                SUM(jiwa_beras + jiwa_uang), 
                SUM(total_beras), 
                SUM(total_uang), 
                SUM(infaq) 
            FROM setoran_dkm
        """)
        rekap_global = c.fetchone()
        
        tot_muzakki = rekap_global[0] or 0
        tot_beras = rekap_global[1] or 0
        tot_uang = rekap_global[2] or 0
        tot_infaq = rekap_global[3] or 0

        # Menampilkan Ringkasan Metrik Angka Se-Kecamatan
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Muzakki Kecamatan", f"{tot_muzakki:,} Jiwa")
        col2.metric("Total Beras Kecamatan", f"{tot_beras:,.2f} Kg")
        col3.metric("Total Uang Zakat", f"Rp {int(tot_uang):,}")
        col4.metric("Total Infaq Keseluruhan", f"Rp {int(tot_infaq):,}")

        st.markdown("---")
        
        # 2. Grafik Komparasi Perolehan Antar Desa (Fitur Eksklusif Admin)
        st.subheader("📈 Grafik Perbandingan Pengumpulan Beras per Desa")
        query_grafik = """
            SELECT alamat_dkm AS Desa, SUM(total_beras) AS 'Total Beras (Kg)' 
            FROM setoran_dkm 
            GROUP BY alamat_dkm
        """
        df_grafik = pd.read_sql_query(query_grafik, conn)
        
        if not df_grafik.empty:
            # Membuat grafik batang bawaan Streamlit yang interaktif
            st.bar_chart(data=df_grafik, x="Desa", y="Total Beras (Kg)", color="#02723A")
        else:
            st.info("Grafik belum tersedia karena belum ada data desa yang masuk.")

        st.markdown("<br>", unsafe_allow_html=True)

        # 3. Tabel Ringkasan Realtime Status Pelaporan Semua Desa
        st.subheader("📋 Status Penerimaan Terintegrasi Seluruh Desa")
        query_tabel_admin = """
            SELECT 
                alamat_dkm AS 'Nama Desa',
                COUNT(DISTINCT nama_dkm) AS 'Jumlah UPZ DKM Melapor',
                SUM(jiwa_beras + jiwa_uang) AS 'Total Muzakki (Jiwa)',
                SUM(total_beras) AS 'Total Beras (Kg)',
                SUM(total_uang) AS 'Zakat Uang (Rp)',
                SUM(infaq) AS 'Infaq (Rp)'
            FROM setoran_dkm
            GROUP BY alamat_dkm
            ORDER BY alamat_dkm ASC
        """
        df_admin = pd.read_sql_query(query_tabel_admin, conn)
        st.dataframe(df_admin, width="stretch", hide_index=True)


    # =========================================================================
    # KONDISI 2: TAMPILAN DASHBOARD UNTUK AMIL DESA (TERKUNCI SESUAI PROFIL)
    # =========================================================================
    else:
        st.title(f"📊 DASHBOARD AMIL DESA {desa_tugas.upper()}")
        st.markdown(f"Sistem Laporan Terpadu Pengumpulan Zakat & Infaq Desa **{desa_tugas}**.")
        st.markdown("---")

        # 1. Mengambil Data Spesifik yang Hanya Diinput Atas Nama Desa Sesuai Profil Tugasnya
        # Penyaringan menggunakan WHERE alamat_dkm = ?
        c.execute("""
            SELECT 
                SUM(jiwa_beras + jiwa_uang), 
                SUM(total_beras), 
                SUM(total_uang), 
                SUM(infaq) 
            FROM setoran_dkm 
            WHERE UPPER(alamat_dkm) = UPPER(?)
        """, (desa_tugas,))
        rekap_desa = c.fetchone()
        
        d_muzakki = rekap_desa[0] or 0
        d_beras = rekap_desa[1] or 0
        d_uang = rekap_desa[2] or 0
        d_infaq = rekap_desa[3] or 0

        # Menampilkan Ringkasan Metrik Angka Khusus Internal Desa Terkait
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Muzakki Internal Desa", f"{d_muzakki:,} Jiwa")
        col2.metric("Stok Beras Desa", f"{d_beras:,.2f} Kg")
        col3.metric("Uang Zakat Desa", f"Rp {int(d_uang):,}")
        col4.metric("Infaq Terhimpun", f"Rp {int(d_infaq):,}")

        st.markdown("---")

        # 2. Tabel Rincian Setoran per UPZ DKM di Dalam Wilayah Desa Tersebut
        st.subheader(f"📋 Daftar Setoran per UPZ DKM / Mushola di Wilayah {desa_tugas}")
        query_tabel_desa = """
            SELECT 
                nama_dkm AS 'Nama UPZ DKM',
                perwakilan AS 'Wakil / Wilayah',
                (jiwa_beras + jiwa_uang) AS 'Muzakki (Jiwa)',
                total_beras AS 'Beras Disetor (Kg)',
                total_uang AS 'Zakat Uang (Rp)',
                infaq AS 'Infaq Kupon (Rp)'
            FROM setoran_dkm
            WHERE UPPER(alamat_dkm) = UPPER(?)
            ORDER BY nama_dkm ASC
        """
        # Membaca data ke DataFrame pandas dengan parameter pengunci desa
        df_desa = pd.read_sql_query(query_tabel_desa, conn, params=(desa_tugas,))
        
        if not df_desa.empty:
            st.dataframe(df_desa, width="stretch", hide_index=True)
        else:
            st.info(f"Belum ada data setoran UPZ DKM yang masuk untuk wilayah Desa {desa_tugas}.")

    conn.close()