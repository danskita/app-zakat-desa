import streamlit as st
import sqlite3
import pandas as pd
from config import DB_NAME

def render():
    st.title("📤 Distribusi Zakat Fitrah UPZ Desa")
    
    desa_tugas = st.session_state.get("desa_tugas", "")
    st.markdown(f"Sistem otomatis kalkulasi dan penyaluran proporsional Asnaf Sabilillah dan Amil untuk wilayah **{desa_tugas.upper()}**.")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # 1. AMBIL TOTAL PENERIMAAN DESA
    c.execute("SELECT SUM(total_beras), SUM(total_uang) FROM setoran_dkm WHERE UPPER(alamat_dkm)=UPPER(?)", (desa_tugas,))
    rekap = c.fetchone()
    tot_b_global = rekap[0] if rekap and rekap[0] else 0
    tot_u_global = rekap[1] if rekap and rekap[1] else 0

    # 2. KALKULASI HAK DESA (6.5% DARI GLOBAL)
    hak_desa_b = tot_b_global * 0.065
    hak_desa_u = tot_u_global * 0.065

    # 3. PEMBAGIAN KELOMPOK ASNAF (87.5% Sabilillah | 12.5% Amilin)
    jatah_sab_b = hak_desa_b * 0.875
    jatah_sab_u = hak_desa_u * 0.875

    jatah_amil_b = hak_desa_b * 0.125
    jatah_amil_u = hak_desa_u * 0.125

    # 4. AMBIL DATA BOBOT DARI MASTER
    # A. Bobot Sabilillah
    df_m_sab = pd.read_sql_query("SELECT * FROM master_kategori_sab", conn)
    total_bobot_sab = df_m_sab['bobot'].sum() if not df_m_sab.empty else 1 # Hindari div/0

    # B. Bobot Amilin
    df_m_amil = pd.read_sql_query("SELECT * FROM master_jabatan_amil", conn)
    total_bobot_amil = df_m_amil['bobot'].sum() if not df_m_amil.empty else 1

    st.markdown("---")
    
    # === TABEL 1: ALOKASI ASNAF SABILILLAH (OTOMATIS) ===
    st.subheader("📌 Alokasi Asnaf Sabilillah (Sistem Bobot Proporsional)")
    st.info(f"Total Jatah Sabilillah: Beras **{jatah_sab_b:,.2f} Kg** | Uang **Rp {int(jatah_sab_u):,}**")

    if not df_m_sab.empty:
        # Menghitung porsi masing-masing kategori Sabilillah berdasarkan bobotnya
        df_m_sab['Alokasi Beras (Kg)'] = (df_m_sab['bobot'] / total_bobot_sab) * jatah_sab_b
        df_m_sab['Alokasi Uang (Rp)'] = (df_m_sab['bobot'] / total_bobot_sab) * jatah_sab_u
        
        # Format tampilan
        df_tampil_sab = df_m_sab.copy()
        df_tampil_sab['Alokasi Beras (Kg)'] = df_tampil_sab['Alokasi Beras (Kg)'].apply(lambda x: f"{x:,.2f}")
        df_tampil_sab['Alokasi Uang (Rp)'] = df_tampil_sab['Alokasi Uang (Rp)'].apply(lambda x: f"Rp {int(x):,}")
        
        st.dataframe(df_tampil_sab.rename(columns={'nama': 'Kategori Sabilillah', 'bobot': 'Bobot'}), width="stretch", hide_index=True)
    else:
        st.warning("Data Kategori Sabilillah di Master belum diisi!")

    st.markdown("---")

    # === TABEL 2: ALOKASI ASNAF AMILIN (OTOMATIS) ===
    st.subheader("👔 Alokasi Asnaf Amilin (Sistem Bobot Proporsional)")
    st.info(f"Total Jatah Amilin: Beras **{jatah_amil_b:,.2f} Kg** | Uang **Rp {int(jatah_amil_u):,}**")

    if not df_m_amil.empty:
        # Menghitung porsi masing-masing jabatan Amilin berdasarkan bobotnya
        df_m_amil['Alokasi Beras (Kg)'] = (df_m_amil['bobot'] / total_bobot_amil) * jatah_amil_b
        df_m_amil['Alokasi Uang (Rp)'] = (df_m_amil['bobot'] / total_bobot_amil) * jatah_amil_u
        
        # Format tampilan
        df_tampil_amil = df_m_amil.copy()
        df_tampil_amil['Alokasi Beras (Kg)'] = df_tampil_amil['Alokasi Beras (Kg)'].apply(lambda x: f"{x:,.2f}")
        df_tampil_amil['Alokasi Uang (Rp)'] = df_tampil_amil['Alokasi Uang (Rp)'].apply(lambda x: f"Rp {int(x):,}")
        
        st.dataframe(df_tampil_amil.rename(columns={'nama': 'Jabatan Amilin', 'bobot': 'Bobot'}), width="stretch", hide_index=True)
    else:
        st.warning("Data Jabatan Amilin di Master belum diisi!")

    # LOGIKA SINKRONISASI OTOMATIS KE DATABASE
    # (Agar bisa langsung dibaca oleh Cetak PDF D4, D5, dan D6)
    if st.button("🔄 Sinkronkan Kalkulasi ini ke Laporan PDF", width="stretch", type="primary"):
        # 1. Bersihkan tabel lama untuk Sabilillah & Amilin
        c.execute("DELETE FROM sabilillah")
        c.execute("DELETE FROM amilin")
        
        # 2. Masukkan data hitungan baru untuk Sabilillah
        if not df_m_sab.empty:
            for _, row in df_m_sab.iterrows():
                # 'program' kita isi dengan nama kategorinya, 'penerima' juga sama atau bisa dikosongkan/disesuaikan
                c.execute("INSERT INTO sabilillah (program, penerima, beras, uang) VALUES (?,?,?,?)", 
                          (row['nama'], "Program " + row['nama'], row['Alokasi Beras (Kg)'], row['Alokasi Uang (Rp)']))
        
        # 3. Masukkan data hitungan baru untuk Amilin
        if not df_m_amil.empty:
            for _, row in df_m_amil.iterrows():
                # 'nama' bisa diisi placeholder jabatan sementara, karena detail nama orang belum ada
                c.execute("INSERT INTO amilin (nama, jabatan, beras, uang) VALUES (?,?,?,?)", 
                          ("Pengurus (" + row['nama'] + ")", row['nama'], row['Alokasi Beras (Kg)'], row['Alokasi Uang (Rp)']))
        
        conn.commit()
        st.success("Tersinkronisasi! Kalkulasi Zakat untuk Sabilillah & Amilin telah direkam dan siap dicetak ke PDF (Format D4, D5, D6).")

    conn.close()