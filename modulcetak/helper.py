import os
import sqlite3
from config import DB_NAME

def get_pengaturan():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT nama_desa, kepala_desa, nama_kecamatan, kabupaten, ketua_upz, sekretaris, logo_path, no_hp, total_jiwa, total_kk FROM pengaturan WHERE id=1")
    p = c.fetchone()
    conn.close()
    if p: return p
    return ("Desa", "Kades", "Kecamatan", "Kabupaten", "Ketua", "Sekretaris", "", "-", 0, 0)

def cetak_kop_surat_resmi(pdf, desa, kec, kab, logo_path="", is_landscape=False):
    page_width = 297 if is_landscape else 210
    margin_side = 10 
    pdf.set_y(10)
    if logo_path and os.path.exists(logo_path):
        try: pdf.image(logo_path, x=margin_side, y=10, w=22)
        except: pass
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 6, "BADAN AMIL ZAKAT NASIONAL (BAZNAS)", ln=True, align="C")
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 7, f"UNIT PENGUMPUL ZAKAT (UPZ) DESA {desa.upper()}", ln=True, align="C")
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 6, f"KECAMATAN {kec.upper()} - KABUPATEN {kab.upper()}", ln=True, align="C")
    pdf.ln(5)
    y_garis = max(pdf.get_y(), 34)
    line_width = page_width - (margin_side * 2)
    pdf.set_line_width(0.8)
    pdf.line(margin_side, y_garis, margin_side + line_width, y_garis)
    pdf.set_line_width(0.2)
    pdf.line(margin_side, y_garis + 1, margin_side + line_width, y_garis + 1)
    pdf.set_y(y_garis + 5)