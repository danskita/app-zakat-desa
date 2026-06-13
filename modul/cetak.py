import streamlit as st
import sqlite3
import datetime
from config import DB_NAME

# Import seluruh fungsi cetak
try:
    from modulcetak import cetak_d1, cetak_d2, cetak_d3, cetak_d4, cetak_d5, cetak_d6, cetak_kupon, cetak_bast_kec
except ImportError:
    pass

def render():
    st.title("🖨️ Pusat Cetak Dokumen (Modular)")
    
    desa_tugas = st.session_state.get("desa_tugas", "")
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT nama_desa FROM pengaturan WHERE id=1")
    p_desa = c.fetchone()
    conn.close()
    desa_default = desa_tugas if desa_tugas else (p_desa[0].capitalize() if p_desa and p_desa[0] else "Desa")

    with st.container(border=True):
        st.subheader("Atur Titimangsa Surat")
        col1, col2, col3 = st.columns(3)
        no_ba = col1.text_input("Nomor Surat:", f"......./BAST/DPH/III/{datetime.datetime.now().year}")
        hari_ba = col2.text_input("Hari:", "Senin")
        tgl_ba = col3.text_input("Tanggal:", "15 Ramadhan 1446")
        tempat_ba = st.text_input("Tempat TTD:", desa_default)

    st.markdown("---")
    
    kategori = st.selectbox("Pilih Dokumen yang Akan Dicetak:", [
        "Pilih Format...",
        "1. Cetak D1 (Surat Pengantar)",
        "2. Cetak D2 (Daftar Penerimaan)",
        "3. Cetak D3 (Rekapitulasi 100%)",
        "4. Cetak D4 (Asnaf Sabilillah)",
        "5. Cetak D5 (Rekap Alokasi Desa)",
        "6. Cetak D6 (Asnaf Amilin)",
        "7. Cetak BAST Kupon",
        "10. BAST Penyerahan 11% Kecamatan"
    ])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ---------------- ROUTING ----------------
    if kategori == "1. Cetak D1 (Surat Pengantar)": cetak_d1.render_ui(desa_default, no_ba, hari_ba, tgl_ba, tempat_ba)
    elif kategori == "2. Cetak D2 (Daftar Penerimaan)": cetak_d2.render_ui(desa_default, no_ba, hari_ba, tgl_ba, tempat_ba)
    elif kategori == "3. Cetak D3 (Rekapitulasi 100%)": cetak_d3.render_ui(desa_default, no_ba, hari_ba, tgl_ba, tempat_ba)
    elif kategori == "4. Cetak D4 (Asnaf Sabilillah)": cetak_d4.render_ui(desa_default, no_ba, hari_ba, tgl_ba, tempat_ba)
    elif kategori == "5. Cetak D5 (Rekap Alokasi Desa)": cetak_d5.render_ui(desa_default, no_ba, hari_ba, tgl_ba, tempat_ba)
    elif kategori == "6. Cetak D6 (Asnaf Amilin)": cetak_d6.render_ui(desa_default, no_ba, hari_ba, tgl_ba, tempat_ba)
    elif kategori == "7. Cetak BAST Kupon": cetak_kupon.render_ui(desa_default, no_ba, hari_ba, tgl_ba, tempat_ba)
    elif kategori == "10. BAST Penyerahan 11% Kecamatan": cetak_bast_kec.render_ui(desa_default, no_ba, hari_ba, tgl_ba, tempat_ba)