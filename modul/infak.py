import streamlit as st
import sqlite3
import pandas as pd
import datetime
import os
import time  
from config import DB_NAME

def render():
    st.title("🎟️ Penerimaan Infaq Kupon DKM")
    
    # Mengambil profil desa pengguna yang sedang login
    desa_tugas = st.session_state.get("desa_tugas", "")
    st.markdown(f"Kelola data setoran Kupon Infaq, sirkulasi fisik, dan audit selisih dari setiap UPZ DKM di wilayah **{desa_tugas.upper()}**.")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Membuat tabel otomatis untuk Kupon Infaq versi sinkron DKM
    c.execute('''CREATE TABLE IF NOT EXISTS kupon_infaq (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tanggal TEXT,
        nama_dkm TEXT,
        alamat_dkm TEXT,
        perwakilan TEXT,
        alamat_perwakilan TEXT,
        jumlah_awal INTEGER,
        kupon_kembali INTEGER,
        nominal_disetor REAL,
        kupon_laku INTEGER,
        kupon_hilang INTEGER,
        nilai_lembar REAL,
        desa_pengelola TEXT
    )''')
    
    # --- SISTEM AUTO-PATCH DATABASE ---
    try: c.execute("ALTER TABLE kupon_infaq ADD COLUMN nama_dkm TEXT")
    except: pass
    try: c.execute("ALTER TABLE kupon_infaq ADD COLUMN alamat_dkm TEXT")
    except: pass
    try: c.execute("ALTER TABLE kupon_infaq ADD COLUMN perwakilan TEXT")
    except: pass
    try: c.execute("ALTER TABLE kupon_infaq ADD COLUMN alamat_perwakilan TEXT")
    except: pass
    try: c.execute("ALTER TABLE kupon_infaq ADD COLUMN kupon_kembali INTEGER DEFAULT 0")
    except: pass
    try: c.execute("ALTER TABLE kupon_infaq ADD COLUMN nominal_disetor REAL DEFAULT 0")
    except: pass
    try: c.execute("ALTER TABLE kupon_infaq ADD COLUMN kupon_laku INTEGER DEFAULT 0")
    except: pass
    try: c.execute("ALTER TABLE kupon_infaq ADD COLUMN kupon_hilang INTEGER DEFAULT 0")
    except: pass
    conn.commit()

    # Mengambil master data DKM sesuai desa login untuk sinkronisasi otomatis
    c.execute("SELECT nama_dkm FROM master_dkm WHERE UPPER(alamat_dkm) = UPPER(?) ORDER BY nama_dkm ASC", (desa_tugas,))
    daftar_dkm = [row[0] for row in c.fetchall()]
    
    if not daftar_dkm:
        c.execute("SELECT nama_dkm FROM master_dkm ORDER BY nama_dkm ASC")
        daftar_dkm = [row[0] for row in c.fetchall()]

    # Mengambil pengaturan default dari profil
    c.execute("SELECT nominal_kupon FROM pengaturan WHERE id=1")
    res_pengaturan = c.fetchone()
    default_nilai = int(res_pengaturan[0]) if res_pengaturan and res_pengaturan[0] else 0

    st.markdown("---")
    st.subheader("Form Input Setoran Kupon Infaq")
    
    selected_dkm = st.selectbox("Pilih UPZ DKM Sumber Pemasukan:", ["Pilih DKM..."] + daftar_dkm) if daftar_dkm else st.text_input("Nama UPZ DKM Induk:")

    is_duplicate = False
    if selected_dkm and selected_dkm != "Pilih DKM...":
        c.execute("SELECT id FROM kupon_infaq WHERE nama_dkm=? AND UPPER(desa_pengelola)=UPPER(?)", (selected_dkm, desa_tugas))
        if c.fetchone():
            is_duplicate = True
            st.error(f"⚠️ Peringatan: Data setoran kupon infaq untuk UPZ DKM **{selected_dkm}** sudah ada! Gunakan fitur **Hapus** di bawah jika ingin mengulang/merevisi data.")

    wakil_list = []
    if selected_dkm and selected_dkm != "Pilih DKM...":
        c.execute("SELECT perwakilan FROM master_dkm WHERE nama_dkm=?", (selected_dkm,))
        res_master = c.fetchone()
        if res_master and res_master[0]:
            wakil_list = [x.strip() for x in res_master[0].split(",") if x.strip()]

    with st.container(border=True):
        tgl_hari_ini = datetime.datetime.now().strftime("%d-%m-%Y")
        
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            in_tgl = st.text_input("Tanggal Setoran:", value=tgl_hari_ini)
            alamat_dkm = st.text_input("Desa Induk (Otomatis Sinkron):", value=desa_tugas, disabled=True)
        with col_a2:
            if wakil_list:
                wakil_upz = st.selectbox("Wakil UPZ / Mushola:", ["Pusat (Tidak ada wakil)"] + wakil_list)
                wakil_upz = "" if wakil_upz == "Pusat (Tidak ada wakil)" else wakil_upz
            else:
                wakil_upz = st.text_input("Wakil UPZ (Manual):")
            alamat_wakil = st.text_input("Cakupan Wilayah / Alamat Wakil DKM:")

        st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
        st.write("📊 **Audit Sirkulasi Fisik & Nominal Uang Infaq (Bidirectional Reaktif)**")
        
        mode_hitung = st.radio("Metode Pengisian Data:", ["Berdasarkan Jumlah Kupon Keluar", "Berdasarkan Nominal Uang Tunai Disetor"], horizontal=True)
        
        col_k, col_u = st.columns(2)
        
        in_nilai = st.number_input("Nilai Kupon / Lembar (Rp) - [SINKRON PENGATURAN]:", min_value=0, value=default_nilai, step=500, disabled=True)
        
        if mode_hitung == "Berdasarkan Jumlah Kupon Keluar":
            with col_k:
                in_awal = st.number_input("Banyaknya Kupon Awal Diterima DKM (Lbr):", min_value=0, value=0, step=1)
                in_terjual = st.number_input("Jumlah Kupon Keluar / Terjual (Lbr):", min_value=0, value=0, step=1)
                in_kembali = st.number_input("Fisik Kupon Sisa Dikembalikan (Lbr):", min_value=0, value=0, step=1)
            
            in_uang_calc = in_terjual * in_nilai
            kupon_laku_calc = in_terjual
            sisa_seharusnya = in_awal - in_terjual
            kupon_hilang_calc = sisa_seharusnya - in_kembali
            
            with col_u:
                st.number_input("Nominal Uang Harus Disetor (Rp) - [TERHITUNG]:", value=int(in_uang_calc), disabled=True)
                st.number_input("Audit Selisih / Kupon Hilang (Lbr) - [TERHITUNG]:", value=int(kupon_hilang_calc), disabled=True)
                
            in_uang = in_uang_calc
            kupon_laku = kupon_laku_calc
            kupon_hilang = kupon_hilang_calc
            
        else: 
            with col_u:
                in_uang = st.number_input("Nominal Uang Tunai Nyata Disetor (Rp):", min_value=0, value=0, step=1000)
                in_awal = st.number_input("Banyaknya Kupon Awal Diterima DKM (Lbr):", min_value=0, value=0, step=1)
                in_kembali = st.number_input("Fisik Kupon Sisa Dikembalikan (Lbr):", min_value=0, value=0, step=1)
            
            kupon_laku_calc = int(in_uang // in_nilai) if in_nilai > 0 else 0
            sisa_seharusnya = in_awal - kupon_laku_calc
            kupon_hilang_calc = sisa_seharusnya - in_kembali
            
            with col_k:
                st.number_input("Konversi Kupon Laku Terjual (Lbr) - [TERHITUNG]:", value=kupon_laku_calc, disabled=True)
                st.number_input("Audit Selisih / Kupon Hilang (Lbr) - [TERHITUNG]:", value=int(kupon_hilang_calc), disabled=True)
                
            in_terjual = kupon_laku_calc
            kupon_laku = kupon_laku_calc
            kupon_hilang = kupon_hilang_calc

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("💾 Simpan Data Setoran Infaq", width="stretch", type="primary", disabled=is_duplicate):
            if selected_dkm == "Pilih DKM...":
                st.warning("Harap pilih nama UPZ DKM terlebih dahulu!")
            elif in_terjual > in_awal:
                st.error("Gagal! Jumlah kupon laku terjual tidak logis melebihi kupon awal.")
            else:
                c.execute('''INSERT INTO kupon_infaq (tanggal, nama_dkm, alamat_dkm, perwakilan, alamat_perwakilan, jumlah_awal, kupon_kembali, nominal_disetor, kupon_laku, kupon_hilang, nilai_lembar, desa_pengelola) 
                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', 
                          (in_tgl, selected_dkm, desa_tugas, wakil_upz, alamat_wakil, in_awal, in_kembali, float(in_uang), kupon_laku, kupon_hilang, in_nilai, desa_tugas))
                
                c.execute("UPDATE setoran_dkm SET infaq=?, kupon_diterima=?, kupon_terjual=?, kupon_kembali=? WHERE nama_dkm=? AND UPPER(alamat_dkm)=UPPER(?)",
                          (float(in_uang), in_awal, kupon_laku, in_kembali, selected_dkm, desa_tugas))
                
                conn.commit()
                st.success(f"Berhasil! Data infaq kupon dari UPZ DKM **{selected_dkm}** tersimpan dan tersinkronisasi.")
                
                time.sleep(1.5)  
                st.rerun()

    st.markdown("---")
    st.subheader("📋 Daftar Riwayat Setoran Kupon Infaq")
    
    query_kupon = """
    SELECT 
        id as id_asli, 
        tanggal as 'Tanggal', 
        nama_dkm as 'Nama UPZ DKM', 
        perwakilan as 'Wakil/Mushola',
        jumlah_awal as 'Awal (Lbr)', 
        kupon_laku as 'Terjual (Lbr)', 
        kupon_kembali as 'Kembali (Lbr)',
        kupon_hilang as 'Kurang/Hilang',
        nominal_disetor as 'Uang Masuk (Rp)'
    FROM kupon_infaq 
    WHERE UPPER(desa_pengelola) = UPPER(?)
    ORDER BY id DESC
    """
    df_kupon = pd.read_sql_query(query_kupon, conn, params=(desa_tugas,))
    
    if not df_kupon.empty:
        df_tampil = df_kupon.copy()
        df_tampil.insert(0, "No.", range(1, len(df_tampil) + 1))
        
        def color_hilang(val):
            return 'color: #ff4b4b' if val > 0 else ''
            
        st.dataframe(df_tampil.drop(columns=["id_asli"]).style.map(color_hilang, subset=['Kurang/Hilang']), width="stretch", hide_index=True)
        
        col_info, col_del = st.columns([1.5, 1])
        
        with col_info:
            st.info("💡 **Informasi:** Untuk mencetak Dokumen Berita Acara Serah Terima (BAST) Kupon Infaq, silakan buka menu **🖨️ Cetak Laporan PDF** di panel samping.")

        with col_del:
            with st.expander("🗑️ Hapus Data Setoran"):
                opsi_hapus = [f"No. {row['No.']} - {row['Nama UPZ DKM']}" for _, row in df_tampil.iterrows()]
                pil_hapus = st.selectbox("Pilih Baris yang Ingin Dihapus:", ["Pilih Data..."] + opsi_hapus)
                
                if st.button("Eksekusi Hapus Data", width="stretch", type="primary"):
                    if pil_hapus != "Pilih Data...":
                        no_urut = int(pil_hapus.split(" - ")[0].replace("No. ", ""))
                        baris_data = df_tampil[df_tampil["No."] == no_urut].iloc[0]
                        id_target = int(baris_data["id_asli"])
                        nama_dkm_target = baris_data["Nama UPZ DKM"]
                        
                        c.execute("DELETE FROM kupon_infaq WHERE id=?", (id_target,))
                        c.execute("UPDATE setoran_dkm SET infaq=0, kupon_diterima=0, kupon_terjual=0, kupon_kembali=0 WHERE nama_dkm=? AND UPPER(alamat_dkm)=UPPER(?)", (nama_dkm_target, desa_tugas))
                        
                        conn.commit()
                        st.success("Data berhasil dihapus!")
                        st.rerun()
                    else:
                        st.warning("Silakan tentukan baris data terlebih dahulu.")
    else:
        st.info(f"Belum ada data sirkulasi kupon infaq untuk wilayah Desa {desa_tugas.upper()}.")

    conn.close()