import streamlit as st
import sqlite3
import datetime
import os
import time
from fpdf import FPDF
from config import DB_NAME

def render_ui(desa_default, no_ba, hari_ba, tgl_ba, tempat_ba):
    st.subheader("📄 Format D2 (Penerimaan Zakat & Infaq)")
    st.write("Rekapitulasi penerimaan Zakat Fitrah dan Infaq dari seluruh DKM (Sesuai Format Gambar/A4 Portrait).")
    
    if st.button("Siapkan Dokumen D2", width="stretch"):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # 1. Ambil data Pengaturan
        c.execute("SELECT nama_desa, kepala_desa, nama_kecamatan, kabupaten, ketua_upz, sekretaris, logo_path, no_hp, total_jiwa, total_kk FROM pengaturan WHERE id=1")
        p_data = c.fetchone()
        if p_data:
            desa, kades, kec, kab, ketua, sekretaris, logo_path, no_hp, total_jiwa, total_kk = p_data
        else:
            desa = kades = kec = kab = ketua = sekretaris = logo_path = no_hp = ""
            total_jiwa = total_kk = 0
            
        # 2. Ambil data Setoran
        c.execute("SELECT * FROM setoran_dkm ORDER BY nama_dkm ASC, perwakilan ASC")
        dkm_rows_detail = c.fetchall()
        conn.close()

        # 3. Setup PDF (Portrait A4)
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_margins(10, 10, 10)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # --- HEADER KOP SURAT ---
        pdf.set_font("Arial", "", 10)
        pdf.set_xy(160, 10)
        pdf.cell(40, 6, "Model : D2", border=1, align="C")
        
        pdf.set_xy(10, 10)
        # Logo Garuda/BAZNAS (Jika path logo valid)
        if logo_path and os.path.exists(logo_path):
            try:
                pdf.image(logo_path, x=95, y=10, w=20)
            except:
                pass
        
        # Teks Header
        pdf.set_y(30)
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(0, 128, 0) # Warna hijau (opsional)
        pdf.cell(0, 5, "BAZNAS", ln=True, align="C")
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "B", 8)
        pdf.cell(0, 4, "BADAN AMIL ZAKAT NASIONAL", ln=True, align="C")
        pdf.cell(0, 4, f"KABUPATEN {kab.upper() if kab else '-'}", ln=True, align="C")
        
        pdf.ln(3)
        y_garis = pdf.get_y()
        pdf.set_line_width(0.2)
        pdf.line(10, y_garis, 200, y_garis)
        
        pdf.ln(2)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 5, "DAFTAR PENERIMAAN ZAKAT FITRAH DAN INFAQ", ln=True, align="C")
        pdf.cell(0, 5, f"BULAN RAMADHAN TAHUN 1447 H / {datetime.datetime.now().year} M", ln=True, align="C")
        
        # Garis Ganda Bawah Judul
        pdf.ln(2)
        y_garis = pdf.get_y()
        pdf.set_line_width(0.6)
        pdf.line(10, y_garis, 200, y_garis)
        pdf.set_line_width(0.2)
        pdf.line(10, y_garis+1, 200, y_garis+1)
        
        pdf.ln(4)
        
        # --- INFO DESA ---
        pdf.set_font("Arial", "B", 9)
        pdf.cell(30, 5, "Desa / Kelurahan", border=0)
        pdf.cell(5, 5, ":", border=0)
        pdf.cell(75, 5, f"{desa.upper() if desa else '-'}", border=0)
        pdf.cell(30, 5, "Jumlah KK", border=0)
        pdf.cell(5, 5, ":", border=0)
        pdf.cell(0, 5, f"{total_kk if total_kk else '-'}", border=0, ln=True)
        
        pdf.cell(30, 5, "Kecamatan", border=0)
        pdf.cell(5, 5, ":", border=0)
        pdf.cell(75, 5, f"{kec.upper() if kec else '-'}", border=0)
        pdf.cell(30, 5, "Jumlah Jiwa", border=0)
        pdf.cell(5, 5, ":", border=0)
        pdf.cell(0, 5, f"{total_jiwa if total_jiwa else '-'}", border=0, ln=True)
        
        pdf.cell(110, 5, "", border=0)
        pdf.cell(30, 5, "No. HP Pengumpul", border=0)
        pdf.cell(5, 5, ":", border=0)
        pdf.cell(0, 5, f"{no_hp if no_hp else '-'}", border=0, ln=True)
        
        pdf.ln(2)
        
        # --- HELPER HEADER TABEL ---
        def draw_header_d2(pdf):
            y_h = pdf.get_y()
            pdf.set_line_width(0.5)
            pdf.line(10, y_h, 200, y_h)
            pdf.set_line_width(0.2)
            pdf.line(10, y_h+1, 200, y_h+1)
            
            pdf.set_y(y_h+2)
            pdf.set_font("Arial", "B", 9)
            y_start = pdf.get_y()
            
            # Baris 1 & 2 Gabungan
            pdf.cell(10, 12, "No.", 1, 0, "C")
            pdf.cell(55, 12, "Nama DKM", 1, 0, "C")
            pdf.cell(20, 12, "Jml. Jiwa", 1, 0, "C")
            
            x_zakat = pdf.get_x()
            pdf.cell(60, 6, "Zakat Fitrah", 1, 0, "C")
            
            x_infaq = pdf.get_x()
            pdf.cell(45, 6, "Infaq Ramadhan", 1, 1, "C")
            
            # Baris 2 (Sub-kolom Zakat & Infaq)
            pdf.set_xy(x_zakat, y_start+6)
            pdf.cell(25, 6, "Beras (Kg.)", 1, 0, "C")
            pdf.cell(35, 6, "Uang Tunai (Rp.)", 1, 0, "C")
            
            pdf.set_xy(x_infaq, y_start+6)
            pdf.cell(15, 6, "Org", 1, 0, "C")
            pdf.cell(30, 6, "Rp.", 1, 1, "C")
            
            # Baris 3 (Angka Penanda Kolom dengan Background Hijau)
            pdf.set_fill_color(0, 153, 51)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(10, 5, "1", 1, 0, "C", fill=True)
            pdf.cell(55, 5, "2", 1, 0, "C", fill=True)
            pdf.cell(20, 5, "3", 1, 0, "C", fill=True)
            pdf.cell(25, 5, "4", 1, 0, "C", fill=True)
            pdf.cell(35, 5, "5", 1, 0, "C", fill=True)
            pdf.cell(15, 5, "6", 1, 0, "C", fill=True)
            pdf.cell(30, 5, "7", 1, 1, "C", fill=True)
            pdf.set_fill_color(255, 255, 255) # Reset fill color
            
        draw_header_d2(pdf)
        
        # --- KONTEN TABEL ---
        pdf.set_font("Arial", "", 9)
        
        t_jiwa = 0
        t_beras = 0
        t_uang = 0
        t_rp_infaq = 0
        
        for i, r in enumerate(dkm_rows_detail):
            if pdf.get_y() > 250:
                pdf.add_page()
                draw_header_d2(pdf)
                pdf.set_font("Arial", "", 9)
            
            nama_dkm = (str(r[1]) + (" - " + str(r[3]) if r[3] else ""))[:35]
            # Menggunakan indeks kolom: r[6]=jiwa_beras, r[7]=jiwa_uang, r[10]=total_beras, r[11]=total_uang, r[12]=infaq
            jiwa = int(r[6] or 0) + int(r[7] or 0)
            beras = float(r[10] or 0)
            uang = float(r[11] or 0)
            infaq = float(r[12] or 0)
            
            t_jiwa += jiwa
            t_beras += beras
            t_uang += uang
            t_rp_infaq += infaq
            
            pdf.cell(10, 7, str(i+1), 1, 0, "C")
            pdf.cell(55, 7, f" {nama_dkm.upper()}", 1, 0, "L")
            
            # Format angka koma dan titik ejaan Indonesia
            jiwa_str = f"{jiwa:.1f}".replace(".", ",") if jiwa else "-"
            beras_str = f"{beras:.1f}".replace(".", ",") if beras else "-"
            uang_str = f"{int(uang):,}".replace(",", ".") if uang else "-"
            infaq_str = f"{int(infaq):,}".replace(",", ".") if infaq else "-"
            
            pdf.cell(20, 7, jiwa_str, 1, 0, "R")
            pdf.cell(25, 7, beras_str, 1, 0, "R")
            pdf.cell(35, 7, uang_str, 1, 0, "R")
            pdf.cell(15, 7, "-", 1, 0, "C") # Kolom Orang Infaq (Kosong di draft)
            pdf.cell(30, 7, infaq_str, 1, 1, "R")

        # --- FOOTER JUMLAH ---
        pdf.set_font("Arial", "B", 9)
        pdf.cell(65, 8, "JUMLAH", 1, 0, "C")
        
        # Format desimal total persis gambar (.00)
        t_jiwa_str = f"{t_jiwa:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if t_jiwa else "-"
        t_beras_str = f"{t_beras:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if t_beras else "-"
        t_uang_str = f"{int(t_uang):,}".replace(",", ".") + ",00" if t_uang else "-"
        t_infaq_str = f"{int(t_rp_infaq):,}".replace(",", ".") + ",00" if t_rp_infaq else "-"
        
        pdf.cell(20, 8, t_jiwa_str, 1, 0, "R")
        pdf.cell(25, 8, t_beras_str, 1, 0, "R")
        pdf.cell(35, 8, t_uang_str, 1, 0, "R")
        pdf.cell(15, 8, "-", 1, 0, "C")
        pdf.cell(30, 8, t_infaq_str, 1, 1, "R")
        
        pdf.ln(10)
        
        # --- TANDA TANGAN ---
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 5, "Panitia Pengumpul", 0, 1, "C")
        pdf.ln(5)
        pdf.cell(95, 5, "Ketua UPZ Desa", 0, 0, "C")
        pdf.cell(95, 5, "Sekretaris UPZ Desa", 0, 1, "C")
        pdf.ln(20)
        pdf.set_font("Arial", "B", 10)
        
        # Sesuai draft tanda tangan hanya diisi angka "0" atau teks
        nama_ketua = ketua if ketua else "0"
        nama_sekretaris = sekretaris if sekretaris else "0"
        
        pdf.cell(95, 5, nama_ketua, 0, 0, "C")
        pdf.cell(95, 5, nama_sekretaris, 0, 1, "C")
        
        # --- GENERATE UNDUHAN ---
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        ts = int(time.time())
        
        st.success("✨ Dokumen D2 (Format A4 Sesuai Gambar) berhasil disiapkan!")
        st.download_button(
            label="📥 UNDUH PDF D2 SEKARANG",
            data=pdf_bytes,
            file_name=f"Format_D2_Penerimaan_{desa}_{ts}.pdf",
            mime="application/pdf",
            width="stretch"
        )