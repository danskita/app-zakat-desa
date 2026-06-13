import sqlite3
import streamlit as st

DB_NAME = "database_upz_desa.db"

@st.cache_resource
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Tabel Pengaturan
    cursor.execute('''CREATE TABLE IF NOT EXISTS pengaturan (
            id INTEGER PRIMARY KEY, nama_desa TEXT, kepala_desa TEXT, nama_kecamatan TEXT, kabupaten TEXT,
            ketua_upz TEXT, sekretaris TEXT, bendahara TEXT, tarif_beras REAL, tarif_uang REAL, harga_jual_beras REAL, beras_dijual REAL,
            logo_path TEXT, nominal_kupon REAL, no_hp TEXT, total_jiwa INTEGER, total_kk INTEGER)''')

    # 2. Tabel Aktif
    cursor.execute('''CREATE TABLE IF NOT EXISTS setoran_dkm (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nama_dkm TEXT, alamat_dkm TEXT, perwakilan TEXT, alamat_perwakilan TEXT,
            tipe_input TEXT, jiwa_beras INTEGER, jiwa_uang INTEGER, fisik_beras REAL, fisik_uang REAL, 
            total_beras REAL, total_uang REAL, infaq REAL, kupon_diterima INTEGER DEFAULT 0, kupon_terjual INTEGER DEFAULT 0, kupon_kembali INTEGER DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS sabilillah (id INTEGER PRIMARY KEY AUTOINCREMENT, program TEXT, penerima TEXT, beras REAL, uang REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS amilin (id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, jabatan TEXT, beras REAL, uang REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS distribusi_ngaji (id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, lembaga TEXT, dkm TEXT, alamat TEXT, bobot REAL, uang REAL)''')

    # 3. Tabel Arsip
    cursor.execute('''CREATE TABLE IF NOT EXISTS arsip_setoran_dkm (id INTEGER PRIMARY KEY AUTOINCREMENT, tahun_arsip TEXT, nama_dkm TEXT, alamat_dkm TEXT, perwakilan TEXT, alamat_perwakilan TEXT, tipe_input TEXT, jiwa_beras INTEGER, jiwa_uang INTEGER, fisik_beras REAL, fisik_uang REAL, total_beras REAL, total_uang REAL, infaq REAL, kupon_diterima INTEGER, kupon_terjual INTEGER, kupon_kembali INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS arsip_sabilillah (id INTEGER PRIMARY KEY AUTOINCREMENT, tahun_arsip TEXT, program TEXT, penerima TEXT, beras REAL, uang REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS arsip_amilin (id INTEGER PRIMARY KEY AUTOINCREMENT, tahun_arsip TEXT, nama TEXT, jabatan TEXT, beras REAL, uang REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS arsip_distribusi_ngaji (id INTEGER PRIMARY KEY AUTOINCREMENT, tahun_arsip TEXT, nama TEXT, lembaga TEXT, dkm TEXT, alamat TEXT, bobot REAL, uang REAL)''')

    # 4. Tabel Master Data
    cursor.execute('''CREATE TABLE IF NOT EXISTS master_dkm (id INTEGER PRIMARY KEY AUTOINCREMENT, nama_dkm TEXT, ketua_dkm TEXT, alamat_dkm TEXT, perwakilan TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS master_kategori_sab (id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, bobot REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS master_jabatan_amil (id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, bobot REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS guru_ngaji (id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, lembaga TEXT, dkm TEXT, alamat TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS qurban (id INTEGER PRIMARY KEY AUTOINCREMENT, tahun TEXT, nama_dkm TEXT, jenis_hewan TEXT, jumlah_hewan INTEGER, jumlah_mudhohi INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS majlis_talim (id INTEGER PRIMARY KEY AUTOINCREMENT, nama_majlis TEXT, alamat TEXT, rt TEXT, rw TEXT, hari TEXT, jam TEXT, pimpinan TEXT)''')

    # 5. TABEL BARU: MULTI-USER AUTHENTICATION
    cursor.execute('''CREATE TABLE IF NOT EXISTS pengguna (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT,          -- 'admin' (Kecamatan) atau 'amil_desa' (Amil Desa harian)
            nama_desa TEXT      -- Menandakan wilayah tugas spesifik desa terkait
    )''')

    # ==========================================
    # DATA AWAL (SEEDING DATA)
    # ==========================================
    
    # Seeding Tabel Pengaturan
    cursor.execute('SELECT COUNT(*) FROM pengaturan')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''INSERT INTO pengaturan (nama_desa, kepala_desa, nama_kecamatan, kabupaten, ketua_upz, sekretaris, bendahara, tarif_beras, tarif_uang, harga_jual_beras, beras_dijual, nominal_kupon, logo_path, no_hp, total_jiwa, total_kk)
            VALUES ('Rancapaku', 'Jajang Basar', 'Padakembang', 'Tasikmalaya', 'Dadan Abdurrahman', '', '', 2.5, 37000, 15000, 0, 0, '', '', 0, 0)''')
    
    # Seeding Kategori Sabilillah
    cursor.execute('SELECT COUNT(*) FROM master_kategori_sab')
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO master_kategori_sab (nama, bobot) VALUES (?,?)", [("Operasional Lembaga Keagamaan", 3), ("Sarana Keagamaan", 3), ("Lainnya", 1)])
    
    # Seeding Jabatan Amil
    cursor.execute('SELECT COUNT(*) FROM master_jabatan_amil')
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO master_jabatan_amil (nama, bobot) VALUES (?,?)", [("Ketua", 4), ("Sekretaris", 3), ("Bendahara", 3), ("Anggota", 2), ("Amil Pembantu", 1)])
        
    # Seeding Akun Pengguna Default (Jika masih kosong)
    cursor.execute("SELECT COUNT(*) FROM pengguna WHERE role='admin'")
    if cursor.fetchone()[0] == 0:
        # Akun Utama Admin Kecamatan
        cursor.execute("INSERT INTO pengguna (username, password, role, nama_desa) VALUES (?,?,?,?)",
                       ('admin', 'admin123', 'admin', 'Kecamatan'))
        
        # Akun Sampel Pertama untuk Amil Desa Rancapaku
        cursor.execute("INSERT INTO pengguna (username, password, role, nama_desa) VALUES (?,?,?,?)",
                       ('amil_rancapaku', 'rancapaku123', 'amil_desa', 'Rancapaku'))
        
    conn.commit()
    conn.close()