import streamlit as st
import sqlite3
import pandas as pd
from config import DB_NAME

def render():
    st.title("🕌 Data Majlis Ta'lim Desa")
    st.markdown("Kelola daftar Majlis Ta'lim, Pimpinan, dan jadwal pengajian di sini.")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Form Input Majlis
    with st.form("form_majlis"):
        st.subheader("Tambah Data Majlis")
        col1, col2 = st.columns(2)
        
        with col1:
            mj_nama = st.text_input("Nama Majlis Ta'lim:")
            mj_pimpinan = st.text_input("Nama Pimpinan:")
            mj_alamat = st.text_input("Alamat / Dusun:")
            
        with col2:
            col_rt, col_rw = st.columns(2)
            with col_rt: 
                mj_rt = st.text_input("RT:")
            with col_rw: 
                mj_rw = st.text_input("RW:")
            
            mj_hari = st.selectbox("Hari Pengajian:", ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu", "Setiap Hari", "Kondisional"])
            mj_jam = st.text_input("Jam Pengajian (Cth: 16:00 WIB):")

        if st.form_submit_button("💾 Simpan Data Majlis", width="stretch"):
            if not mj_nama:
                st.error("Nama Majlis wajib diisi!")
            else:
                c.execute("INSERT INTO majlis_talim (nama_majlis, alamat, rt, rw, hari, jam, pimpinan) VALUES (?,?,?,?,?,?,?)", 
                          (mj_nama, mj_alamat, mj_rt, mj_rw, mj_hari, mj_jam, mj_pimpinan))
                conn.commit()
                st.success(f"Berhasil! Majlis {mj_nama} ditambahkan.")
                st.rerun()

    st.markdown("---")
    st.subheader("📋 Daftar Majlis Ta'lim")
    
    # Menampilkan Tabel
    query_mj = "SELECT id as ID, nama_majlis as 'Nama Majlis', pimpinan as 'Pimpinan', alamat as 'Alamat', rt||'/'||rw as 'RT/RW', hari||', '||jam as 'Waktu Pengajian' FROM majlis_talim"
    df_mj = pd.read_sql_query(query_mj, conn)
    
    if not df_mj.empty:
        st.dataframe(df_mj, width="stretch", hide_index=True)
        
        # Fitur Hapus
        with st.expander("🗑️ Hapus Data Majlis"):
            id_hapus_mj = st.number_input("Masukkan ID Majlis yang ingin dihapus:", min_value=0, step=1, key="del_mj")
            if st.button("Hapus Data"):
                c.execute("DELETE FROM majlis_talim WHERE id=?", (id_hapus_mj,))
                conn.commit()
                st.success(f"Data dengan ID {id_hapus_mj} dihapus!")
                st.rerun()
    else:
        st.info("Belum ada data Majlis Ta'lim yang terdaftar.")
        
    conn.close()