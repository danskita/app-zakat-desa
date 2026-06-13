import streamlit as st
import sqlite3
import datetime
import os
import time
from fpdf import FPDF
from config import DB_NAME

def render_ui(desa_default, no_ba, hari_ba, tgl_ba, tempat_ba):
    st.subheader("📄 Format D5 (Daftar Penyaluran Mustahiq)")
    st.write("Cetak daftar penyaluran Zakat Fitrah dan Infaq kepada Mustahiq (Sesuai Draft D5 / A4 Portrait).")
    
    if st.button("Siapkan Dokumen D5", width="stretch"):
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
            
        # 2. Ambil data Mustahik
        try:
            c.execute("SELECT nama, alamat, asnaf, beras, uang FROM mustahik ORDER BY asnaf ASC, nama ASC")
            mustahik_rows = c.fetchall()
        except sqlite3.OperationalError:
            try:
                # Fallback jika penamaan kolom berbeda
                c.execute("SELECT nama_mustahik, alamat, kategori, jumlah_beras, jumlah_uang FROM mustahik")
                mustahik_rows = c.fetchall()
            except:
                mustahik_rows = []
                
        conn.close()

        # 3. Setup PDF (Portrait A4)
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_margins(10, 10, 10)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # --- HEADER KOP SURAT ---
        pdf.set_font("Arial", "", 10)
        pdf.set_xy(160, 10)
        pdf.cell(40, 6, "Model : D5", border=1, align="C")
        
        pdf.set_xy(10, 10)
        # Logo Garuda/BAZNAS
        if logo_path and os.path.exists(logo_path):
            try:
                pdf.image(logo_path, x=95, y=10, w=20)
            except:
                pass
        
        # Teks Header
        pdf.set_y(30)
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(0, 128, 0)
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
        pdf.cell(0, 5, "DAFTAR PENYALURAN ZAKAT FITRAH DAN INFAQ KEPADA MUSTAHIQ", ln=True, align="C")
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
        
        # --- HELPER HEADER TABEL D5 ---
        def draw_header_d5(pdf):
            y_h = pdf.get_y()
            pdf.set_line_width(0.5)
            pdf.line(10, y_h, 200, y_h)
            pdf.set_line_width(0.2)
            pdf.line(10, y_h+1, 200, y_h+1)
            
            pdf.set_y(y_h+2)
            pdf.set_font("Arial", "B", 9)
            y_start = pdf.get_y()
            
            # Lebar Total = 190mm
            pdf.cell(10, 12, "No.", 1, 0, "C")
            pdf.cell(45, 12, "Nama Mustahiq", 1, 0, "C")
            pdf.cell(35, 12, "Alamat", 1, 0, "C")
            pdf.cell(30, 12, "Asnaf", 1, 0, "C")
            
            x_terima = pdf.get_x()
            pdf.cell(45, 6, "Diterima", 1, 0, "C")
            
            x_ttd = pdf.get_x()
            pdf.cell(25, 12, "Tanda Tangan", 1, 1, "C")
            
            # Sub-kolom Diterima
            pdf.set_xy(x_terima, y_start+6)
            pdf.cell(20, 6, "Beras (Kg)", 1, 0, "C")
            pdf.cell(25, 6, "Uang (Rp)", 1, 0, "C")
            
            # Baris Penomoran Hijau
            pdf.set_xy(10, y_start+12)
            pdf.set_fill_color(0, 153, 51)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(10, 5, "1", 1, 0, "C", fill=True)
            pdf.cell(45, 5, "2", 1, 0, "C", fill=True)
            pdf.cell(35, 5, "3", 1, 0, "C", fill=True)
            pdf.cell(30, 5, "4", 1, 0, "C", fill=True)
            pdf.cell(20, 5, "5", 1, 0, "C", fill=True)
            pdf.cell(25, 5, "6", 1, 0, "C", fill=True)
            pdf.cell(25, 5, "7", 1, 1, "C", fill=True)
            pdf.set_fill_color(255, 255, 255)
            
        draw_header_d5(pdf)
        
        # --- KONTEN TABEL ---
        pdf.set_font("Arial", "", 9)
        
        t_beras = 0
        t_uang = 0
        
        if not mustahik_rows:
            pdf.cell(190, 8, "Belum ada data mustahik untuk disalurkan.", 1, 1, "C")
        else:
            for i, r in enumerate(mustahik_rows):
                if pdf.get_y() > 250:
                    pdf.add_page()
                    draw_header_d5(pdf)
                    pdf.set_font("Arial", "", 9)
                
                nama = str(r[0])[:25] if r[0] else "-"
                alamat = str(r[1])[:20] if r[1] else "-"
                asnaf = str(r[2])[:15] if r[2] else "-"
                beras = float(r[3] or 0)
                uang = float(r[4] or 0)
                
                t_beras += beras
                t_uang += uang
                
                pdf.cell(10, 8, str(i+1), 1, 0, "C")
                pdf.cell(45, 8, f" {nama}", 1, 0, "L")
                pdf.cell(35, 8, f" {alamat}", 1, 0, "L")
                pdf.cell(30, 8, f" {asnaf}", 1, 0, "L")
                
                beras_str = f"{beras:.2f}".replace(".", ",") if beras > 0 else "-"
                uang_str = f"{int(uang):,}".replace(",", ".") if uang > 0 else "-"
                
                pdf.cell(20, 8, beras_str, 1, 0, "C")
                pdf.cell(25, 8, uang_str, 1, 0, "R")
                
                # Format Tanda Tangan Zig-zag
                if (i+1) % 2 != 0:
                    ttd_text = f" {i+1}. ............."
                    pdf.cell(25, 8, ttd_text, 1, 1, "L")
                else:
                    ttd_text = f"            {i+1}. ............."
                    pdf.cell(25, 8, ttd_text, 1, 1, "L")

        # --- FOOTER JUMLAH ---
        pdf.set_font("Arial", "B", 9)
        pdf.cell(120, 8, "JUMLAH TOTAL PENYALURAN", 1, 0, "C")
        
        t_beras_str = f"{t_beras:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if t_beras else "-"
        t_uang_str = f"{int(t_uang):,}".replace(",", ".") + ",00" if t_uang else "-"
        
        pdf.cell(20, 8, t_beras_str, 1, 0, "C")
        pdf.cell(25, 8, t_uang_str, 1, 0, "R")
        pdf.cell(25, 8, "", 1, 1, "C")
        
        pdf.ln(8)
        
        # --- TANDA TANGAN ---
        pdf.set_font("Arial", "", 10)
        if tempat_ba and tgl_ba:
            pdf.cell(190, 5, f"{tempat_ba}, {tgl_ba}", align="R", ln=True)
        else:
            pdf.cell(190, 5, f"{kab.capitalize() if kab else 'Tasikmalaya'}, ................................{datetime.datetime.now().year}", align="R", ln=True)
        
        pdf.cell(190, 5, "Panitia Pengumpul", align="C", ln=True)
        pdf.ln(2)
        pdf.cell(95, 5, "Ketua UPZ Desa", 0, 0, "C")
        pdf.cell(95, 5, "Sekretaris UPZ Desa", 0, 1, "C")
        
        pdf.ln(20)
        pdf.set_font("Arial", "B", 10)
        
        nama_ketua = ketua if ketua else "0"
        nama_sekretaris = sekretaris if sekretaris else "0"
        
        pdf.cell(95, 5, nama_ketua, 0, 0, "C")
        pdf.cell(95, 5, nama_sekretaris, 0, 1, "C")
        
        # --- GENERATE UNDUHAN ---
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        ts = int(time.time())
        
        st.success("✨ Dokumen D5 (Daftar Penyaluran Mustahiq) berhasil disiapkan!")
        st.download_button(
            label="📥 UNDUH PDF D5 SEKARANG",
            data=pdf_bytes,
            file_name=f"Format_D5_Penyaluran_Mustahiq_{desa}_{ts}.pdf",
            mime="application/pdf",
            width="stretch"
        )