import streamlit as st
import sqlite3
import pandas as pd
from config import DB_NAME
import time

def render():
    st.title("⚙️ Panel Kontrol Admin Kecamatan")
    st.markdown("Kelola hak akses password akun Amil Desa dan pantau kepatuhan pelaporan.")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    tab_user, tab_rekap = st.tabs(["🔐 Manajemen Akun & Password", "📊 Rekapitulasi Global Kecamatan"])

    # --- TAB 1: KELOLA AKUN ---
    with tab_user:
        st.subheader("📋 Daftar Pengguna Terdaftar")
        
        # Ambil data dari database
        df_users_raw = pd.read_sql_query("SELECT id, username, password, role, nama_desa FROM pengguna", conn)
        
        if not df_users_raw.empty:
            # MEMBUAT NOMOR URUT OTOMATIS (Sembunyikan ID Asli dari Tabel)
            df_users_tampil = df_users_raw.copy()
            df_users_tampil.insert(0, "No.", range(1, len(df_users_tampil) + 1))
            
            # Tampilkan tabel tanpa kolom ID database asli demi kerapian
            df_tabel_bersih = df_users_tampil.drop(columns=["id"])
            st.dataframe(
                df_tabel_bersih.rename(columns={
                    "username": "Username",
                    "password": "Password / Sandi",
                    "role": "Hak Akses",
                    "nama_desa": "Wilayah Tugas"
                }), 
                width="stretch", 
                hide_index=True
            )
        else:
            st.info("Belum ada pengguna yang terdaftar.")
            df_users_raw = pd.DataFrame(columns=["id", "username", "password", "role", "nama_desa"])

        st.markdown("---")
        
        # MEMBUAT AREA EDIT & TAMBAH DATA (CRUD INTEGRASI)
        col_form, col_opsi = st.columns([2, 1])
        
        with col_form:
            st.subheader("📝 Form Kelola Akun (Tambah / Edit)")
            
            # Buat dropdown pilihan untuk menentukan apakah mau tambah baru atau edit yang sudah ada
            pilihan_aksi = st.selectbox("Pilih Opsi Tindakan:", ["+ Tambah Akun Baru", "✏️ Edit Akun yang Sudah Ada"])
            
            # Variabel bawaan form (Default)
            val_username = ""
            val_password = ""
            val_role = "amil_desa"
            val_desa = ""
            id_target_update = None
            
            # Jika memilih EDIT, isi form otomatis terisi berdasarkan akun yang dipilih
            if pilihan_aksi == "✏️ Edit Akun yang Sudah Ada" and not df_users_raw.empty:
                list_pilihan_edit = [f"{row['username']} ({row['nama_desa']})" for _, row in df_users_raw.iterrows()]
                akun_terpilih = st.selectbox("Pilih Akun yang Akan Diubah:", list_pilihan_edit)
                
                # Cari data detail akun tersebut berdasarkan baris terpilih
                username_pilihan = akun_terpilih.split(" (")[0]
                row_detail = df_users_raw[df_users_raw["username"] == username_pilihan].iloc[0]
                
                val_username = row_detail["username"]
                val_password = row_detail["password"]
                val_role = row_detail["role"]
                val_desa = row_detail["nama_desa"]
                id_target_update = int(row_detail["id"])
                
            # Render Form Pengisian Akun
            with st.form("form_simpan_user"):
                c_form1, c_form2 = st.columns(2)
                with c_form1:
                    # Username dikunci (disabled) jika sedang mode edit agar tidak merusak relasi data
                    in_username = st.text_input(
                        "Username Akun:", 
                        value=val_username, 
                        disabled=(pilihan_aksi == "✏️ Edit Akun yang Sudah Ada"),
                        help="Gunakan huruf kecil tanpa spasi"
                    ).strip().lower()
                    
                    in_password = st.text_input("Kata Sandi / Password:", value=val_password)
                with c_form2:
                    list_role = ["amil_desa", "admin"]
                    idx_role = list_role.index(val_role) if val_role in list_role else 0
                    in_role = st.selectbox("Hak Akses Peran:", list_role, index=idx_role)
                    
                    in_nama_desa = st.text_input("Nama Desa Wilayah Tugas:", value=val_desa)
                
                tombol_label = "💾 SIMPAN PERUBAHAN (UPDATE)" if pilihan_aksi == "✏️ Edit Akun yang Sudah Ada" else "➕ DAFTARKAN AKUN BARU"
                
                if st.form_submit_button(tombol_label, width="stretch"):
                    if pilihan_aksi == "✏️ Edit Akun yang Sudah Ada" and id_target_update:
                        # EKSEKUSI PROSES EDIT & SIMPAN
                        c.execute(
                            "UPDATE pengguna SET password=?, role=?, nama_desa=? WHERE id=?",
                            (in_password, in_role, in_nama_desa, id_target_update)
                        )
                        st.success(f"Berhasil memperbarui data kata sandi untuk akun '{val_username}'!")
                    else:
                        # EKSEKUSI PROSES TAMBAH BARU
                        if in_username and in_password:
                            try:
                                c.execute(
                                    "INSERT INTO pengguna (username, password, role, nama_desa) VALUES (?,?,?,?)",
                                    (in_username, in_password, in_role, in_nama_desa)
                                )
                                st.success(f"Akun baru '{in_username}' berhasil ditambahkan ke sistem!")
                            except sqlite3.IntegrityError:
                                st.error("Gagal! Username tersebut sudah terdaftar di database.")
                        else:
                            st.error("Username dan Password tidak boleh dikosongkan!")
                    
                    conn.commit()
                    time.sleep(1.5)
                    st.rerun()

        with col_opsi:
            st.subheader("🗑️ Zona Hapus Akun")
            if not df_users_raw.empty:
                list_hapus = [f"{row['username']}" for _, row in df_users_raw.iterrows() if row['role'] != 'admin']
                if list_hapus:
                    user_hapus = st.selectbox("Pilih Akun yang Akan Dihapus:", list_hapus)
                    if st.button("❌ Hapus Akun Permanen", type="primary", width="stretch"):
                        c.execute("DELETE FROM pengguna WHERE username=?", (user_hapus,))
                        conn.commit()
                        st.success(f"Akun '{user_hapus}' berhasil dihapus!")
                        st.rerun()
                else:
                    st.caption("Tidak ada akun amil desa sekunder yang bisa dihapus.")
            else:
                st.caption("Daftar pengguna kosong.")

    # --- TAB 2: REKAP GLOBAL KECAMATAN ---
    with tab_rekap:
        st.subheader("Total Rekapitulasi Setoran Zakat Antar Desa")
        st.write("Data di bawah ini merangkum seluruh setoran yang diinput oleh masing-masing Amil Desa.")
        
        query_global = """
        SELECT 
            nama_dkm AS 'Nama UPZ DKM',
            alamat_dkm AS 'Desa Induk',
            (jiwa_beras + jiwa_uang) AS 'Muzakki (Jiwa)',
            total_beras AS 'Total Beras (Kg)',
            total_uang AS 'Total Uang Zakat (Rp)',
            infaq AS 'Total Infaq (Rp)'
        FROM setoran_dkm
        ORDER BY alamat_dkm ASC, nama_dkm ASC
        """
        df_global = pd.read_sql_query(query_global, conn)
        
        if not df_global.empty:
            # Tambahkan nomor urut otomatis pada tabel rekap global kecamatan
            df_global.insert(0, "No.", range(1, len(df_global) + 1))
            st.dataframe(df_global, width="stretch", hide_index=True)
            
            c.execute("SELECT SUM(total_beras), SUM(total_uang), SUM(infaq) FROM setoran_dkm")
            total_all = c.fetchone()
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Grand Total Beras Kecamatan", f"{total_all[0] or 0:,.2f} Kg")
            col2.metric("Grand Total Uang Zakat", f"Rp {int(total_all[1] or 0):,}")
            col3.metric("Grand Total Infaq", f"Rp {int(total_all[2] or 0):,}")
        else:
            st.info("Belum ada desa yang melakukan input setoran zakat.")

    conn.close()