import streamlit as st
import sqlite3
import pandas as pd
from config import DB_NAME

def render():
    st.title("📁 Arsip Data Tahunan")
    st.markdown("Lihat dan kelola kembali data laporan zakat dari tahun-tahun sebelumnya.")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Ambil daftar tahun yang ada di database arsip
    c.execute('''
        SELECT tahun_arsip FROM arsip_setoran_dkm
        UNION SELECT tahun_arsip FROM arsip_sabilillah
        UNION SELECT tahun_arsip FROM arsip_amilin
        UNION SELECT tahun_arsip FROM arsip_distribusi_ngaji
    ''')
    tahun_list = sorted([str(r[0]) for r in c.fetchall()], reverse=True)

    if not tahun_list:
        st.info("Belum ada data arsip yang tersimpan. Kamu bisa mengarsipkan data tahun ini melalui menu 'Pengaturan'.")
    else:
        # Form Pemilihan Tahun Arsip
        col_thn, col_btn = st.columns([2, 1])
        with col_thn:
            pilih_tahun = st.selectbox("Pilih Tahun Arsip:", tahun_list)
        
        with col_btn:
            st.write("") 
            st.write("")
            with st.popover("⚠️ Opsi Berbahaya"):
                st.warning(f"Hapus seluruh arsip tahun {pilih_tahun}?")
                if st.button("Ya, Hapus Permanen", type="primary"):
                    c.execute("DELETE FROM arsip_setoran_dkm WHERE tahun_arsip=?", (pilih_tahun,))
                    c.execute("DELETE FROM arsip_sabilillah WHERE tahun_arsip=?", (pilih_tahun,))
                    c.execute("DELETE FROM arsip_amilin WHERE tahun_arsip=?", (pilih_tahun,))
                    c.execute("DELETE FROM arsip_distribusi_ngaji WHERE tahun_arsip=?", (pilih_tahun,))
                    conn.commit()
                    st.success(f"Arsip tahun {pilih_tahun} dihapus!")
                    st.rerun()

        st.markdown("---")
        
        tab_a1, tab_a2, tab_a3, tab_a4 = st.tabs(["📥 DKM", "📤 Sabilillah", "👔 Amilin", "📖 Guru Ngaji"])
        
        with tab_a1:
            df_a1 = pd.read_sql_query(f"SELECT id as ID, nama_dkm as 'Nama DKM', total_beras as 'Beras (Kg)', total_uang as 'Uang Zakat (Rp)', infaq as 'Infaq (Rp)' FROM arsip_setoran_dkm WHERE tahun_arsip='{pilih_tahun}'", conn)
            st.dataframe(df_a1, width="stretch", hide_index=True)
            
        with tab_a2:
            df_a2 = pd.read_sql_query(f"SELECT id as ID, program as 'Program', penerima as 'Penerima', beras as 'Beras (Kg)', uang as 'Uang (Rp)' FROM arsip_sabilillah WHERE tahun_arsip='{pilih_tahun}'", conn)
            st.dataframe(df_a2, width="stretch", hide_index=True)
            
        with tab_a3:
            df_a3 = pd.read_sql_query(f"SELECT id as ID, nama as 'Nama', jabatan as 'Jabatan', beras as 'Beras (Kg)', uang as 'Uang (Rp)' FROM arsip_amilin WHERE tahun_arsip='{pilih_tahun}'", conn)
            st.dataframe(df_a3, width="stretch", hide_index=True)
            
        with tab_a4:
            df_a4 = pd.read_sql_query(f"SELECT id as ID, nama as 'Nama', lembaga as 'Lembaga', dkm as 'DKM', uang as 'Uang (Rp)' FROM arsip_distribusi_ngaji WHERE tahun_arsip='{pilih_tahun}'", conn)
            st.dataframe(df_a4, width="stretch", hide_index=True)

    conn.close()