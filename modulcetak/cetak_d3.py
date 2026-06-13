import streamlit as st
import sqlite3
import datetime
import os
import time
from fpdf import FPDF
from config import DB_NAME

def render_ui(desa_default, no_ba, hari_ba, tgl_ba, tempat_ba):
    st.subheader("📄 Format D3 (Rekapitulasi 100%)")
    st.write("Cetak rekapitulasi penerimaan dan penyaluran zakat keseluruhan (A4 Portrait sesuai draft asli).")
    
    if st.button("Siapkan Dokumen D3", width="stretch"):
        # 1. Ambil Data dari Database
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT nama_desa, kepala_desa, nama_kecamatan, kabupaten, ketua_upz, sekretaris, logo_path, no_hp, total_jiwa, total_kk FROM pengaturan WHERE id=1")
        p_data = c.fetchone()
        if p_data:
            desa, kades, kec, kab, ketua, sekretaris, logo_path, no_hp, total_jiwa, total_kk = p_data
        else:
            desa = kades = kec = kab = ketua = sekretaris = logo_path = no_hp = ""
            total_jiwa = total_kk = 0
            
        c.execute("SELECT jiwa_beras, jiwa_uang, total_beras, total_uang, infaq FROM setoran_dkm")
        dkm_rows = c.fetchall()
        conn.close()

        # Kalkulasi
        t_jb = sum(int(r[0] or 0) for r in dkm_rows)
        t_ju = sum(int(r[1] or 0) for r in dkm_rows)
        t_tb = sum(float(r[2] or 0) for r in dkm_rows)
        t_tu = sum(float(r[3] or 0) for r in dkm_rows)
        t_inf = sum(float(r[4] or 0) for r in dkm_rows)

        # Perhitungan Penyaluran Hak Luar DKM
        desa_b = t_tb * 0.065
        desa_u = t_tu * 0.065
        salur_b = desa_b * 0.875
        salur_u = desa_u * 0.875
        amil_b = desa_b * 0.125
        amil_u = desa_u * 0.125
        
        kec_b = t_tb * 0.05
        kec_u = t_tu * 0.05
        
        kab_b = t_tb * 0.06
        kab_u = t_tu * 0.06

        # 2. Gambar PDF
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_margins(10, 10, 10)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Header box Model D3
        pdf.set_font("Arial", "", 10)
        pdf.set_xy(160, 10)
        pdf.cell(40, 6, "Model : D3", border=1, align="C")
        
        # Logo
        pdf.set_xy(10, 15)
        if logo_path and os.path.exists(logo_path):
            try:
                pdf.image(logo_path, x=20, y=15, w=22)
            except:
                pass

        pdf.set_xy(10, 20)
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(0, 128, 0)
        pdf.cell(0, 5, "BAZNAS", ln=True, align="C")
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "B", 8)
        pdf.cell(0, 4, "BADAN AMIL ZAKAT NASIONAL", ln=True, align="C")
        pdf.cell(0, 4, f"KABUPATEN {kab.upper() if kab else '-'}", ln=True, align="C")
        
        pdf.ln(3)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 5, "REKAPITULASI PENERIMAAN DAN PENYALURAN ZAKAT FITRAH DAN INFAQ", ln=True, align="C")
        pdf.cell(0, 5, f"BULAN RAMADHAN TAHUN 1447 H / {datetime.datetime.now().year} M", ln=True, align="C")
        
        pdf.ln(2)
        y_garis = pdf.get_y()
        pdf.set_line_width(0.6)
        pdf.line(10, y_garis, 200, y_garis)
        pdf.set_line_width(0.2)
        pdf.line(10, y_garis+1, 200, y_garis+1)
        
        pdf.ln(3)
        pdf.set_font("Arial", "B", 9)
        pdf.cell(30, 5, "Desa / Kelurahan", border=0)
        pdf.cell(5, 5, ":", border=0)
        pdf.cell(65, 5, f"{desa.upper() if desa else '-'}", border=0)
        pdf.cell(30, 5, "Jumlah KK", border=0)
        pdf.cell(5, 5, ":", border=0)
        pdf.cell(0, 5, f"{total_kk} KK" if total_kk else "-", border=0, ln=True)
        
        pdf.cell(30, 5, "Kecamatan", border=0)
        pdf.cell(5, 5, ":", border=0)
        pdf.cell(65, 5, f"{kec.upper() if kec else '-'}", border=0)
        pdf.cell(30, 5, "Jumlah Jiwa", border=0)
        pdf.cell(5, 5, ":", border=0)
        pdf.cell(0, 5, f"{total_jiwa} Jiwa" if total_jiwa else "-", border=0, ln=True)
        
        pdf.cell(100, 5, "", border=0)
        pdf.cell(30, 5, "No. HP Pengumpul", border=0)
        pdf.cell(5, 5, ":", border=0)
        pdf.cell(0, 5, f"{no_hp if no_hp else '-'}", border=0, ln=True)
        
        pdf.ln(1)
        y_garis = pdf.get_y()
        pdf.set_line_width(0.6)
        pdf.line(10, y_garis, 200, y_garis)
        pdf.set_line_width(0.2)
        pdf.line(10, y_garis+1, 200, y_garis+1)
        
        pdf.ln(4)
        
        # --- SECTION A. PENGHIMPUNAN ---
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, "A.  PENGHIMPUNAN", ln=True)
        
        pdf.set_font("Arial", "B", 9)
        pdf.cell(10, 6, "")
        pdf.cell(0, 6, "1. Zakat Fitrah", ln=True)
        
        # Tabel Zakat Fitrah
        pdf.cell(10, 6, "")
        pdf.cell(10, 6, "", border="LRT")
        pdf.cell(60, 6, "Jumlah Total Penghimpunan :", border="LRT")
        pdf.cell(15, 6, "Beras", border=1)
        pdf.cell(5, 6, ":", border=1, align="C")
        pdf.cell(30, 6, f"{t_tb:,.2f} kg".replace(",", "X").replace(".", ",").replace("X", "."), border=1, align="R")
        pdf.cell(35, 6, f"{t_jb:,} Orang".replace(",", "."), border=1, align="R", ln=True)
        
        pdf.cell(10, 6, "")
        pdf.cell(10, 6, "", border="LRB")
        pdf.cell(60, 6, "", border="LRB")
        pdf.cell(15, 6, "Uang", border=1)
        pdf.cell(5, 6, ":", border=1, align="C")
        pdf.cell(30, 6, f"Rp {int(t_tu):,}".replace(",", "."), border=1, align="L")
        pdf.cell(35, 6, f"{t_ju:,} Orang".replace(",", "."), border=1, align="R", ln=True)
        
        pdf.ln(3)
        pdf.cell(10, 6, "")
        pdf.cell(0, 6, "2. Infaq", ln=True)
        
        # Tabel Infaq
        pdf.cell(10, 6, "")
        pdf.cell(105, 6, "Uraian", border=1, align="C")
        pdf.cell(40, 6, "Jumlah", border=1, align="C", ln=True)
        
        pdf.cell(10, 6, "")
        pdf.cell(10, 6, "a.", border=1, align="C")
        pdf.cell(65, 6, "Jumlah Total Penghimpunan : Jumlah :", border=1)
        pdf.cell(10, 6, "Rp", border="LBT")
        pdf.cell(20, 6, f"{int(t_inf):,}".replace(",", ".") if t_inf else "-", border="RBT", align="R")
        pdf.cell(40, 6, "0 Orang", border=1, align="C", ln=True)
        
        pdf.ln(2)
        pdf.set_font("Arial", "", 9)
        pdf.cell(10, 5, "")
        pdf.cell(0, 5, "Pendistribusian harus sesuai dengan Ketentuan yang telah disepakati yaitu 6,5% Dana Salur dan Dana Amil", ln=True)
        
        pdf.ln(3)
        
        # --- SECTION B. PENYALURAN ---
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, "B.  PENYALURAN", ln=True)
        
        pdf.set_font("Arial", "B", 9)
        pdf.cell(10, 6, "")
        pdf.cell(0, 6, "1. Zakat Fitrah", ln=True)
        
        # Header Tabel Penyaluran
        pdf.cell(10, 6, "")
        pdf.cell(35, 6, "Penyaluran", border=1, align="C")
        pdf.cell(45, 6, "Asnaf", border=1, align="C")
        pdf.cell(20, 6, "Jenis", border=1, align="C")
        pdf.cell(35, 6, "Jumlah", border=1, align="C")
        pdf.cell(40, 6, "Ket", border=1, align="C", ln=True)
        
        pdf.set_font("Arial", "", 9)
        # Row 1 (Desa - Keseluruhan Beras)
        pdf.cell(10, 6, "")
        pdf.cell(35, 6, " a.  Desa", border="LRT")
        pdf.cell(45, 6, " 6,5% (Keseluruhan)", border="LRT", align="C")
        pdf.cell(20, 6, " Beras", border=1)
        pdf.cell(35, 6, f"{desa_b:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), border=1, align="R")
        pdf.cell(40, 6, " Kg", border=1, align="L", ln=True)
        
        # Row 2 (Desa - Keseluruhan Uang)
        pdf.cell(10, 6, "")
        pdf.cell(35, 6, "", border="LR")
        pdf.cell(45, 6, "", border="LRB")
        pdf.cell(20, 6, " Uang", border=1)
        pdf.cell(35, 6, f"{desa_u:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), border=1, align="R")
        pdf.cell(40, 6, " Rupiah", border=1, align="L", ln=True)
        
        # Row 3 (Dana Salur - Beras)
        pdf.cell(10, 6, "")
        pdf.cell(35, 6, "", border="LR")
        pdf.cell(45, 6, " Dana Salur", border="LRT", align="C")
        pdf.cell(20, 6, " Beras", border=1)
        pdf.cell(35, 6, f"{salur_b:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), border=1, align="R")
        pdf.cell(40, 6, " Kg", border=1, align="L", ln=True)
        
        # Row 4 (Dana Salur - Uang)
        pdf.cell(10, 6, "")
        pdf.cell(35, 6, "", border="LR")
        pdf.cell(45, 6, "", border="LRB")
        pdf.cell(20, 6, " Uang", border=1)
        pdf.cell(35, 6, f"{salur_u:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), border=1, align="R")
        pdf.cell(40, 6, " Rupiah", border=1, align="L", ln=True)
        
        # Row 5 (Hak Amil - Beras)
        pdf.cell(10, 6, "")
        pdf.cell(35, 6, "", border="LR")
        pdf.cell(45, 6, " Hak Amil", border="LRT", align="C")
        pdf.cell(20, 6, " Beras", border=1)
        pdf.cell(35, 6, f"{amil_b:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), border=1, align="R")
        pdf.cell(40, 6, " Kg", border=1, align="L", ln=True)
        
        # Row 6 (Hak Amil - Uang)
        pdf.cell(10, 6, "")
        pdf.cell(35, 6, "", border="LRB")
        pdf.cell(45, 6, "", border="LRB")
        pdf.cell(20, 6, " Uang", border=1)
        pdf.cell(35, 6, f"{amil_u:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), border=1, align="R")
        pdf.cell(40, 6, " Rupiah", border=1, align="L", ln=True)
        
        # Row 7 (Kecamatan - Beras)
        pdf.cell(10, 6, "")
        pdf.cell(35, 6, " b. Kecamatan 5,00%", border="LRT")
        pdf.cell(45, 6, " Sabillillah dan Amilin", border="LRT", align="C")
        pdf.cell(20, 6, " Beras", border=1)
        pdf.cell(35, 6, f"{kec_b:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), border=1, align="R")
        pdf.cell(40, 6, " Kg", border=1, align="L", ln=True)
        
        # Row 8 (Kecamatan - Uang)
        pdf.cell(10, 6, "")
        pdf.cell(35, 6, "", border="LRB")
        pdf.cell(45, 6, "", border="LRB")
        pdf.cell(20, 6, " Uang", border=1)
        pdf.cell(35, 6, f"{kec_u:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), border=1, align="R")
        pdf.cell(40, 6, " Rupiah", border=1, align="L", ln=True)
        
        # Row 9 (BAZNAS - Beras)
        pdf.cell(10, 6, "")
        pdf.cell(35, 6, " b. BAZNAS 6,00%", border="LRT")
        pdf.cell(45, 6, " Sabillillah dan Amilin", border="LRT", align="C")
        pdf.cell(20, 6, " Beras", border=1)
        pdf.cell(35, 6, f"{kab_b:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), border=1, align="R")
        pdf.cell(40, 6, " Kg", border=1, align="L", ln=True)
        
        # Row 10 (BAZNAS - Uang)
        pdf.cell(10, 6, "")
        pdf.cell(35, 6, "", border="LRB")
        pdf.cell(45, 6, "", border="LRB")
        pdf.cell(20, 6, " Uang", border=1)
        pdf.cell(35, 6, f"{kab_u:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), border=1, align="R")
        pdf.cell(40, 6, " Rupiah", border=1, align="L", ln=True)
        
        pdf.ln(5)
        
        # --- TANDA TANGAN ---
        pdf.cell(100, 5, "")
        
        # Integrasi Pengaturan Titimangsa dari Menu Cetak Utama
        if tempat_ba and tgl_ba:
            pdf.cell(90, 5, f"{tempat_ba}, {tgl_ba}", align="C", ln=True)
        else:
            pdf.cell(90, 5, f"{kab.capitalize() if kab else 'Tasikmalaya'}, ................................{datetime.datetime.now().year}", align="C", ln=True)
        
        pdf.cell(190, 5, "Panitia Pengumpul", align="C", ln=True)
        pdf.cell(95, 5, "Ketua UPZ DKM", align="C")
        pdf.cell(95, 5, "Sekretaris UPZ DKM", align="C", ln=True)
        
        pdf.ln(15)
        pdf.set_font("Arial", "B", 10)
        nama_ketua = ketua if ketua else "0"
        nama_sekretaris = sekretaris if sekretaris else "0"
        
        pdf.cell(95, 5, nama_ketua, align="C")
        pdf.cell(95, 5, nama_sekretaris, align="C", ln=True)
        
        pdf.ln(5)
        
        # --- KETERANGAN ---
        pdf.set_font("Arial", "B", 9)
        pdf.cell(0, 5, "Keterangan :", ln=True)
        pdf.set_font("Arial", "", 9)
        pdf.cell(0, 5, "Dibuat rangkap 3:", ln=True)
        pdf.cell(0, 5, "-    Satu untuk UPZ Desa/Kelurahan", ln=True)
        pdf.cell(0, 5, "-    Satu untuk UPZ Kecamatan", ln=True)
        pdf.cell(0, 5, "-    Satu untuk BAZNAS", ln=True)
        
        # GENERATE UNDUHAN
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        ts = int(time.time())
        
        st.success("✨ Dokumen D3 (Format Persis Gambar) berhasil disiapkan!")
        st.download_button(
            label="📥 UNDUH PDF D3 SEKARANG",
            data=pdf_bytes,
            file_name=f"Format_D3_Rekapitulasi_{desa}_{ts}.pdf",
            mime="application/pdf",
            width="stretch"
        )