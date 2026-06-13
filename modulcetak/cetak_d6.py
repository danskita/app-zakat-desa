import streamlit as st
import sqlite3
import datetime
import os
import time
from fpdf import FPDF
from config import DB_NAME

def render_ui(desa_default, no_ba, hari_ba, tgl_ba, tempat_ba):
    st.subheader("📄 Format D6 (Penyaluran Amilin)")
    st.write("Cetak Daftar Penyaluran Zakat Fitrah untuk Asnaf Amilin (Sesuai Draft Terbaru).")
    
    if st.button("Siapkan Dokumen D6", width="stretch"):
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
            
        # 2. Ambil data Amilin dari database tersinkron
        try:
            c.execute("SELECT nama, jabatan, beras, uang FROM amilin ORDER BY id ASC")
            amilin_rows = c.fetchall()
        except Exception:
            amilin_rows = []
            
        conn.close()

        # 3. Setup PDF (Portrait A4)
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_margins(10, 10, 10)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # --- HEADER MODEL BOX ---
        pdf.set_font("Arial", "", 10)
        pdf.set_xy(160, 10)
        pdf.cell(40, 6, "Model : D6", border=1, align="C")
        
        pdf.set_xy(10, 10)
        # Logo Garuda/BAZNAS
        if logo_path and os.path.exists(logo_path):
            try:
                pdf.image(logo_path, x=95, y=10, w=20)
            except:
                pass
        
        # Teks Header KOP
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
        pdf.cell(0, 5, "DAFTAR PENYALURAN ZAKAT FITRAH UNTUK AMILIN", ln=True, align="C")
        pdf.cell(0, 5, f"BULAN RAMADHAN TAHUN 1446 H / {datetime.datetime.now().year} M", ln=True, align="C")

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
        
        # --- BERITA ACARA ---
        pdf.set_font("Arial", "BU", 11)
        pdf.cell(0, 6, "Berita Acara", ln=True, align="C")
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 6, "Penyaluran Zakat Fitrah Hak Amilin", ln=True, align="C")
        pdf.ln(2)
        
        pdf.set_font("Arial", "", 10)
        txt_hari = hari_ba if hari_ba else "........................"
        txt_tgl = tgl_ba if tgl_ba else "........................"
        
        txt_pembuka = f"Pada hari ini, {txt_hari} Tanggal {txt_tgl} Tahun {datetime.datetime.now().year} telah dilaksanakan penyaluran Zakat Fitrah Hak Amilin bertempat sebagaimana alamat tersebut di atas dengan daftar penerima sebagai berikut:"
        pdf.multi_cell(0, 5, txt_pembuka)
        pdf.ln(3)
        
        # --- HELPER HEADER TABEL ---
        def draw_header_d6(pdf):
            y_h = pdf.get_y()
            pdf.set_font("Arial", "B", 8)
            
            # Lebar Total = 190mm
            pdf.cell(10, 10, "NO.", 1, 0, "C")
            pdf.cell(55, 10, "NAMA", 1, 0, "C")
            pdf.cell(45, 10, "AMILIN / JABATAN", 1, 0, "C")
            
            x_bagi = pdf.get_x()
            pdf.cell(55, 5, "Jumlah Pembagian", 1, 0, "C")
            pdf.cell(25, 10, "TANDA TANGAN", 1, 1, "C")
            
            # Sub-kolom Pembagian
            pdf.set_xy(x_bagi, y_h + 5)
            pdf.cell(20, 5, "Beras (Kg)", 1, 0, "C")
            pdf.cell(35, 5, "Uang (Rp)", 1, 0, "C")
            
            # Baris Penomoran Hijau
            pdf.set_y(y_h + 10)
            pdf.set_fill_color(0, 153, 51)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(10, 5, "1", 1, 0, "C", fill=True)
            pdf.cell(55, 5, "2", 1, 0, "C", fill=True)
            pdf.cell(45, 5, "3", 1, 0, "C", fill=True)
            pdf.cell(20, 5, "4", 1, 0, "C", fill=True)
            pdf.cell(35, 5, "5", 1, 0, "C", fill=True)
            pdf.cell(25, 5, "6", 1, 1, "C", fill=True)
            pdf.set_fill_color(255, 255, 255)
            
        draw_header_d6(pdf)
        
        # --- KONTEN TABEL ---
        pdf.set_font("Arial", "", 8)
        
        tot_b = 0
        tot_u = 0
        
        if not amilin_rows:
            # Generate blank rows to mimic draft formatting if empty
            for i in range(5):
                pdf.cell(10, 8, str(i+1), 1, 0, "C")
                pdf.cell(55, 8, "", 1, 0, "L")
                pdf.cell(45, 8, "", 1, 0, "L")
                pdf.cell(20, 8, "", 1, 0, "C")
                pdf.cell(35, 8, "", 1, 0, "R")
                if (i+1) % 2 != 0:
                    pdf.cell(25, 8, f" {i+1}. .............", 1, 1, "L")
                else:
                    pdf.cell(25, 8, f"        {i+1}. .............", 1, 1, "L")
        else:
            for i, r in enumerate(amilin_rows):
                if pdf.get_y() > 250:
                    pdf.add_page()
                    draw_header_d6(pdf)
                    pdf.set_font("Arial", "", 8)
                
                penerima = str(r[0])[:35] if r[0] else "-"
                jabatan = str(r[1])[:30] if r[1] else "-"
                b = float(r[2] or 0)
                u = float(r[3] or 0)
                
                tot_b += b
                tot_u += u
                
                pdf.cell(10, 8, str(i+1), 1, 0, "C")
                pdf.cell(55, 8, f" {penerima}", 1, 0, "L")
                pdf.cell(45, 8, f" {jabatan}", 1, 0, "L")
                
                b_str = f"{b:.2f}".replace(".", ",") if b > 0 else "-"
                u_str = f"{int(u):,}".replace(",", ".") if u > 0 else "-"
                
                pdf.cell(20, 8, b_str, 1, 0, "C")
                pdf.cell(35, 8, u_str, 1, 0, "R")
                
                # Format Tanda Tangan Zig-zag
                if (i+1) % 2 != 0:
                    pdf.cell(25, 8, f" {i+1}. .............", 1, 1, "L")
                else:
                    pdf.cell(25, 8, f"        {i+1}. .............", 1, 1, "L")

        # --- FOOTER JUMLAH ---
        pdf.set_font("Arial", "B", 8)
        pdf.cell(110, 8, "JUMLAH ................................ :", 1, 0, "C")
        
        tot_b_str = f"{tot_b:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if tot_b else "0,00 kg"
        tot_u_str = f"Rp {int(tot_u):,}".replace(",", ".") + ",00" if tot_u else "Rp "
        
        pdf.cell(20, 8, tot_b_str, 1, 0, "C")
        pdf.cell(35, 8, tot_u_str, 1, 0, "R")
        pdf.cell(25, 8, "-", 1, 1, "C")
        
        pdf.ln(6)
        
        # --- PARAGRAF PENUTUP ---
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 5, "Demikian berita acara ini kami buat dengan sebenarnya dengan penuh tanggung jawab, agar yang berkepentingan\nmemakluminya.")
        
        pdf.ln(8)
        
        # --- BLOK TANDA TANGAN (SAMA DENGAN D4) ---
        if tempat_ba and tgl_ba:
            txt_tgl_ttd = f"{tempat_ba}, {tgl_ba}"
        else:
            txt_tgl_ttd = f"Tasikmalaya, ................................{datetime.datetime.now().year}"
            
        # 1. Tanggal (Rata Kanan)
        pdf.cell(0, 5, txt_tgl_ttd, align="R", ln=True)
        
        # 2. Panitia Pengumpul (Rata Tengah)
        pdf.cell(0, 5, "Panitia Pengumpul", align="C", ln=True)
        
        # 3. Jabatan TTD (Kiri dan Kanan)
        pdf.cell(95, 5, "Ketua UPZ Desa", align="C")
        pdf.cell(95, 5, "Sekretaris UPZ Desa", align="C", ln=True)
        
        pdf.ln(20)
        pdf.set_font("Arial", "B", 10)
        
        nama_ketua = ketua if ketua else "0"
        nama_sekretaris = sekretaris if sekretaris else "0"
        
        # 4. Nama Pejabat (Kiri dan Kanan)
        pdf.cell(95, 5, nama_ketua, align="C")
        pdf.cell(95, 5, nama_sekretaris, align="C", ln=True)
        
        # --- GENERATE UNDUHAN ---
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        ts = int(time.time())
        
        st.success("✨ Dokumen D6 (Penyaluran Amilin) berhasil disiapkan dengan format terbaru!")
        st.download_button(
            label="📥 UNDUH PDF D6 SEKARANG",
            data=pdf_bytes,
            file_name=f"Format_D6_Amilin_{desa}_{ts}.pdf",
            mime="application/pdf",
            width="stretch"
        )