import streamlit as st
import sqlite3
import datetime
import os
import time
from fpdf import FPDF
from config import DB_NAME

def render_ui(desa_default, no_ba, hari_ba, tgl_ba, tempat_ba):
    st.subheader("📄 Format D1 (Surat Pengantar)")
    st.write("Cetak Surat resmi pengantar dokumen laporan desa ke kecamatan (Sesuai Draft D1).")
    
    if st.button("🖨️ Generate PDF D1", width="stretch", type="primary"):
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
        conn.close()
        
        desa = desa_default

        # 2. Setup PDF (Portrait A4)
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_margins(15, 15, 15)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # --- HEADER MODEL BOX ---
        pdf.set_font("Arial", "", 10)
        pdf.set_xy(160, 10)
        pdf.cell(35, 6, "Model : D1", border=1, align="C")
        
        pdf.set_xy(15, 10)
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
        pdf.line(15, y_garis, 195, y_garis)
        
        pdf.ln(2)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 5, "LAPORAN PENGUMPULAN DAN PENYALURAN ZAKAT FITRAH DAN INFAQ", ln=True, align="C")
        pdf.cell(0, 5, f"BULAN RAMADHAN TAHUN 1446 H / {datetime.datetime.now().year} M", ln=True, align="C")

        pdf.ln(2)
        y_garis = pdf.get_y()
        pdf.set_line_width(0.6)
        pdf.line(15, y_garis, 195, y_garis)
        pdf.set_line_width(0.2)
        pdf.line(15, y_garis+1, 195, y_garis+1)
        
        pdf.ln(6)
        
        # --- META SURAT ---
        pdf.set_font("Arial", "", 10)
        pdf.cell(20, 5, "Nomor", border=0)
        pdf.cell(5, 5, ":", border=0, align="C")
        pdf.cell(0, 5, "Istimewa" if not no_ba else no_ba, border=0, ln=True)
        
        pdf.cell(20, 5, "Lampiran", border=0)
        pdf.cell(5, 5, ":", border=0, align="C")
        pdf.cell(0, 5, "1 (Satu) berkas", border=0, ln=True)
        
        pdf.cell(20, 5, "Perihal", border=0)
        pdf.cell(5, 5, ":", border=0, align="C")
        pdf.cell(0, 5, "Laporan", border=0, ln=True)
        
        pdf.ln(4)
        
        # --- TUJUAN SURAT ---
        pdf.cell(0, 5, "Yang terhormat", ln=True)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 5, "Ketua UPZ Kecamatan", ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 5, "di-", ln=True)
        pdf.cell(10, 5, "")
        pdf.cell(0, 5, "Tempat", ln=True)
        
        pdf.ln(5)
        
        # --- PARAGRAF PEMBUKA ---
        pdf.cell(0, 5, "Assalamualaikum Wr. Wb.", ln=True)
        pdf.ln(2)
        
        txt_pembuka = f"Bersama ini kami sampaikan berkas laporan lengkap pengumpulan dan penyaluran Zakat Fitrah dan infak Ramadhan Tahun 1446 H / {datetime.datetime.now().year} M dengan data sebagai berikut :"
        pdf.multi_cell(0, 5, txt_pembuka)
        pdf.ln(2)
        
        # --- INFO IDENTITAS DESA ---
        pdf.set_font("Arial", "B", 10)
        pdf.cell(35, 5, "Desa", border=0)
        pdf.cell(5, 5, ":", border=0)
        pdf.cell(0, 5, f"{desa.upper() if desa else '-'}", border=0, ln=True)
        
        pdf.cell(35, 5, "Kecamatan", border=0)
        pdf.cell(5, 5, ":", border=0)
        pdf.cell(0, 5, f"{kec.upper() if kec else '-'}", border=0, ln=True)
        
        pdf.cell(35, 5, "Jumlah KK", border=0)
        pdf.cell(5, 5, ":", border=0)
        pdf.cell(0, 5, f"{total_kk if total_kk else '-'}", border=0, ln=True)
        
        pdf.cell(35, 5, "Jumlah Jiwa", border=0)
        pdf.cell(5, 5, ":", border=0)
        pdf.cell(0, 5, f"{total_jiwa if total_jiwa else '-'}", border=0, ln=True)
        
        pdf.cell(35, 5, "No. HP", border=0)
        pdf.cell(5, 5, ":", border=0)
        pdf.cell(0, 5, f"{no_hp if no_hp else '-'}", border=0, ln=True)
        
        pdf.ln(4)
        
        # --- TABEL DOKUMEN (CEKLIS) ---
        pdf.set_font("Arial", "B", 10)
        pdf.cell(10, 8, "NO", 1, 0, "C")
        pdf.cell(140, 8, "LEMBARAN", 1, 0, "C")
        pdf.cell(30, 8, "CEKLIS", 1, 1, "C")
        
        pdf.set_font("Arial", "", 10)
        
        # Menyesuaikan daftar dokumen persis sesuai urutan laporan sistem
        lampiran = [
            "Daftar pengumpulan zakat fitrah dan infak Ramadhan (D2)",
            "Tabel Pembagian Zakat Fitrah (D3)",
            "Daftar penyaluran zakat fitrah asnaf Sabilillah (D4)",
            "Rekap Penyaluran Zakat Fitrah berdasarkan Program (D5)",
            "Daftar Penyaluran Zakat Fitrah Asnaf Amilin (D6)",
            "Berita Acara Serah Terima Zakat Fitrah Kecamatan"
        ]
        
        for i, teks in enumerate(lampiran):
            pdf.cell(10, 8, str(i+1), 1, 0, "C")
            pdf.cell(140, 8, f" {teks}", 1, 0, "L")
            pdf.cell(30, 8, "", 1, 1, "C") # Kolom ceklis dibiarkan kosong untuk dicentang manual
            
        pdf.ln(6)
        
        # --- PARAGRAF PENUTUP ---
        pdf.cell(0, 5, "Demikian laporan ini kami sampaikan dan dapat diterima dengan baik.", ln=True)
        pdf.cell(0, 5, "Wassalamu'alaikum Wr. Wb.", ln=True)
        
        pdf.ln(10)
        
        # --- BLOK TANDA TANGAN KOREKSI LAYOUT ---
        if tempat_ba and tgl_ba:
            txt_tgl_ttd = f"{tempat_ba}, {tgl_ba}"
        else:
            txt_tgl_ttd = f"Tasikmalaya, ................................{datetime.datetime.now().year}"
            
        # 1. Tanggal (Rata Kanan)
        pdf.cell(0, 5, txt_tgl_ttd, align="R", ln=True)
        
        # 2. Panitia Pengumpul (Rata Tengah)
        pdf.cell(0, 5, "Panitia Pengumpul", align="C", ln=True)
        
        # 3. Jabatan TTD (Kiri dan Kanan)
        pdf.cell(90, 5, "Ketua UPZ Desa", align="C")
        pdf.cell(90, 5, "Sekretaris UPZ Desa", align="C", ln=True)
        
        pdf.ln(20)
        pdf.set_font("Arial", "B", 10)
        
        nama_ketua = ketua if ketua else "0"
        nama_sekretaris = sekretaris if sekretaris else "0"
        
        # 4. Nama Pejabat (Kiri dan Kanan)
        pdf.cell(90, 5, nama_ketua, align="C")
        pdf.cell(90, 5, nama_sekretaris, align="C", ln=True)
        
        # --- GENERATE UNDUHAN ---
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        ts = int(time.time())
        
        st.success("✨ Dokumen D1 (Surat Pengantar) berhasil disiapkan dengan format terbaru!")
        st.download_button(
            label="📥 UNDUH PDF D1 SEKARANG",
            data=pdf_bytes,
            file_name=f"Format_D1_Pengantar_{desa}_{ts}.pdf",
            mime="application/pdf",
            width="stretch"
        )