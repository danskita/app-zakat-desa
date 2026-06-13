import streamlit as st
import sqlite3
import pandas as pd
from config import DB_NAME

def render():
    st.title("⚙️ Pengaturan Profil Desa")
    st.write("Silakan perbarui profil dan konfigurasi UPZ Desa di sini.")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    try:
        c.execute("ALTER TABLE pengaturan ADD COLUMN no_hp TEXT")
        c.execute("ALTER TABLE pengaturan ADD COLUMN total_jiwa INTEGER")
        c.execute("ALTER TABLE pengaturan ADD COLUMN total_kk INTEGER")
    except:
        pass

    c.execute("SELECT * FROM pengaturan WHERE id=1")
    data = c.fetchone()
    
    if data:
        desa = data[1] if data[1] else ""
        kades = data[2] if data[2] else ""
        kec = data[3] if data[3] else ""
        kab = data[4] if data[4] else ""
        ketua = data[5] if data[5] else ""
        sek = data[6] if data[6] else ""
        ben = data[7] if data[7] else ""
        tarif = int(data[9]) if data[9] else 0
        h_beras = int(data[10]) if data[10] else 0
        j_beras = data[11] if data[11] else 0.0
        
        try:
            c.execute("SELECT nominal_kupon, logo_path, no_hp, total_jiwa, total_kk FROM pengaturan WHERE id=1")
            res_tambahan = c.fetchone()
            nom_kupon = int(res_tambahan[0]) if res_tambahan and res_tambahan[0] else 0
            logo_path = res_tambahan[1] if res_tambahan and res_tambahan[1] else ""
            no_hp = res_tambahan[2] if res_tambahan and res_tambahan[2] else ""
            total_jiwa = int(res_tambahan[3]) if res_tambahan and res_tambahan[3] else 0
            total_kk = int(res_tambahan[4]) if res_tambahan and res_tambahan[4] else 0
        except:
            nom_kupon = 0; logo_path = ""; no_hp = ""; total_jiwa = 0; total_kk = 0

        with st.form("form_pengaturan"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Data Desa")
                in_desa = st.text_input("Nama Desa:", value=desa)
                in_kades = st.text_input("Kepala Desa:", value=kades)
                in_kec = st.text_input("Kecamatan:", value=kec)
                in_kab = st.text_input("Kabupaten:", value=kab)
                in_jiwa = st.number_input("Total Penduduk (Jiwa):", value=total_jiwa, min_value=0)
                in_kk = st.number_input("Total Kepala Keluarga (KK):", value=total_kk, min_value=0)
                
            with col2:
                st.subheader("Data Pengurus UPZ")
                in_ketua = st.text_input("Ketua UPZ:", value=ketua)
                in_hp = st.text_input("No. HP / WhatsApp:", value=no_hp)
                in_sek = st.text_input("Sekretaris:", value=sek)
                in_ben = st.text_input("Bendahara:", value=ben)
            
            st.markdown("---")
            st.subheader("Konfigurasi Tarif & Lainnya")
            col3, col4 = st.columns(2)
            with col3:
                in_tarif = st.number_input("Tarif Zakat Uang (Rp):", value=tarif, min_value=0)
                in_h_beras = st.number_input("Harga Jual Beras (Rp):", value=h_beras, min_value=0)
            with col4:
                in_j_beras = st.number_input("Beras Dijual (Kg):", value=float(j_beras), min_value=0.0)
                in_nom_kupon = st.number_input("Nominal Kupon Infaq (Rp):", value=nom_kupon, min_value=0)
                in_logo = st.text_input("Nama File Logo (Kop Surat):", value=logo_path)

            if st.form_submit_button("💾 Simpan Pengaturan", width="stretch"):
                c.execute('''UPDATE pengaturan SET 
                             nama_desa=?, kepala_desa=?, nama_kecamatan=?, kabupaten=?, 
                             ketua_upz=?, sekretaris=?, bendahara=?, tarif_uang=?, 
                             harga_jual_beras=?, beras_dijual=?, nominal_kupon=?, 
                             logo_path=?, no_hp=?, total_jiwa=?, total_kk=? 
                             WHERE id=1''',
                          (in_desa, in_kades, in_kec, in_kab, 
                           in_ketua, in_sek, in_ben, float(in_tarif), 
                           float(in_h_beras), in_j_beras, float(in_nom_kupon), 
                           in_logo, in_hp, in_jiwa, in_kk))
                conn.commit()
                st.success("Data pengaturan berhasil diperbarui!")
                st.rerun()

        st.markdown("---")
        with st.expander("📦 Arsipkan & Bersihkan Tahun Ini (Zona Berbahaya)"):
            st.warning("PENTING: Seluruh Data Zakat & Penyaluran tahun ini akan dipindahkan ke ARSIP dan tabel aktif akan dikosongkan.")
            with st.form("form_arsip"):
                tahun_arsip = st.text_input("Ketik Tahun untuk diarsipkan (Contoh: 2026):")
                if st.form_submit_button("Arsipkan Sekarang"):
                    if tahun_arsip:
                        try:
                            c.execute("INSERT INTO arsip_setoran_dkm (tahun_arsip, nama_dkm, alamat_dkm, perwakilan, alamat_perwakilan, tipe_input, jiwa_beras, jiwa_uang, fisik_beras, fisik_uang, total_beras, total_uang, infaq, kupon_diterima, kupon_terjual, kupon_kembali) SELECT ?, nama_dkm, alamat_dkm, perwakilan, alamat_perwakilan, tipe_input, jiwa_beras, jiwa_uang, fisik_beras, fisik_uang, total_beras, total_uang, infaq, kupon_diterima, kupon_terjual, kupon_kembali FROM setoran_dkm", (tahun_arsip,))
                            c.execute("INSERT INTO arsip_sabilillah (tahun_arsip, program, penerima, beras, uang) SELECT ?, program, penerima, beras, uang FROM sabilillah", (tahun_arsip,))
                            c.execute("INSERT INTO arsip_amilin (tahun_arsip, nama, jabatan, beras, uang) SELECT ?, nama, jabatan, beras, uang FROM amilin", (tahun_arsip,))
                            c.execute("INSERT INTO arsip_distribusi_ngaji (tahun_arsip, nama, lembaga, dkm, alamat, bobot, uang) SELECT ?, nama, lembaga, dkm, alamat, bobot, uang FROM distribusi_ngaji", (tahun_arsip,))

                            c.execute("DELETE FROM setoran_dkm")
                            c.execute("DELETE FROM sabilillah")
                            c.execute("DELETE FROM amilin")
                            c.execute("DELETE FROM distribusi_ngaji")
                            
                            conn.commit()
                            st.success(f"Berhasil! Semua data telah diarsipkan pada tahun {tahun_arsip}. Tabel input sekarang kosong.")
                        except Exception as e:
                            st.error(f"Gagal mengarsipkan: {e}")
                    else:
                        st.error("Tahun wajib diisi!")
    else:
        st.error("Data pengaturan tidak ditemukan di database! Pastikan database tidak kosong.")

    conn.close()