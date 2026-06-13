import streamlit as st
import sqlite3
import pandas as pd
import datetime
import os
from config import DB_NAME

def render():
    st.title("🖨️ Cetak Laporan Kecamatan (PDF)")
    
    st.markdown("Cetak rekapitulasi data tingkat kecamatan, meliputi Zakat, Hewan Qurban, Majlis Ta'lim, dan Kupon Infaq.")

    # PENTING: Cek apakah library FPDF sudah terinstall
    try:
        from fpdf import FPDF
    except ImportError:
        st.error("Library FPDF belum terinstall. Buka terminal dan ketik: pip install fpdf")
        st.stop()

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT nama_kecamatan, kabupaten, logo_path FROM pengaturan WHERE id=1")
    p_data = c.fetchone()
    if p_data:
        kec, kab, logo_path = p_data[0], p_data[1], p_data[2]
    else:
        kec, kab, logo_path = "KECAMATAN", "KABUPATEN", ""

    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.subheader("Atur Titimangsa Surat")
        with st.container(border=True):
            tgl_ba = st.text_input("Tanggal Laporan:", value=datetime.datetime.now().strftime("%d %B %Y"))
            tempat_ba = st.text_input("Tempat TTD:", value=kec.capitalize())
            ketua_kec = st.text_input("Nama Ketua UPZ Kecamatan:", value="Ketua UPZ Kecamatan")
            st.info("💡 Data di atas akan tercetak otomatis di bagian tanda tangan bawah laporan.")

    # ==========================================
    # FUNGSI HELPER KOP SURAT UNTUK KECAMATAN
    # ==========================================
    def cetak_kop_surat_kecamatan(pdf, kec, kab, logo_path="", is_landscape=False):
        page_width = 297 if is_landscape else 210
        margin_side = 10 
        pdf.set_y(10)
        if logo_path and os.path.exists(logo_path):
            try: pdf.image(logo_path, x=margin_side, y=10, w=22)
            except: pass
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 6, "BADAN AMIL ZAKAT NASIONAL (BAZNAS)", ln=True, align="C")
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 7, f"UNIT PENGUMPUL ZAKAT (UPZ) KECAMATAN {kec.upper()}", ln=True, align="C")
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 6, f"KABUPATEN {kab.upper()}", ln=True, align="C")
        pdf.ln(5)
        y_garis = max(pdf.get_y(), 34)
        line_width = page_width - (margin_side * 2)
        pdf.set_line_width(0.8)
        pdf.line(margin_side, y_garis, margin_side + line_width, y_garis)
        pdf.set_line_width(0.2)
        pdf.line(margin_side, y_garis + 1, margin_side + line_width, y_garis + 1)
        pdf.set_y(y_garis + 5)

    with col2:
        st.subheader("Daftar Laporan Tingkat Kecamatan")
        
        # ==================================================
        # 1. LAPORAN REKAPITULASI ZAKAT FITRAH (KECAMATAN)
        # ==================================================
        with st.expander("📊 Laporan Rekapitulasi Zakat Fitrah", expanded=True):
            st.write("Laporan rekapitulasi penghimpunan dan setoran zakat fitrah dari seluruh desa.")
            if st.button("🖨️ Siapkan Laporan Zakat (PDF)", width="stretch"):
                # Menarik data zakat dari semua desa dan menjumlahkannya berdasarkan desa
                c.execute("""SELECT UPPER(alamat_dkm), SUM(jiwa_beras+jiwa_uang), SUM(total_beras), SUM(total_uang) 
                             FROM setoran_dkm GROUP BY UPPER(alamat_dkm) ORDER BY UPPER(alamat_dkm) ASC""")
                z_rows = c.fetchall()
                
                if not z_rows:
                    st.error("Data Zakat masih kosong!")
                else:
                    pdf = FPDF(orientation="L", unit="mm", format="A4")
                    pdf.set_margins(10, 10, 10); pdf.set_auto_page_break(auto=True, margin=15); pdf.add_page()
                    cetak_kop_surat_kecamatan(pdf, kec, kab, logo_path, is_landscape=True)
                    
                    pdf.set_font("Arial", "B", 12); pdf.cell(0, 8, "REKAPITULASI PENERIMAAN ZAKAT FITRAH TINGKAT KECAMATAN", ln=True, align="C")
                    pdf.cell(0, 6, f"TAHUN {datetime.datetime.now().year} M", ln=True, align="C"); pdf.ln(8)
                    
                    pdf.set_font("Arial", "B", 9)
                    pdf.cell(10, 10, "No", 1, 0, "C"); pdf.cell(50, 10, "Desa / Kelurahan", 1, 0, "C")
                    pdf.cell(30, 10, "Muzakki (Jiwa)", 1, 0, "C")
                    
                    x_start = pdf.get_x()
                    pdf.cell(90, 5, "Total Pengumpulan (100%)", 1, 0, "C")
                    pdf.cell(90, 5, "Hak Kecamatan & Kabupaten (11%)", 1, 1, "C")
                    
                    pdf.set_xy(x_start, pdf.get_y())
                    pdf.cell(45, 5, "Beras (Kg)", 1, 0, "C"); pdf.cell(45, 5, "Uang (Rp)", 1, 0, "C")
                    pdf.cell(45, 5, "Beras (Kg)", 1, 0, "C"); pdf.cell(45, 5, "Uang (Rp)", 1, 1, "C")
                    
                    pdf.set_font("Arial", "", 9)
                    t_jiwa = 0; t_tb = 0; t_tu = 0; t_fb = 0; t_fu = 0
                    for i, r in enumerate(z_rows):
                        pdf.cell(10, 8, str(i+1), 1, 0, "C")
                        pdf.cell(50, 8, str(r[0]), 1, 0, "L")
                        pdf.cell(30, 8, f"{int(r[1] or 0)}", 1, 0, "C")
                        
                        tb = r[2] or 0; tu = r[3] or 0
                        # Sistem otomatis memotong 11% (Gabungan Hak Kecamatan 5% + Kabupaten 6%)
                        fb = tb * 0.11; fu = tu * 0.11 
                        
                        pdf.cell(45, 8, f"{tb:,.2f}", 1, 0, "C")
                        pdf.cell(45, 8, f"Rp {int(tu):,}", 1, 0, "R")
                        pdf.cell(45, 8, f"{fb:,.2f}", 1, 0, "C")
                        pdf.cell(45, 8, f"Rp {int(fu):,}", 1, 1, "R")
                        
                        t_jiwa += (r[1] or 0); t_tb += tb; t_tu += tu; t_fb += fb; t_fu += fu
                        
                    pdf.set_font("Arial", "B", 9)
                    pdf.cell(60, 8, "TOTAL KESELURUHAN", 1, 0, "C")
                    pdf.cell(30, 8, f"{int(t_jiwa)}", 1, 0, "C")
                    pdf.cell(45, 8, f"{t_tb:,.2f}", 1, 0, "C"); pdf.cell(45, 8, f"Rp {int(t_tu):,}", 1, 0, "R")
                    pdf.cell(45, 8, f"{t_fb:,.2f}", 1, 0, "C"); pdf.cell(45, 8, f"Rp {int(t_fu):,}", 1, 1, "R")
                    
                    pdf.ln(15); pdf.set_font("Arial", "", 11)
                    pdf.cell(180, 6, "", 0, 0, "C"); pdf.cell(90, 6, f"{tempat_ba}, {tgl_ba}", 0, 1, "C")
                    pdf.cell(180, 6, "", 0, 0, "C"); pdf.cell(90, 6, "Ketua UPZ Kecamatan,", 0, 1, "C")
                    pdf.ln(20); pdf.set_font("Arial", "B", 11)
                    pdf.cell(180, 6, "", 0, 0, "C"); pdf.cell(90, 6, f"( {ketua_kec} )", 0, 1, "C")
                    
                    pdf_bytes = pdf.output(dest='S').encode('latin-1')
                    st.download_button(label="📥 UNDUH LAPORAN ZAKAT", data=pdf_bytes, file_name="Laporan_Zakat_Kecamatan.pdf", mime="application/pdf", use_container_width=True)

        # ==================================================
        # 2. LAPORAN DATA HEWAN QURBAN
        # ==================================================
        with st.expander("🐄 Laporan Rekapitulasi Hewan Qurban"):
            st.write("Laporan total hewan qurban seluruh desa di lingkup kecamatan.")
            if st.button("🖨️ Siapkan Laporan Qurban (PDF)", width="stretch"):
                c.execute("SELECT tahun, nama_dkm, jenis_hewan, jumlah_hewan, jumlah_mudhohi FROM qurban ORDER BY tahun DESC, nama_dkm ASC")
                q_rows = c.fetchall()
                
                if not q_rows:
                    st.error("Data Qurban masih kosong!")
                else:
                    pdf = FPDF(orientation="P", unit="mm", format="A4")
                    pdf.set_margins(10, 10, 10); pdf.set_auto_page_break(auto=True, margin=15); pdf.add_page()
                    cetak_kop_surat_kecamatan(pdf, kec, kab, logo_path)
                    
                    pdf.set_font("Arial", "B", 12); pdf.cell(0, 8, "REKAPITULASI DATA HEWAN QURBAN TINGKAT KECAMATAN", ln=True, align="C")
                    pdf.cell(0, 6, f"TAHUN {datetime.datetime.now().year} M", ln=True, align="C"); pdf.ln(8)
                    
                    pdf.set_font("Arial", "B", 10)
                    pdf.cell(10, 8, "No", 1, 0, "C"); pdf.cell(20, 8, "Tahun", 1, 0, "C")
                    pdf.cell(80, 8, "Asal Desa / Wilayah", 1, 0, "C"); pdf.cell(30, 8, "Jenis Hewan", 1, 0, "C")
                    pdf.cell(25, 8, "Jml (Ekor)", 1, 0, "C"); pdf.cell(25, 8, "Mudhohi", 1, 1, "C")
                    
                    pdf.set_font("Arial", "", 10)
                    tot_hewan = 0; tot_mudhohi = 0
                    for i, r in enumerate(q_rows):
                        pdf.cell(10, 8, str(i+1), 1, 0, "C")
                        pdf.cell(20, 8, str(r[0]), 1, 0, "C")
                        pdf.cell(80, 8, str(r[1])[:40], 1, 0, "L")
                        pdf.cell(30, 8, str(r[2]), 1, 0, "C")
                        pdf.cell(25, 8, str(r[3]), 1, 0, "C")
                        pdf.cell(25, 8, str(r[4]), 1, 1, "C")
                        tot_hewan += r[3]; tot_mudhohi += r[4]
                    
                    pdf.set_font("Arial", "B", 10)
                    pdf.cell(140, 8, "TOTAL KESELURUHAN SE-KECAMATAN", 1, 0, "C")
                    pdf.cell(25, 8, f"{tot_hewan} Ekor", 1, 0, "C")
                    pdf.cell(25, 8, f"{tot_mudhohi} Org", 1, 1, "C")
                    
                    pdf.ln(15); pdf.set_font("Arial", "", 11)
                    pdf.cell(100, 6, "", 0, 0, "C"); pdf.cell(90, 6, f"{tempat_ba}, {tgl_ba}", 0, 1, "C")
                    pdf.cell(100, 6, "", 0, 0, "C"); pdf.cell(90, 6, "Ketua UPZ Kecamatan,", 0, 1, "C")
                    pdf.ln(20); pdf.set_font("Arial", "B", 11)
                    pdf.cell(100, 6, "", 0, 0, "C"); pdf.cell(90, 6, f"( {ketua_kec} )", 0, 1, "C")
                    
                    pdf_bytes = pdf.output(dest='S').encode('latin-1')
                    st.download_button(label="📥 UNDUH LAPORAN QURBAN", data=pdf_bytes, file_name="Laporan_Qurban_Kecamatan.pdf", mime="application/pdf", use_container_width=True)

        # ==================================================
        # 3. LAPORAN DATA MAJLIS TA'LIM
        # ==================================================
        with st.expander("🕌 Laporan Data Majlis Ta'lim"):
            st.write("Rekapitulasi seluruh Majlis Ta'lim dan jadwal pengajian tingkat kecamatan.")
            if st.button("🖨️ Siapkan Laporan Majlis Ta'lim (PDF)", width="stretch"):
                c.execute("SELECT nama_majlis, pimpinan, alamat, rt, rw, hari, jam FROM majlis_talim ORDER BY alamat ASC, nama_majlis ASC")
                m_rows = c.fetchall()
                
                if not m_rows:
                    st.error("Data Majlis Ta'lim masih kosong!")
                else:
                    pdf = FPDF(orientation="L", unit="mm", format="A4")
                    pdf.set_margins(10, 10, 10); pdf.set_auto_page_break(auto=True, margin=15); pdf.add_page()
                    cetak_kop_surat_kecamatan(pdf, kec, kab, logo_path, is_landscape=True)
                    
                    pdf.set_font("Arial", "B", 12); pdf.cell(0, 8, "DAFTAR INVENTARIS MAJLIS TA'LIM TINGKAT KECAMATAN", ln=True, align="C"); pdf.ln(8)
                    
                    pdf.set_font("Arial", "B", 10)
                    pdf.cell(10, 8, "No", 1, 0, "C"); pdf.cell(60, 8, "Nama Majlis Ta'lim", 1, 0, "C")
                    pdf.cell(60, 8, "Pimpinan / Ustadz", 1, 0, "C"); pdf.cell(80, 8, "Alamat Lengkap", 1, 0, "C")
                    pdf.cell(30, 8, "Hari / Waktu", 1, 0, "C"); pdf.cell(30, 8, "Jam", 1, 1, "C")
                    
                    pdf.set_font("Arial", "", 10)
                    for i, r in enumerate(m_rows):
                        pdf.cell(10, 8, str(i+1), 1, 0, "C")
                        pdf.cell(60, 8, str(r[0])[:30], 1, 0, "L")
                        pdf.cell(60, 8, str(r[1])[:30], 1, 0, "L")
                        alamat_full = f"{r[2]} RT {r[3]} RW {r[4]}"
                        pdf.cell(80, 8, alamat_full[:45], 1, 0, "L")
                        pdf.cell(30, 8, str(r[5])[:15], 1, 0, "C")
                        pdf.cell(30, 8, str(r[6])[:15], 1, 1, "C")
                    
                    pdf.ln(15); pdf.set_font("Arial", "", 11)
                    pdf.cell(180, 6, "", 0, 0, "C"); pdf.cell(90, 6, f"{tempat_ba}, {tgl_ba}", 0, 1, "C")
                    pdf.cell(180, 6, "", 0, 0, "C"); pdf.cell(90, 6, "Ketua UPZ Kecamatan,", 0, 1, "C")
                    pdf.ln(20); pdf.set_font("Arial", "B", 11)
                    pdf.cell(180, 6, "", 0, 0, "C"); pdf.cell(90, 6, f"( {ketua_kec} )", 0, 1, "C")
                    
                    pdf_bytes = pdf.output(dest='S').encode('latin-1')
                    st.download_button(label="📥 UNDUH LAPORAN MAJLIS TA'LIM", data=pdf_bytes, file_name="Laporan_Majlis_Talim.pdf", mime="application/pdf", use_container_width=True)

        # ==================================================
        # 4. LAPORAN KUPON INFAQ (SIRKULASI & SELISIH)
        # ==================================================
        with st.expander("🎟️ Laporan Rekap Kupon Infaq (Sirkulasi)"):
            st.write("Rekapitulasi sirkulasi dan pendapatan uang kupon infaq seluruh desa di kecamatan.")
            if st.button("🖨️ Siapkan Laporan Kupon (PDF)", width="stretch"):
                try:
                    c.execute("""SELECT desa_pengelola, nama_dkm, jumlah_awal, kupon_laku, kupon_kembali, kupon_hilang, nominal_disetor 
                                 FROM kupon_infaq ORDER BY desa_pengelola ASC, nama_dkm ASC""")
                    k_rows = c.fetchall()
                except:
                    k_rows = []

                if not k_rows:
                    st.error("Data sirkulasi kupon infaq masih kosong!")
                else:
                    pdf = FPDF(orientation="L", unit="mm", format="A4")
                    pdf.set_margins(10, 10, 10); pdf.set_auto_page_break(auto=True, margin=15); pdf.add_page()
                    cetak_kop_surat_kecamatan(pdf, kec, kab, logo_path, is_landscape=True)
                    
                    pdf.set_font("Arial", "B", 12); pdf.cell(0, 8, "REKAPITULASI SIRKULASI KUPON INFAQ RAMADHAN", ln=True, align="C")
                    pdf.cell(0, 6, f"TINGKAT KECAMATAN TAHUN {datetime.datetime.now().year} M", ln=True, align="C"); pdf.ln(8)
                    
                    pdf.set_font("Arial", "B", 9)
                    pdf.cell(10, 8, "No", 1, 0, "C"); pdf.cell(40, 8, "Desa Pengelola", 1, 0, "C")
                    pdf.cell(60, 8, "Nama UPZ DKM (Sumber)", 1, 0, "C"); pdf.cell(22, 8, "Awal (Lbr)", 1, 0, "C")
                    pdf.cell(22, 8, "Laku (Lbr)", 1, 0, "C"); pdf.cell(22, 8, "Kembali", 1, 0, "C")
                    pdf.cell(22, 8, "Selisih/Hilang", 1, 0, "C"); pdf.cell(50, 8, "Total Uang Disetor (Rp)", 1, 1, "C")
                    
                    pdf.set_font("Arial", "", 9)
                    t_awal=0; t_laku=0; t_kembali=0; t_hilang=0; t_uang=0
                    for i, r in enumerate(k_rows):
                        k_awal = int(r[2] or 0); k_laku = int(r[3] or 0); k_kem = int(r[4] or 0)
                        k_hil = int(r[5] or 0); uang = float(r[6] or 0)
                        
                        pdf.cell(10, 8, str(i+1), 1, 0, "C")
                        pdf.cell(40, 8, str(r[0])[:20].upper(), 1, 0, "L")
                        pdf.cell(60, 8, str(r[1])[:30], 1, 0, "L")
                        pdf.cell(22, 8, f"{k_awal}", 1, 0, "C")
                        pdf.cell(22, 8, f"{k_laku}", 1, 0, "C")
                        pdf.cell(22, 8, f"{k_kem}", 1, 0, "C")
                        
                        if k_hil > 0:
                            pdf.set_text_color(220, 20, 60)
                            pdf.cell(22, 8, f"{k_hil}", 1, 0, "C")
                            pdf.set_text_color(0, 0, 0)
                        else:
                            pdf.cell(22, 8, f"{k_hil}", 1, 0, "C")
                            
                        pdf.cell(50, 8, f"Rp {int(uang):,}", 1, 1, "R")
                        
                        t_awal+=k_awal; t_laku+=k_laku; t_kembali+=k_kem; t_hilang+=k_hil; t_uang+=uang
                        
                    pdf.set_font("Arial", "B", 9)
                    pdf.cell(110, 8, "TOTAL KESELURUHAN", 1, 0, "C")
                    pdf.cell(22, 8, f"{t_awal} Lbr", 1, 0, "C"); pdf.cell(22, 8, f"{t_laku} Lbr", 1, 0, "C")
                    pdf.cell(22, 8, f"{t_kembali} Lbr", 1, 0, "C"); pdf.cell(22, 8, f"{t_hilang} Lbr", 1, 0, "C")
                    pdf.cell(50, 8, f"Rp {int(t_uang):,}", 1, 1, "R")
                    
                    pdf.ln(15); pdf.set_font("Arial", "", 11)
                    pdf.cell(180, 6, "", 0, 0, "C"); pdf.cell(90, 6, f"{tempat_ba}, {tgl_ba}", 0, 1, "C")
                    pdf.cell(180, 6, "", 0, 0, "C"); pdf.cell(90, 6, "Ketua UPZ Kecamatan,", 0, 1, "C")
                    pdf.ln(20); pdf.set_font("Arial", "B", 11)
                    pdf.cell(180, 6, "", 0, 0, "C"); pdf.cell(90, 6, f"( {ketua_kec} )", 0, 1, "C")
                    
                    pdf_bytes = pdf.output(dest='S').encode('latin-1')
                    st.download_button(label="📥 UNDUH LAPORAN KUPON INFAQ", data=pdf_bytes, file_name="Laporan_Kupon_Infaq_Kecamatan.pdf", mime="application/pdf", use_container_width=True)

    conn.close()