import streamlit as st
import sqlite3
import pandas as pd
import datetime
from config import DB_NAME

def render():
    st.title("🐄 Data Hewan Qurban Desa")
    st.markdown("Kelola rekapitulasi data hewan qurban tingkat desa di sini.")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Ambil daftar DKM dari Master Data
    try:
        c.execute("SELECT nama_dkm FROM master_dkm ORDER BY nama_dkm ASC")
        daftar_dkm = [row[0] for row in c.fetchall()]
    except:
        daftar_dkm = []

    # Ambil tahun saat ini untuk nilai awal (default)
    tahun_sekarang = str(datetime.datetime.now().year)

    # ==========================================
    # FORM INPUT QURBAN
    # ==========================================
    with st.form("form_qurban"):
        st.subheader("Input Data Hewan Qurban")
        
        col1, col2 = st.columns(2)
        with col1:
            in_tahun = st.text_input("Tahun (Hijriah/Masehi):", value=tahun_sekarang)
            
            if daftar_dkm:
                in_dkm = st.selectbox("Nama DKM / Wilayah:", ["Pilih DKM/Wilayah..."] + daftar_dkm)
            else:
                in_dkm = st.text_input("Nama DKM / Wilayah (Ketik manual):")
                
            in_jenis = st.selectbox("Jenis Hewan Qurban:", ["Sapi", "Domba", "Kambing", "Kerbau"])

        with col2:
            in_hewan = st.number_input("Jumlah Hewan (Ekor):", min_value=0, value=0, step=1)
            in_mudhohi = st.number_input("Jumlah Mudhohi (Orang):", min_value=0, value=0, step=1, 
                                         help="Biarkan 0 agar dihitung otomatis (Sapi/Kerbau = 7 Org, Domba/Kambing = 1 Org).")

        submit_qurban = st.form_submit_button("💾 Simpan Data Qurban", width="stretch")

        if submit_qurban:
            if in_dkm == "Pilih DKM/Wilayah..." or not in_dkm:
                st.error("Gagal! Nama DKM / Wilayah wajib diisi.")
            elif in_hewan <= 0:
                st.error("Gagal! Jumlah hewan harus lebih dari 0.")
            else:
                # Logika hitung otomatis jika mudhohi dibiarkan 0
                if in_mudhohi == 0:
                    pengali = 7 if in_jenis in ["Sapi", "Kerbau"] else 1
                    in_mudhohi = in_hewan * pengali

                try:
                    c.execute("INSERT INTO qurban (tahun, nama_dkm, jenis_hewan, jumlah_hewan, jumlah_mudhohi) VALUES (?,?,?,?,?)", 
                              (in_tahun, in_dkm, in_jenis, in_hewan, in_mudhohi))
                    conn.commit()
                    st.success(f"Berhasil! Data Qurban dari **{in_dkm}** telah dicatat.")
                    st.rerun() # Refresh tabel
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {e}")

    # ==========================================
    # TABEL DAFTAR QURBAN
    # ==========================================
    st.markdown("---")
    st.subheader("📋 Daftar Rekapitulasi Qurban")

    query_qurban = """
    SELECT 
        id as ID, 
        tahun as Tahun, 
        nama_dkm as 'Nama DKM / Wilayah', 
        jenis_hewan as 'Jenis Hewan', 
        jumlah_hewan as 'Jml Hewan (Ekor)', 
        jumlah_mudhohi as 'Jml Mudhohi (Orang)' 
    FROM qurban 
    ORDER BY tahun DESC, nama_dkm ASC
    """
    df_qurban = pd.read_sql_query(query_qurban, conn)

    if not df_qurban.empty:
        st.dataframe(df_qurban, width="stretch", hide_index=True)

        col_del_qurban, col_edit_qurban = st.columns(2)

        # --- 1. FITUR HAPUS QURBAN ---
        with col_del_qurban:
            with st.expander("🗑️ Hapus Data Qurban"):
                id_hapus_qurban = st.number_input("Masukkan ID baris yang dihapus:", min_value=0, step=1, key="del_qurban")
                if st.button("Hapus Data Qurban", width="stretch"):
                    c.execute("DELETE FROM qurban WHERE id=?", (id_hapus_qurban,))
                    conn.commit()
                    st.success(f"Data dengan ID {id_hapus_qurban} berhasil dihapus!")
                    st.rerun()

        # --- 2. FITUR EDIT QURBAN ---
        with col_edit_qurban:
            with st.expander("✏️ Ubah Data (Edit)"):
                daftar_pil_qurban = [f"{row['ID']} - {row['Nama DKM / Wilayah']} ({row['Jenis Hewan']})" for _, row in df_qurban.iterrows()]
                pil_edit_qurban = st.selectbox("Pilih Data yang akan diedit:", ["Pilih Data..."] + daftar_pil_qurban, key="sel_edit_qurban")
                
                if pil_edit_qurban != "Pilih Data...":
                    id_edit_qurban = pil_edit_qurban.split(" - ")[0]
                    c.execute("SELECT tahun, nama_dkm, jenis_hewan, jumlah_hewan, jumlah_mudhohi FROM qurban WHERE id=?", (id_edit_qurban,))
                    r_qurban = c.fetchone()
                    
                    if r_qurban:
                        with st.form("form_edit_qurban"):
                            st.caption(f"Mengedit ID: {id_edit_qurban}")
                            e_tahun = st.text_input("Tahun:", value=r_qurban[0])
                            
                            try:
                                c.execute("SELECT nama_dkm FROM master_dkm ORDER BY nama_dkm ASC")
                                d_dkm = [row[0] for row in c.fetchall()]
                            except:
                                d_dkm = []
                                
                            if r_qurban[1] in d_dkm:
                                idx_dkm = d_dkm.index(r_qurban[1])
                                e_dkm = st.selectbox("Nama DKM / Wilayah:", d_dkm, index=idx_dkm)
                            else:
                                e_dkm = st.text_input("Nama DKM / Wilayah:", value=r_qurban[1])

                            opsi_hewan = ["Sapi", "Domba", "Kambing", "Kerbau"]
                            idx_hewan = opsi_hewan.index(r_qurban[2]) if r_qurban[2] in opsi_hewan else 0
                            e_jenis = st.selectbox("Jenis Hewan:", opsi_hewan, index=idx_hewan)
                            
                            e_hewan = st.number_input("Jml Hewan (Ekor):", value=int(r_qurban[3]), min_value=1)
                            e_mudhohi = st.number_input("Jml Mudhohi (Orang):", value=int(r_qurban[4]), min_value=0, help="Ubah jadi 0 untuk dihitung otomatis")
                            
                            if st.form_submit_button("💾 Simpan Perubahan", width="stretch"):
                                m_baru = e_mudhohi
                                
                                if m_baru == 0:
                                    pengali = 7 if e_jenis in ["Sapi", "Kerbau"] else 1
                                    m_baru = e_hewan * pengali
                                
                                c.execute("UPDATE qurban SET tahun=?, nama_dkm=?, jenis_hewan=?, jumlah_hewan=?, jumlah_mudhohi=? WHERE id=?", 
                                          (e_tahun, e_dkm, e_jenis, e_hewan, m_baru, id_edit_qurban))
                                conn.commit()
                                st.success("Data Qurban berhasil diperbarui!")
                                st.rerun()
    else:
        st.info("Belum ada data hewan qurban yang tersimpan.")

    conn.close()