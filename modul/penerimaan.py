import streamlit as st
import sqlite3
import pandas as pd
from config import DB_NAME

def render():
    st.title("📥 Penerimaan Zakat Fitrah DKM")
    
    desa_tugas = st.session_state.get("desa_tugas", "")
    st.markdown(f"Kelola data setoran zakat fitrah (Jiwa & Fisik 17.5%) dari setiap UPZ DKM di wilayah **{desa_tugas.upper()}**.")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Mengambil master data DKM sesuai desa login
    c.execute("SELECT nama_dkm FROM master_dkm WHERE UPPER(alamat_dkm) = UPPER(?) ORDER BY nama_dkm ASC", (desa_tugas,))
    daftar_dkm = [row[0] for row in c.fetchall()]
    
    if not daftar_dkm:
        c.execute("SELECT nama_dkm FROM master_dkm ORDER BY nama_dkm ASC")
        daftar_dkm = [row[0] for row in c.fetchall()]

    # Mengambil tarif dari pengaturan
    c.execute("SELECT tarif_beras, tarif_uang FROM pengaturan WHERE id=1")
    res_tarif = c.fetchone()
    t_b = res_tarif[0] if res_tarif and res_tarif[0] else 2.5
    t_u = res_tarif[1] if res_tarif and res_tarif[1] else 35000

    st.markdown("---")
    st.subheader("Form Input Setoran Zakat")
    
    # Pilih DKM
    selected_dkm = st.selectbox("Pilih UPZ DKM Induk:", ["Pilih DKM..."] + daftar_dkm) if daftar_dkm else st.text_input("Nama UPZ DKM Induk:")

    # -----------------------------------------------------------
    # PROTEKSI INPUT GANDA (Cek apakah DKM sudah setor)
    # -----------------------------------------------------------
    is_duplicate = False
    if selected_dkm and selected_dkm != "Pilih DKM...":
        c.execute("SELECT id FROM setoran_dkm WHERE nama_dkm=? AND UPPER(alamat_dkm)=UPPER(?)", (selected_dkm, desa_tugas))
        if c.fetchone():
            is_duplicate = True
            st.error(f"⚠️ Peringatan: Data setoran zakat untuk UPZ DKM **{selected_dkm}** sudah ada di database! Gunakan fitur **Edit** di bawah jika ingin mengubah data.")

    # Ambil data perwakilan DKM
    wakil_list = []
    if selected_dkm and selected_dkm != "Pilih DKM...":
        c.execute("SELECT perwakilan FROM master_dkm WHERE nama_dkm=?", (selected_dkm,))
        res_master = c.fetchone()
        if res_master and res_master[0]:
            wakil_list = [x.strip() for x in res_master[0].split(",") if x.strip()]

    # Kontainer Input Utama (Reaktif / Realtime)
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            alamat_dkm = st.text_input("Desa Induk (Otomatis):", value=desa_tugas, disabled=True)
            alamat_wakil = st.text_input("Cakupan Wilayah / Alamat Wakil:")
        with col2:
            if wakil_list:
                wakil_upz = st.selectbox("Wakil UPZ / Mushola:", ["Pusat (Tidak ada wakil)"] + wakil_list)
                wakil_upz = "" if wakil_upz == "Pusat (Tidak ada wakil)" else wakil_upz
            else:
                wakil_upz = st.text_input("Wakil UPZ (Manual):")

        st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
        st.write("📝 **Rincian Perhitungan Zakat Fitrah**")
        
        mode_input = st.radio("Metode Kalkulasi Zakat:", ["Berdasarkan Data Jiwa", "Berdasarkan Setoran Fisik (17.5%)"], horizontal=True)
        
        col_j, col_f = st.columns(2)
        
        # -----------------------------------------------------------
        # LOGIKA PERHITUNGAN OTOMATIS (BIDIRECTIONAL REALTIME)
        # -----------------------------------------------------------
        if mode_input == "Berdasarkan Data Jiwa":
            with col_j:
                j_b = st.number_input("Jumlah Muzakki Beras (Jiwa):", min_value=0, value=0)
                j_u = st.number_input("Jumlah Muzakki Uang (Jiwa):", min_value=0, value=0)
            
            # Sistem menghitung fisik penyerahan ke desa (17.5%)
            tb = j_b * t_b; tu = j_u * t_u
            f_b_calc = tb * 0.175; f_u_calc = tu * 0.175
            
            with col_f:
                st.number_input("Fisik Beras Disetor ke UPZ Desa (Kg):", value=float(f_b_calc), disabled=True)
                st.number_input("Fisik Uang Disetor ke UPZ Desa (Rp):", value=int(f_u_calc), disabled=True)
                f_b, f_u = f_b_calc, f_u_calc

        else: # Mode Fisik disetor
            with col_f:
                f_b = st.number_input("Fisik Beras Disetor ke UPZ Desa (Kg):", min_value=0.0, value=0.0, step=0.5)
                f_u = st.number_input("Fisik Uang Disetor ke UPZ Desa (Rp):", min_value=0, value=0, step=1000)
            
            # Sistem membalikkan hitungan ke total jiwa global (100%)
            tb_calc = f_b / 0.175 if f_b > 0 else 0
            tu_calc = f_u / 0.175 if f_u > 0 else 0
            j_b_calc = int(round(tb_calc / t_b)) if t_b > 0 else 0
            j_u_calc = int(round(tu_calc / t_u)) if t_u > 0 else 0
            
            with col_j:
                st.number_input("Estimasi Muzakki Beras (Jiwa):", value=j_b_calc, disabled=True)
                st.number_input("Estimasi Muzakki Uang (Jiwa):", value=j_u_calc, disabled=True)
                j_b, j_u = j_b_calc, j_u_calc
                tb, tu = tb_calc, tu_calc

        st.markdown("<br>", unsafe_allow_html=True)

        # -----------------------------------------------------------
        # TOMBOL SIMPAN (Dengan Proteksi Input Ganda)
        # -----------------------------------------------------------
        if st.button("💾 Simpan Data Setoran Zakat", width="stretch", type="primary", disabled=is_duplicate):
            if selected_dkm == "Pilih DKM...":
                st.warning("Harap pilih nama UPZ DKM terlebih dahulu!")
            else:
                tipe_input_db = "jiwa" if mode_input == "Berdasarkan Data Jiwa" else "fisik"
                # Mengisi infaq dan kupon dengan nilai 0 karena sudah dipisah ke modul sendiri
                c.execute('''INSERT INTO setoran_dkm (nama_dkm, alamat_dkm, perwakilan, alamat_perwakilan, tipe_input, jiwa_beras, jiwa_uang, fisik_beras, fisik_uang, total_beras, total_uang, infaq, kupon_diterima, kupon_terjual, kupon_kembali) VALUES (?,?,?,?,?,?,?,?,?,?,?,0,0,0,0)''', 
                          (selected_dkm, desa_tugas, wakil_upz, alamat_wakil, tipe_input_db, j_b, j_u, f_b, f_u, tb, tu))
                conn.commit()
                st.success(f"Berhasil! Data zakat dari UPZ DKM **{selected_dkm}** telah disimpan.")
                st.rerun()

    st.markdown("---")
    st.subheader("📋 Daftar Penerimaan Zakat Terkini")
    
    query_setoran = """
    SELECT id as id_asli, nama_dkm as 'Nama DKM', perwakilan as 'Wakil/Mushola', (jiwa_beras + jiwa_uang) as 'Total Jiwa', total_beras as 'Total Beras 100% (Kg)', total_uang as 'Total Uang 100% (Rp)', fisik_beras as 'Setor Fisik Beras (Kg)', fisik_uang as 'Setor Fisik Uang (Rp)' 
    FROM setoran_dkm WHERE UPPER(alamat_dkm) = UPPER(?) ORDER BY id DESC
    """
    df_setoran = pd.read_sql_query(query_setoran, conn, params=(desa_tugas,))
    
    if not df_setoran.empty:
        df_tampil = df_setoran.copy()
        df_tampil.insert(0, "No.", range(1, len(df_tampil) + 1))
        st.dataframe(df_tampil.drop(columns=["id_asli"]), width="stretch", hide_index=True)
        
        col_del, col_edit = st.columns(2)
        
        # --- FITUR HAPUS ---
        with col_del:
            with st.expander("🗑️ Hapus Data Setoran"):
                opsi_hapus = [f"No. {row['No.']} - {row['Nama DKM']}" for _, row in df_tampil.iterrows()]
                pil_hapus = st.selectbox("Pilih Data Zakat yang Dihapus:", ["Pilih Data..."] + opsi_hapus)
                
                if st.button("Hapus Data Zakat", width="stretch", type="primary"):
                    if pil_hapus != "Pilih Data...":
                        no_urut = int(pil_hapus.split(" - ")[0].replace("No. ", ""))
                        id_target = int(df_tampil[df_tampil["No."] == no_urut]["id_asli"].values[0])
                        c.execute("DELETE FROM setoran_dkm WHERE id=?", (id_target,))
                        conn.commit(); st.success("Data zakat berhasil dihapus!"); st.rerun()
                    else:
                        st.warning("Pilih data terlebih dahulu.")
                        
        # --- FITUR EDIT ---
        with col_edit:
            with st.expander("✏️ Ubah Data Zakat (Edit)"):
                opsi_edit = [f"No. {row['No.']} - {row['Nama DKM']}" for _, row in df_tampil.iterrows()]
                pil_edit = st.selectbox("Pilih Data Zakat yang Diedit:", ["Pilih Data..."] + opsi_edit)
                
                if pil_edit != "Pilih Data...":
                    no_urut_edit = int(pil_edit.split(" - ")[0].replace("No. ", ""))
                    id_edit = int(df_tampil[df_tampil["No."] == no_urut_edit]["id_asli"].values[0])
                    
                    c.execute("SELECT nama_dkm, jiwa_beras, jiwa_uang, fisik_beras, fisik_uang, tipe_input FROM setoran_dkm WHERE id=?", (id_edit,))
                    row_edit = c.fetchone()
                    
                    if row_edit:
                        with st.form("form_edit_penerimaan"):
                            st.caption(f"Mengedit Setoran: {row_edit[0]}")
                            mode_edit = st.radio("Prioritas Hitung Saat Disimpan Ulang:", ["Pegang Data Jiwa", "Pegang Data Fisik"])
                            
                            c_e1, c_e2 = st.columns(2)
                            with c_e1:
                                e_jb = st.number_input("Jiwa Beras:", value=int(row_edit[1] or 0))
                                e_ju = st.number_input("Jiwa Uang:", value=int(row_edit[2] or 0))
                            with c_e2:
                                e_fb = st.number_input("Fisik Beras Disetor:", value=float(row_edit[3] or 0.0), step=0.5)
                                e_fu = st.number_input("Fisik Uang Disetor:", value=int(row_edit[4] or 0), step=1000)
                            
                            if st.form_submit_button("💾 Simpan Perubahan Edit Zakat", width="stretch"):
                                if mode_edit == "Pegang Data Jiwa":
                                    t_b_baru = e_jb * t_b; t_u_baru = e_ju * t_u
                                    e_fb = t_b_baru * 0.175; e_fu = t_u_baru * 0.175
                                else:
                                    t_b_baru = e_fb / 0.175 if e_fb > 0 else 0
                                    t_u_baru = e_fu / 0.175 if e_fu > 0 else 0
                                    e_jb = int(round(t_b_baru / t_b)) if t_b > 0 else 0
                                    e_ju = int(round(t_u_baru / t_u)) if t_u > 0 else 0
                                
                                c.execute('''UPDATE setoran_dkm SET jiwa_beras=?, jiwa_uang=?, fisik_beras=?, fisik_uang=?, total_beras=?, total_uang=? WHERE id=?''', 
                                          (e_jb, e_ju, e_fb, e_fu, t_b_baru, t_u_baru, id_edit))
                                conn.commit(); st.success("Data zakat berhasil diperbarui!"); st.rerun()
    else: 
        st.info(f"Belum ada data setoran zakat fitrah yang masuk untuk wilayah Desa {desa_tugas.upper()}.")
        
    conn.close()