import streamlit as st
import sqlite3
import pandas as pd
from config import DB_NAME

def render():
    st.title("📂 Kelola Data Master")
    
    desa_tugas = st.session_state.get("desa_tugas", "")
    st.markdown(f"Kelola data UPZ DKM, Guru Ngaji, serta persentase distribusi untuk wilayah **{desa_tugas.upper()}**.")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # --- AUTO PATCH DATABASE ---
    try: c.execute("ALTER TABLE guru_ngaji ADD COLUMN desa_pengelola TEXT")
    except: pass
    try: c.execute("ALTER TABLE master_dkm ADD COLUMN alamat_spesifik TEXT")
    except: pass
    try: c.execute("ALTER TABLE master_jabatan_amil ADD COLUMN nama_pengurus TEXT")
    except: pass
    try: c.execute("ALTER TABLE guru_ngaji ADD COLUMN bobot REAL DEFAULT 1.0")
    except: pass
    conn.commit()

    tab_dkm, tab_ngaji, tab_sab, tab_amil = st.tabs([
        "🕌 Master UPZ DKM", "📖 Master Guru Ngaji", "📌 Kategori Sabilillah", "👔 Jabatan Amilin"
    ])

    # ================= TAB 1: MASTER DKM =================
    with tab_dkm:
        with st.form("form_dkm"):
            st.subheader("Tambah UPZ DKM Baru")
            col1, col2 = st.columns(2)
            with col1:
                in_nama = st.text_input("Nama UPZ DKM (Misal: AL-IKHLAS):")
                in_ketua = st.text_input("Nama Ketua DKM:")
                in_alamat_spesifik = st.text_input("Alamat DKM / Dusun / RT RW:")
            with col2:
                in_alamat = st.text_input("Desa Induk (Otomatis):", value=desa_tugas, disabled=True)
                in_wakil = st.text_input("Daftar Wakil / Mushola (Pisahkan dengan koma):")
            
            if st.form_submit_button("💾 Simpan Data DKM", width="stretch"):
                if in_nama:
                    c.execute("INSERT INTO master_dkm (nama_dkm, ketua_dkm, alamat_dkm, perwakilan, alamat_spesifik) VALUES (?,?,?,?,?)", 
                              (in_nama.upper(), in_ketua, desa_tugas, in_wakil, in_alamat_spesifik))
                    conn.commit(); st.success(f"Berhasil menambahkan DKM {in_nama}"); st.rerun()
                else:
                    st.error("Nama DKM tidak boleh kosong!")

        st.markdown("---")
        df_dkm = pd.read_sql_query("SELECT id as ID, nama_dkm as 'Nama DKM', ketua_dkm as 'Ketua', alamat_spesifik as 'Alamat DKM', perwakilan as 'Wakil' FROM master_dkm WHERE UPPER(alamat_dkm)=UPPER(?)", conn, params=(desa_tugas,))
        if not df_dkm.empty:
            df_tampil = df_dkm.copy()
            df_tampil.insert(0, "No.", range(1, len(df_tampil) + 1))
            st.dataframe(df_tampil.drop(columns=["ID"]), width="stretch", hide_index=True)
            
            with st.expander("🗑️ Hapus Data DKM"):
                opsi_hapus = [f"No. {row['No.']} - {row['Nama DKM']}" for _, row in df_tampil.iterrows()]
                pil_hapus = st.selectbox("Pilih DKM yang Dihapus:", ["Pilih Data..."] + opsi_hapus)
                if st.button("Hapus DKM", width="stretch", type="primary"):
                    if pil_hapus != "Pilih Data...":
                        id_target = int(df_tampil[df_tampil["No."] == int(pil_hapus.split(" - ")[0].replace("No. ", ""))]["ID"].values[0])
                        c.execute("DELETE FROM master_dkm WHERE id=?", (id_target,))
                        conn.commit(); st.success("Terhapus!"); st.rerun()

    # ================= TAB 2: GURU NGAJI =================
    with tab_ngaji:
        with st.form("form_ngaji"):
            st.subheader("Tambah Data Guru Ngaji / Diniyah")
            col1, col2 = st.columns(2)
            with col1:
                in_ngaji_nama = st.text_input("Nama Pengajar / Ustadz:")
                in_ngaji_lembaga = st.text_input("Nama Lembaga / Pengajian:")
                in_ngaji_bobot = st.number_input("Bobot Pembagian (Angka Bebas):", min_value=1.0, value=1.0)
            with col2:
                c.execute("SELECT nama_dkm FROM master_dkm WHERE UPPER(alamat_dkm) = UPPER(?) ORDER BY nama_dkm ASC", (desa_tugas,))
                daftar_dkm = [row[0] for row in c.fetchall()]
                
                if daftar_dkm:
                    in_ngaji_dkm = st.selectbox("UPZ DKM Terkait (Sinkron Master):", ["Pilih DKM..."] + daftar_dkm)
                else:
                    in_ngaji_dkm = st.text_input("UPZ DKM Terkait (Ketik Manual karena Master kosong):")
                
                st.info("💡 *Alamat Guru Ngaji akan otomatis ditarik dari Alamat Spesifik DKM.*")
            
            if st.form_submit_button("💾 Simpan Guru Ngaji", width="stretch"):
                if not in_ngaji_nama or in_ngaji_dkm == "Pilih DKM...":
                    st.error("Nama dan DKM Terkait wajib diisi!")
                else:
                    c.execute("SELECT alamat_spesifik FROM master_dkm WHERE nama_dkm=?", (in_ngaji_dkm,))
                    res_alamat = c.fetchone()
                    alamat_otomatis = res_alamat[0] if res_alamat and res_alamat[0] else "-" 
                    
                    c.execute("INSERT INTO guru_ngaji (nama, lembaga, dkm, alamat, desa_pengelola, bobot) VALUES (?,?,?,?,?,?)", 
                              (in_ngaji_nama, in_ngaji_lembaga, in_ngaji_dkm, alamat_otomatis, desa_tugas, float(in_ngaji_bobot)))
                    conn.commit(); st.success("Data Tersimpan dan Alamat tersinkronisasi!"); st.rerun()

        st.markdown("---")
        df_ngaji = pd.read_sql_query("SELECT id as ID, nama as 'Nama Ustadz', lembaga as 'Nama Lembaga', dkm as 'Asal DKM', alamat as 'Alamat Sinkron DKM', bobot as 'Bobot' FROM guru_ngaji WHERE UPPER(desa_pengelola)=UPPER(?)", conn, params=(desa_tugas,))
        if not df_ngaji.empty:
            df_t_ngaji = df_ngaji.copy()
            df_t_ngaji.insert(0, "No.", range(1, len(df_t_ngaji) + 1))
            st.dataframe(df_t_ngaji.drop(columns=["ID"]), width="stretch", hide_index=True)
            
            with st.expander("🗑️ Hapus Data Guru Ngaji"):
                opsi_hapus_n = [f"No. {row['No.']} - {row['Nama Ustadz']} ({row['Asal DKM']})" for _, row in df_t_ngaji.iterrows()]
                pil_hapus_n = st.selectbox("Pilih Data yang Dihapus:", ["Pilih Data..."] + opsi_hapus_n)
                if st.button("Hapus Guru Ngaji", width="stretch", type="primary"):
                    if pil_hapus_n != "Pilih Data...":
                        id_target = int(df_t_ngaji[df_t_ngaji["No."] == int(pil_hapus_n.split(" - ")[0].replace("No. ", ""))]["ID"].values[0])
                        c.execute("DELETE FROM guru_ngaji WHERE id=?", (id_target,))
                        conn.commit(); st.success("Terhapus!"); st.rerun()
        else:
            st.info("Belum ada data Guru Ngaji yang terdaftar.")

    # ================= TAB 3: SABILILLAH =================
    col_tab_3, col_tab_4 = st.columns(2)
    
    with tab_sab:
        with st.form("form_kat_sab"):
            st.write("📌 **Asnaf Sabilillah (Proporsi 87.5% Hak Desa)**")
            
            kat_induk = st.selectbox("Kategori Induk (Statis):", [
                "Sarana Keagamaan", 
                "Operasional Lembaga Keagamaan", 
                "Lainnya"
            ])
            s_nama = st.text_input("Sub Kategori (Dinamis):", help="Misal: Pembangunan Masjid, Insentif Marbot, dll.")
            s_bobot = st.number_input("Bobot Pembagian (Angka Bebas):", min_value=1.0, value=1.0)
            
            if st.form_submit_button("Simpan Kategori", width="stretch"):
                if s_nama:
                    nama_final = f"{kat_induk} - {s_nama}"
                    c.execute("INSERT INTO master_kategori_sab (nama, bobot) VALUES (?,?)", (nama_final, float(s_bobot)))
                    conn.commit(); st.rerun()
                else:
                    st.error("Sub Kategori wajib diisi!")
                    
        df_sab_raw = pd.read_sql_query("SELECT id as ID, nama as 'Kategori Lengkap', bobot as 'Bobot' FROM master_kategori_sab", conn)
        if not df_sab_raw.empty:
            df_sab = df_sab_raw.copy()
            df_sab.insert(0, "No.", range(1, len(df_sab) + 1))
            st.dataframe(df_sab.drop(columns=["ID"]), width="stretch", hide_index=True)
            
            # --- FITUR HAPUS OTOMATIS (MENGGUNAKAN NAMA KATEGORI) ---
            with st.expander("🗑️ Hapus Kategori Sabilillah"):
                opsi_hapus_sab = [f"No. {row['No.']} - {row['Kategori Lengkap']}" for _, row in df_sab.iterrows()]
                pil_hapus_sab = st.selectbox("Pilih Kategori yang Dihapus:", ["Pilih Data..."] + opsi_hapus_sab, key="sel_del_sab")
                
                if st.button("Hapus Kategori", key="btn_hapus_sab", type="primary", width="stretch"): 
                    if pil_hapus_sab != "Pilih Data...":
                        no_urut = int(pil_hapus_sab.split(" - ")[0].replace("No. ", ""))
                        id_target = int(df_sab[df_sab["No."] == no_urut]["ID"].values[0])
                        c.execute("DELETE FROM master_kategori_sab WHERE id=?", (id_target,))
                        conn.commit(); st.success("Kategori terhapus!"); st.rerun()
                    else:
                        st.warning("Pilih data terlebih dahulu!")

    # ================= TAB 4: AMILIN =================
    with tab_amil:
        with st.form("form_kat_amil"):
            st.write("👔 **Asnaf Amilin (Proporsi 12.5% Hak Desa)**")
            
            # --- FORM NAMA PENGURUS DITAMBAHKAN ---
            a_pengurus = st.text_input("Nama Lengkap Pengurus (Cth: Ahmad Fulan):")
            a_nama = st.text_input("Jabatan Amilin (Cth: Ketua / Anggota):")
            a_bobot = st.number_input("Bobot Pembagian (Angka Bebas):", min_value=1.0, value=1.0)
            
            if st.form_submit_button("Simpan Amil", width="stretch"):
                if a_nama and a_pengurus:
                    c.execute("INSERT INTO master_jabatan_amil (nama, bobot, nama_pengurus) VALUES (?,?,?)", (a_nama, float(a_bobot), a_pengurus))
                    conn.commit(); st.rerun()
                else:
                    st.error("Nama Pengurus dan Jabatan wajib diisi!")
                    
        # --- TABEL DAN FITUR HAPUS OTOMATIS (MENGGUNAKAN NAMA PENGURUS) ---
        df_amil_raw = pd.read_sql_query("SELECT id as ID, nama_pengurus as 'Nama Pengurus', nama as 'Jabatan', bobot as 'Bobot' FROM master_jabatan_amil", conn)
        if not df_amil_raw.empty:
            df_amil = df_amil_raw.copy()
            df_amil.insert(0, "No.", range(1, len(df_amil) + 1))
            st.dataframe(df_amil.drop(columns=["ID"]), width="stretch", hide_index=True)
            
            with st.expander("🗑️ Hapus Data Amilin"):
                opsi_hapus_amil = [f"No. {row['No.']} - {row['Nama Pengurus']} ({row['Jabatan']})" for _, row in df_amil.iterrows()]
                pil_hapus_amil = st.selectbox("Pilih Amil yang Dihapus:", ["Pilih Data..."] + opsi_hapus_amil, key="sel_del_amil")
                
                if st.button("Hapus Jabatan", key="btn_hapus_amil", type="primary", width="stretch"): 
                    if pil_hapus_amil != "Pilih Data...":
                        no_urut = int(pil_hapus_amil.split(" - ")[0].replace("No. ", ""))
                        id_target = int(df_amil[df_amil["No."] == no_urut]["ID"].values[0])
                        c.execute("DELETE FROM master_jabatan_amil WHERE id=?", (id_target,))
                        conn.commit(); st.success("Data amil terhapus!"); st.rerun()
                    else:
                        st.warning("Pilih data terlebih dahulu!")

    conn.close()