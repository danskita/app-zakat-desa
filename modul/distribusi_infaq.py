import streamlit as st
import sqlite3
import pandas as pd
from config import DB_NAME

def render():
    st.title("📤 Distribusi Infaq & Sedekah (Guru Ngaji)")
    
    desa_tugas = st.session_state.get("desa_tugas", "")
    st.markdown(f"Sistem otomatis kalkulasi dan penyaluran proporsional Infaq (hasil Kupon) untuk Insentif Guru Ngaji di wilayah **{desa_tugas.upper()}**.")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # --- AUTO PATCH DATABASE ---
    try: c.execute("ALTER TABLE distribusi_ngaji ADD COLUMN desa_pengelola TEXT")
    except: pass
    conn.commit()

    # 1. AMBIL TOTAL INFAQ MASUK (DARI ZAKAT/KUPON)
    c.execute("SELECT SUM(infaq) FROM setoran_dkm WHERE UPPER(alamat_dkm)=UPPER(?)", (desa_tugas,))
    res_infaq_masuk = c.fetchone()
    total_infaq_masuk = res_infaq_masuk[0] if res_infaq_masuk and res_infaq_masuk[0] else 0

    # 2. AMBIL DATA GURU NGAJI DARI MASTER
    df_guru = pd.read_sql_query("SELECT * FROM guru_ngaji WHERE UPPER(desa_pengelola)=UPPER(?) ORDER BY nama ASC", conn, params=(desa_tugas,))

    st.markdown("---")
    st.subheader("📊 Alokasi Insentif Guru Ngaji (Sistem Bobot Proporsional)")
    st.info(f"Total Dana Infaq Terkumpul: **Rp {int(total_infaq_masuk):,}**")

    if not df_guru.empty:
        # Menghitung Total Bobot Guru Ngaji
        total_bobot_guru = df_guru['bobot'].sum()
        if total_bobot_guru == 0:
            total_bobot_guru = 1 # Hindari error pembagian dengan 0 jika bobot 0
            
        # Menghitung porsi masing-masing guru berdasarkan bobotnya
        df_guru['Alokasi Insentif (Rp)'] = (df_guru['bobot'] / total_bobot_guru) * total_infaq_masuk
        
        # Format tampilan
        df_tampil = df_guru.copy()
        df_tampil['Alokasi Insentif (Rp)'] = df_tampil['Alokasi Insentif (Rp)'].apply(lambda x: f"Rp {int(x):,}")
        
        st.dataframe(df_tampil[['nama', 'lembaga', 'dkm', 'bobot', 'Alokasi Insentif (Rp)']].rename(
            columns={'nama': 'Nama Guru', 'lembaga': 'Lembaga', 'dkm': 'Asal UPZ DKM', 'bobot': 'Bobot'}
        ), width="stretch", hide_index=True)
        
        # LOGIKA SINKRONISASI OTOMATIS KE DATABASE
        if st.button("🔄 Sinkronkan Kalkulasi ini ke Laporan PDF", width="stretch", type="primary"):
            # Bersihkan riwayat penyaluran infaq desa ini sebelumnya
            c.execute("DELETE FROM distribusi_ngaji WHERE UPPER(desa_pengelola)=UPPER(?)", (desa_tugas,))
            
            # Masukkan data hitungan baru secara proporsional
            for _, row in df_guru.iterrows():
                alokasi_uang = (row['bobot'] / total_bobot_guru) * total_infaq_masuk
                c.execute("INSERT INTO distribusi_ngaji (nama, lembaga, dkm, alamat, uang, bobot, desa_pengelola) VALUES (?,?,?,?,?,?,?)", 
                          (row['nama'], row['lembaga'], row['dkm'], row['alamat'], alokasi_uang, row['bobot'], desa_tugas))
            
            conn.commit()
            st.success("Tersinkronisasi! Data distribusi insentif Guru Ngaji telah direkam secara otomatis dan siap dicetak.")
            st.rerun()
            
    else:
        st.warning("⚠️ Belum ada Guru Ngaji yang terdaftar! Silakan daftarkan dulu di menu **📂 Kelola Data Master** (Tab Guru Ngaji).")

    # --- TABEL DATA TERSIMPAN ---
    st.markdown("---")
    st.subheader("📋 Data Distribusi Tersimpan")
    
    query_riwayat = """
    SELECT nama as 'Nama Penerima', lembaga as 'Lembaga', dkm as 'Asal DKM', bobot as 'Bobot', uang as 'Nominal (Rp)' 
    FROM distribusi_ngaji 
    WHERE UPPER(desa_pengelola) = UPPER(?) 
    ORDER BY nama ASC
    """
    df_riwayat = pd.read_sql_query(query_riwayat, conn, params=(desa_tugas,))
    
    if not df_riwayat.empty:
        df_riwayat_tampil = df_riwayat.copy()
        df_riwayat_tampil.insert(0, "No.", range(1, len(df_riwayat_tampil) + 1))
        df_riwayat_tampil['Nominal (Rp)'] = df_riwayat_tampil['Nominal (Rp)'].apply(lambda x: f"Rp {int(x):,}")
        st.dataframe(df_riwayat_tampil, width="stretch", hide_index=True)
    else:
        st.info("Belum ada data distribusi yang tersimpan di database. Silakan klik tombol Sinkronkan di atas.")

    conn.close()