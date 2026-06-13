import streamlit as st
import sqlite3
import datetime
from fpdf import FPDF
from config import DB_NAME
from modulcetak.helper import get_pengaturan, cetak_kop_surat_resmi

def render_ui(desa_default, no_ba, hari_ba, tgl_ba, tempat_ba):
    st.write("🎟️ **Berita Acara Serah Terima (BAST) Kupon** - Bukti serah terima fisik kupon infaq dengan DKM.")
    if st.button("🖨️ Generate BAST Kupon", width="stretch", type="primary"):
        desa, kades, kec, kab, ketua, sekretaris, logo_path, no_hp, total_jiwa, total_kk = get_pengaturan()
        desa = desa_default
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("""SELECT k.nama_dkm, k.jumlah_awal, k.kupon_laku, k.kupon_kembali, k.kupon_hilang, k.nominal_disetor, m.ketua_dkm, m.alamat_dkm 
                     FROM kupon_infaq k LEFT JOIN master_dkm m ON k.nama_dkm = m.nama_dkm 
                     WHERE UPPER(k.desa_pengelola) = UPPER(?) ORDER BY k.nama_dkm ASC""", (desa,))
        rows = c.fetchall()
        conn.close()
        
        if not rows:
            st.error("Data Kupon Infaq masih kosong!")
            return
            
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_margins(10, 10, 10); pdf.set_auto_page_break(auto=True, margin=15)
        
        tot_awal=0; tot_laku=0; tot_kembali=0; tot_hilang=0; tot_uang=0
        for r in rows:
            nama_dkm = r[0]; k_awal = int(r[1] or 0); k_laku = int(r[2] or 0); k_kembali = int(r[3] or 0); k_hilang = int(r[4] or 0); uang_infaq = float(r[5] or 0)
            ketua_dkm = r[6] if r[6] else "....................................."
            alamat_dkm = r[7] if r[7] else ".............................................................."
            tot_awal += k_awal; tot_laku += k_laku; tot_kembali += k_kembali; tot_hilang += k_hilang; tot_uang += uang_infaq
            
            pdf.add_page(); cetak_kop_surat_resmi(pdf, desa, kec, kab, logo_path)
            pdf.set_font("Arial", "B", 14); pdf.cell(0, 8, "BERITA ACARA SERAH TERIMA BARANG", ln=True, align="C")
            pdf.set_font("Arial", "", 12); pdf.cell(0, 6, no_ba, ln=True, align="C"); pdf.ln(10)
            
            pdf.cell(0, 8, "Yang bertanda tangan di bawah ini:", ln=True)
            pdf.cell(30, 8, "Nama", border=0); pdf.cell(5, 8, ":", border=0); pdf.set_font("Arial", "B", 12); pdf.cell(0, 8, f"{ketua.upper()}", border=0, ln=True); pdf.set_font("Arial", "", 12)
            pdf.cell(30, 8, "Jabatan", border=0); pdf.cell(5, 8, ":", border=0); pdf.cell(0, 8, f"KETUA UPZ DESA {desa.upper()}", border=0, ln=True)
            pdf.cell(0, 8, "selanjutnya disebut  Pihak Pertama (Pihak I)", ln=True); pdf.ln(5)
            
            pdf.cell(30, 8, "Nama Amil", border=0); pdf.cell(5, 8, ":", border=0); pdf.set_font("Arial", "B", 12); pdf.cell(0, 8, f"{ketua_dkm.upper()}", border=0, ln=True); pdf.set_font("Arial", "", 12)
            pdf.cell(30, 8, "Jabatan", border=0); pdf.cell(5, 8, ":", border=0); pdf.cell(0, 8, f"KETUA UPZ DKM {nama_dkm.upper()}", border=0, ln=True)
            pdf.cell(30, 8, "Alamat", border=0); pdf.cell(5, 8, ":", border=0); pdf.cell(0, 8, f"{alamat_dkm}", border=0, ln=True)
            pdf.cell(0, 8, "Yang selanjutnya disebut  Pihak Kedua (Pihak II)", ln=True); pdf.ln(8)
            
            teks_isi = f"Bahwa pada hari ini {hari_ba} tanggal {tgl_ba} PIHAK PERTAMA telah menyerahkan Kupon Infaq Ramadhan kepada PIHAK KEDUA berjumlah {k_awal} lembar dengan kekurangan berjumlah {k_hilang} lembar dari yang diserahkan disetorkan ke BAZNAS."
            pdf.multi_cell(0, 8, teks_isi); pdf.ln(5)
            pdf.multi_cell(0, 8, "Demikian berita acara ini dibuat tanpa ada paksaan dikedua pihak dan dapat digunakan sebagaimana mestinya."); pdf.ln(15)
            
            pdf.cell(100, 6, "Pihak Kedua,", 0, 0, "C"); pdf.cell(90, 6, "Pihak Pertama,", 0, 1, "C"); pdf.ln(20); pdf.set_font("Arial", "B", 12)
            pdf.cell(100, 6, f"( {ketua_dkm.upper()} )", 0, 0, "C"); pdf.cell(90, 6, f"( {ketua.upper()} )", 0, 1, "C")
            
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        timestamp = datetime.datetime.now().strftime("%H%M%S")
        st.download_button(label="📥 UNDUH BAST KUPON", data=pdf_bytes, file_name=f"BAST_Kupon_{desa}_{timestamp}.pdf", mime="application/pdf", use_container_width=True)