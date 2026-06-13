import streamlit as st
import sqlite3
import datetime
from fpdf import FPDF
from config import DB_NAME
from modulcetak.helper import get_pengaturan, cetak_kop_surat_resmi

def render_ui(desa_default, no_ba, hari_ba, tgl_ba, tempat_ba):
    st.write("🤝 **BAST 11% Kecamatan** - Berita Acara Serah Terima Hak Kecamatan & Kabupaten.")
    if st.button("🖨️ Generate BAST Kecamatan", width="stretch", type="primary"):
        desa, kades, kec, kab, ketua, sekretaris, logo_path, _, _, _ = get_pengaturan()
        desa = desa_default
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT SUM(total_beras), SUM(total_uang) FROM setoran_dkm WHERE UPPER(alamat_dkm)=UPPER(?)", (desa,))
        r = c.fetchone()
        conn.close()
        t_tb = r[0] or 0; t_tu = r[1] or 0

        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_margins(10, 10, 10); pdf.set_auto_page_break(auto=True, margin=15); pdf.add_page()
        cetak_kop_surat_resmi(pdf, desa, kec, kab, logo_path)

        pdf.set_font("Arial", "B", 14); pdf.cell(0, 8, "BERITA ACARA SERAH TERIMA ZAKAT FITRAH", ln=True, align="C"); pdf.ln(5)
        
        pdf.set_font("Arial", "", 12); pdf.multi_cell(0, 8, f"Pada hari ini, {hari_ba} tanggal {tgl_ba}, telah dilaksanakan penyerahan Zakat Fitrah dari UPZ Desa {desa} kepada UPZ Kecamatan {kec} sebesar 11% (Gabungan Hak Kecamatan 5% dan BAZNAS Kabupaten 6%) dari total penghimpunan Desa dengan rincian data sebagai berikut:")
        pdf.ln(5)
        
        kec_b = t_tb * 0.05; kec_u = t_tu * 0.05; kab_b = t_tb * 0.06; kab_u = t_tu * 0.06
        tot_b_11 = kec_b + kab_b; tot_u_11 = kec_u + kab_u
        
        pdf.set_font("Arial", "B", 11)
        pdf.cell(60, 8, "Tujuan Penyerahan", border=1, align="C"); pdf.cell(65, 8, "Beras (Kg)", border=1, align="C"); pdf.cell(65, 8, "Uang Tunai (Rp)", border=1, align="C", ln=True)
        pdf.set_font("Arial", "", 11)
        pdf.cell(60, 8, " 1. UPZ Kec. (5%)", border=1); pdf.cell(65, 8, f" {kec_b:.2f} Kg", border=1, align="C"); pdf.cell(65, 8, f" Rp {int(kec_u):,}", border=1, align="C", ln=True)
        pdf.cell(60, 8, " 2. BAZNAS Kab. (6%)", border=1); pdf.cell(65, 8, f" {kab_b:.2f} Kg", border=1, align="C"); pdf.cell(65, 8, f" Rp {int(kab_u):,}", border=1, align="C", ln=True)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(60, 8, " TOTAL DISERAHKAN", border=1); pdf.cell(65, 8, f" {tot_b_11:.2f} Kg", border=1, align="C"); pdf.cell(65, 8, f" Rp {int(tot_u_11):,}", border=1, align="C", ln=True); pdf.ln(10)
        
        pdf.set_font("Arial", "", 12); pdf.multi_cell(0, 8, "Demikian berita acara ini dibuat dengan sebenarnya dan penuh tanggung jawab untuk dapat dijadikan pedoman administrasi."); pdf.ln(20)
        pdf.cell(90, 8, "Pihak Penerima (Kecamatan),", 0, 0, "C"); pdf.cell(100, 8, "Pihak Penyerah (UPZ Desa),", 0, 1, "C"); pdf.ln(25)
        pdf.set_font("Arial", "B", 12); pdf.cell(90, 8, "( ........................................ )", 0, 0, "C"); pdf.cell(100, 8, f"( {ketua} )", 0, 1, "C")

        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        ts = datetime.datetime.now().strftime("%H%M%S")
        st.download_button("📥 UNDUH BAST KECAMATAN", data=pdf_bytes, file_name=f"BAST_Kecamatan_{desa}_{ts}.pdf", mime="application/pdf", use_container_width=True)