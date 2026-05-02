import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from database import init_db, save_diagnosis, get_all_diagnoses, get_stats, get_last_n
from pdf_report import generate_pdf

# ─── Init DB ────────────────────────────────────────────────────────────────────
init_db()

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="MaintainAI — Predictive Maintenance", page_icon="⚙️", layout="wide", initial_sidebar_state="expanded")

# ─── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;800&display=swap');
:root { --bg:#0d0d0d; --surface:#161616; --border:#2a2a2a; --accent:#f5a623; --accent2:#e84545; --safe:#3de888; --text:#f0f0f0; --muted:#777; }
html, body, [class*="css"] { font-family:'Syne',sans-serif; background-color:var(--bg); color:var(--text); }
.stApp { background-color:var(--bg); }
[data-testid="stSidebar"] { background-color:var(--surface)!important; border-right:1px solid var(--border); }
.main-header { display:flex; align-items:center; gap:12px; padding:8px 0 24px 0; border-bottom:1px solid var(--border); margin-bottom:32px; }
.main-header h1 { font-size:2rem; font-weight:800; letter-spacing:-1px; margin:0; color:var(--accent); }
.main-header span { font-family:'Space Mono',monospace; font-size:0.75rem; color:var(--muted); display:block; margin-top:4px; }
.section-card { background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:24px; margin-bottom:20px; }
.section-title { font-size:0.7rem; font-family:'Space Mono',monospace; letter-spacing:3px; color:var(--accent); text-transform:uppercase; margin-bottom:16px; }
.result-box { background:#111; border:1px solid var(--accent); border-radius:12px; padding:28px; margin-top:24px; position:relative; overflow:hidden; }
.result-box::before { content:''; position:absolute; top:0;left:0;right:0; height:3px; background:linear-gradient(90deg,var(--accent),var(--accent2)); }
.severity-badge { display:inline-block; padding:4px 14px; border-radius:999px; font-family:'Space Mono',monospace; font-size:0.72rem; font-weight:700; letter-spacing:1px; text-transform:uppercase; margin-bottom:12px; }
.severity-HIGH { background:#3d1515; color:#e84545; border:1px solid #e84545; }
.severity-MEDIUM { background:#3d2b0a; color:#f5a623; border:1px solid #f5a623; }
.severity-LOW { background:#0f2d1a; color:#3de888; border:1px solid #3de888; }
.result-section-title { font-size:0.65rem; font-family:'Space Mono',monospace; letter-spacing:2px; color:var(--muted); text-transform:uppercase; margin:20px 0 8px 0; }
.result-content { font-size:0.95rem; line-height:1.7; color:#ddd; }
.timestamp { font-family:'Space Mono',monospace; font-size:0.68rem; color:var(--muted); margin-top:20px; padding-top:16px; border-top:1px solid var(--border); }
.history-item { background:var(--surface); border:1px solid var(--border); border-radius:8px; padding:12px 16px; margin-bottom:10px; transition:border-color 0.2s; }
.history-item:hover { border-color:var(--accent); }
.history-machine { font-weight:600; font-size:0.9rem; }
.history-time { font-family:'Space Mono',monospace; font-size:0.65rem; color:var(--muted); margin-top:2px; }
.stat-card { background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:20px; text-align:center; }
.stat-value { font-size:2rem; font-weight:800; color:var(--accent); }
.stat-label { font-family:'Space Mono',monospace; font-size:0.7rem; color:var(--muted); letter-spacing:1px; text-transform:uppercase; margin-top:4px; }
.stTextInput > div > div > input, .stTextArea > div > div > textarea { background-color:#111!important; border:1px solid var(--border)!important; color:var(--text)!important; border-radius:8px!important; }
.stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus { border-color:var(--accent)!important; box-shadow:0 0 0 2px rgba(245,166,35,0.15)!important; }
.stButton > button { background:var(--accent)!important; color:#000!important; font-family:'Space Mono',monospace!important; font-weight:700!important; font-size:0.85rem!important; letter-spacing:1px!important; border:none!important; border-radius:8px!important; padding:12px 28px!important; width:100%!important; transition:opacity 0.2s!important; }
.stButton > button:hover { opacity:0.85!important; }
label, .stSlider label { color:#bbb!important; font-size:0.85rem!important; }
.stSlider > div > div > div > div { background:var(--accent)!important; }
hr { border-color:var(--border)!important; }
.stTabs [data-baseweb="tab-list"] { gap:8px; border-bottom:1px solid var(--border); }
.stTabs [data-baseweb="tab"] { background:transparent; color:var(--muted); font-family:'Space Mono',monospace; font-size:0.8rem; letter-spacing:1px; border-radius:8px 8px 0 0; padding:10px 20px; }
.stTabs [aria-selected="true"] { background:var(--surface)!important; color:var(--accent)!important; border:1px solid var(--border); border-bottom:none; }
.stDownloadButton > button { background:transparent!important; color:var(--accent)!important; border:1px solid var(--accent)!important; font-family:'Space Mono',monospace!important; font-weight:700!important; font-size:0.8rem!important; }
.stDownloadButton > button:hover { background:var(--accent)!important; color:#000!important; }
</style>
""", unsafe_allow_html=True)

# ─── Session State ──────────────────────────────────────────────────────────────
if "api_configured" not in st.session_state:
    st.session_state.api_configured = False
if "last_result" not in st.session_state:
    st.session_state.last_result = None

# ─── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ MaintainAI")
    st.markdown("<hr>", unsafe_allow_html=True)

    api_key = st.text_input("Gemini API Key", type="password", placeholder="AIza...", help="Dapetin di aistudio.google.com")
    if api_key:
        try:
            genai.configure(api_key=api_key)
            st.session_state.api_configured = True
            st.success("✓ API terhubung")
        except Exception:
            st.error("API Key tidak valid")

    st.markdown("<hr>", unsafe_allow_html=True)
    stats = get_stats()
    st.markdown(f"**📊 Total Diagnosa:** {stats['total']}")
    st.markdown(f"**🔴 Kritis:** {stats['high']}")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("**Riwayat Terakhir**")
    last_items = get_last_n(5)
    if last_items:
        for item in last_items:
            icon = "🔴" if item["severity"] == "HIGH" else "🟡" if item["severity"] == "MEDIUM" else "🟢"
            st.markdown(f"""
            <div class='history-item'>
                <div class='history-machine'>{icon} {item['machine_name']}</div>
                <div class='history-time'>{item['timestamp']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("<span style='color:#555;font-size:0.8rem'>Belum ada riwayat</span>", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<span style='color:#444;font-size:0.7rem;font-family:monospace'>v2.0 · Polman Bandung</span>", unsafe_allow_html=True)

# ─── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class='main-header'>
    <div>
        <h1>⚙️ MaintainAI</h1>
        <span>PREDICTIVE MAINTENANCE DIAGNOSTIC SYSTEM</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Tabs ────────────────────────────────────────────────────────────────────────
tab_diagnosa, tab_history = st.tabs(["🔍 DIAGNOSA", "📊 HISTORY & ANALYTICS"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: DIAGNOSA
# ═══════════════════════════════════════════════════════════════════════════════
with tab_diagnosa:
    col1, col2 = st.columns([1.1, 0.9], gap="large")

    with col1:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>// Identitas Mesin</div>", unsafe_allow_html=True)
        machine_name = st.text_input("Nama / Kode Mesin", placeholder="contoh: CNC-01, Kompresor Line-A")
        machine_type = st.selectbox("Tipe Mesin", ["Pilih tipe mesin...", "Mesin CNC", "Kompresor", "Motor Listrik", "Conveyor", "Pompa Hidrolik", "Generator", "Robot Industri", "Mesin Bubut", "Lainnya"])
        machine_age = st.slider("Usia Mesin (tahun)", 0, 30, 5)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>// Gejala yang Diamati</div>", unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            suara = st.selectbox("🔊 Suara Abnormal", ["Tidak ada", "Dengungan", "Gesekan", "Ketukan", "Siulan", "Gemeretak"])
            getaran = st.selectbox("📳 Getaran", ["Normal", "Sedikit meningkat", "Meningkat", "Sangat tinggi"])
        with col_b:
            suhu = st.selectbox("🌡️ Suhu", ["Normal", "Hangat (30-50°C lebih)", "Panas (50-80°C lebih)", "Sangat panas (>80°C)"])
            performa = st.selectbox("📉 Performa", ["Normal", "Sedikit menurun", "Menurun signifikan", "Tidak berfungsi"])
        gejala_lain = st.text_area("Gejala / Observasi Tambahan", placeholder="Deskripsikan gejala lain yang terlihat, bau aneh, kebocoran, dll...", height=100)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>// Kondisi Operasional</div>", unsafe_allow_html=True)
        col_c, col_d = st.columns(2)
        with col_c:
            jam_operasi = st.number_input("Jam Operasi (per hari)", min_value=1, max_value=24, value=8)
        with col_d:
            last_maintenance = st.number_input("Terakhir Maintenance (bulan lalu)", min_value=0, max_value=60, value=6)
        beban = st.selectbox("Beban Kerja Saat Ini", ["Ringan (<50%)", "Normal (50-80%)", "Berat (80-100%)", "Overload (>100%)"])
        st.markdown("</div>", unsafe_allow_html=True)

        analyze_btn = st.button("🔍 ANALISIS SEKARANG")

    with col2:
        st.markdown("<div style='padding-top:8px'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>// Hasil Diagnosa AI</div>", unsafe_allow_html=True)
        result_placeholder = st.empty()
        pdf_placeholder = st.empty()

        if not st.session_state.api_configured:
            result_placeholder.markdown("""
            <div style='background:#161616;border:1px dashed #2a2a2a;border-radius:12px;padding:40px;text-align:center;color:#444'>
                <div style='font-size:2rem;margin-bottom:12px'>🔒</div>
                <div style='font-family:monospace;font-size:0.8rem'>Masukkan API Key di sidebar<br>untuk mulai diagnosa</div>
            </div>
            """, unsafe_allow_html=True)
        elif not analyze_btn:
            result_placeholder.markdown("""
            <div style='background:#161616;border:1px dashed #2a2a2a;border-radius:12px;padding:40px;text-align:center;color:#444'>
                <div style='font-size:2rem;margin-bottom:12px'>⚙️</div>
                <div style='font-family:monospace;font-size:0.8rem'>Isi form di sebelah kiri<br>lalu klik ANALISIS SEKARANG</div>
            </div>
            """, unsafe_allow_html=True)

        if analyze_btn:
            if not st.session_state.api_configured:
                st.error("⚠️ Masukkan API Key terlebih dahulu!")
            elif not machine_name:
                st.error("⚠️ Nama mesin wajib diisi!")
            elif machine_type == "Pilih tipe mesin...":
                st.error("⚠️ Pilih tipe mesin!")
            else:
                with st.spinner("AI sedang menganalisis..."):
                    prompt = f"""
Kamu adalah seorang ahli teknik mesin dan predictive maintenance di industri manufaktur dengan pengalaman 20 tahun.

Analisis kondisi mesin berikut dan berikan diagnosa profesional:

IDENTITAS MESIN:
- Nama/Kode: {machine_name}
- Tipe: {machine_type}
- Usia: {machine_age} tahun
- Jam operasi/hari: {jam_operasi} jam
- Terakhir maintenance: {last_maintenance} bulan yang lalu
- Beban kerja: {beban}

GEJALA YANG DIAMATI:
- Suara abnormal: {suara}
- Getaran: {getaran}
- Suhu: {suhu}
- Performa: {performa}
- Gejala tambahan: {gejala_lain if gejala_lain else "Tidak ada"}

Berikan analisis dalam format JSON berikut (HANYA JSON, tidak ada teks lain):
{{
    "severity": "HIGH/MEDIUM/LOW",
    "kemungkinan_kerusakan": "penjelasan 2-3 kalimat tentang kemungkinan penyebab kerusakan",
    "komponen_berisiko": ["komponen 1", "komponen 2", "komponen 3"],
    "rekomendasi_aksi": "langkah-langkah konkret yang harus dilakukan, berurutan",
    "estimasi_waktu": "estimasi waktu perbaikan",
    "prioritas": "apakah mesin harus dihentikan sekarang atau bisa lanjut beroperasi",
    "tips_pencegahan": "tips untuk mencegah kerusakan serupa di masa depan"
}}
"""
                    try:
                        model = genai.GenerativeModel("gemini-2.0-flash")
                        response = model.generate_content(prompt)
                        raw = response.text.strip()

                        if "```json" in raw:
                            raw = raw.split("```json")[1].split("```")[0].strip()
                        elif "```" in raw:
                            raw = raw.split("```")[1].split("```")[0].strip()

                        data = json.loads(raw)
                        severity = data.get("severity", "MEDIUM")
                        now = datetime.now().strftime("%d %b %Y, %H:%M")

                        # Save to database
                        save_diagnosis(machine_name, machine_type, machine_age, suara, getaran, suhu, performa, gejala_lain, jam_operasi, last_maintenance, beban, severity, data)

                        st.session_state.last_result = {
                            "machine_name": machine_name, "machine_type": machine_type,
                            "machine_age": machine_age, "suara": suara, "getaran": getaran,
                            "suhu": suhu, "performa": performa, "gejala_lain": gejala_lain,
                            "jam_operasi": jam_operasi, "last_maintenance": last_maintenance,
                            "beban": beban, "ai_result": data
                        }

                        sev_label = '🔴 KRITIS' if severity == 'HIGH' else '🟡 PERHATIAN' if severity == 'MEDIUM' else '🟢 AMAN'
                        result_placeholder.markdown(f"""
                        <div class='result-box'>
                            <div class='severity-badge severity-{severity}'>{sev_label} · {severity}</div>
                            <div style='font-size:1.4rem;font-weight:800;margin-bottom:4px'>{machine_name}</div>
                            <div style='font-family:monospace;font-size:0.72rem;color:#555'>{machine_type} · {machine_age} tahun</div>
                            <div class='result-section-title'>// Kemungkinan Kerusakan</div>
                            <div class='result-content'>{data.get('kemungkinan_kerusakan', '-')}</div>
                            <div class='result-section-title'>// Komponen Berisiko</div>
                            <div class='result-content'>{'  ·  '.join(data.get('komponen_berisiko', []))}</div>
                            <div class='result-section-title'>// Rekomendasi Aksi</div>
                            <div class='result-content'>{data.get('rekomendasi_aksi', '-')}</div>
                            <div class='result-section-title'>// Status Operasional</div>
                            <div class='result-content'>{data.get('prioritas', '-')}</div>
                            <div class='result-section-title'>// Estimasi Waktu Perbaikan</div>
                            <div class='result-content'>{data.get('estimasi_waktu', '-')}</div>
                            <div class='result-section-title'>// Tips Pencegahan</div>
                            <div class='result-content'>{data.get('tips_pencegahan', '-')}</div>
                            <div class='timestamp'>⏱ Dianalisis pada {now}</div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Generate PDF
                        pdf_buffer = generate_pdf(machine_name, machine_type, machine_age, suara, getaran, suhu, performa, gejala_lain, jam_operasi, last_maintenance, beban, data)
                        pdf_placeholder.download_button(
                            label="📄 Download Laporan PDF",
                            data=pdf_buffer,
                            file_name=f"MaintainAI_Report_{machine_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                            mime="application/pdf"
                        )

                    except json.JSONDecodeError:
                        result_placeholder.error("❌ Gagal parsing respons AI. Coba lagi.")
                    except Exception as e:
                        result_placeholder.error(f"❌ Error: {str(e)}")

        st.markdown("</div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: HISTORY & ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════
with tab_history:
    all_data = get_all_diagnoses()
    stats = get_stats()

    # Stats cards
    st.markdown("<div class='section-title'>// Statistik Keseluruhan</div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"<div class='stat-card'><div class='stat-value'>{stats['total']}</div><div class='stat-label'>Total Diagnosa</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='stat-card'><div class='stat-value' style='color:#e84545'>{stats['high']}</div><div class='stat-label'>🔴 High</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='stat-card'><div class='stat-value' style='color:#f5a623'>{stats['medium']}</div><div class='stat-label'>🟡 Medium</div></div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div class='stat-card'><div class='stat-value' style='color:#3de888'>{stats['low']}</div><div class='stat-label'>🟢 Low</div></div>", unsafe_allow_html=True)

    if all_data:
        df = pd.DataFrame(all_data)
        chart_col1, chart_col2 = st.columns(2)

        # Pie chart
        with chart_col1:
            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            st.markdown("<div class='section-title'>// Distribusi Severity</div>", unsafe_allow_html=True)
            sev_counts = df["severity"].value_counts().reset_index()
            sev_counts.columns = ["Severity", "Count"]
            color_map = {"HIGH": "#e84545", "MEDIUM": "#f5a623", "LOW": "#3de888"}
            fig_pie = px.pie(sev_counts, values="Count", names="Severity", color="Severity",
                             color_discrete_map=color_map, hole=0.45)
            fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                  font=dict(color="#ccc", family="Space Mono"), showlegend=True,
                                  margin=dict(t=20, b=20, l=20, r=20), height=300)
            fig_pie.update_traces(textinfo="percent+label", textfont_size=11)
            st.plotly_chart(fig_pie, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Bar chart by machine type
        with chart_col2:
            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            st.markdown("<div class='section-title'>// Diagnosa per Tipe Mesin</div>", unsafe_allow_html=True)
            type_sev = df.groupby(["machine_type", "severity"]).size().reset_index(name="count")
            fig_bar = px.bar(type_sev, x="machine_type", y="count", color="severity",
                             color_discrete_map=color_map, barmode="group",
                             labels={"machine_type": "Tipe Mesin", "count": "Jumlah", "severity": "Severity"})
            fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                  font=dict(color="#ccc", family="Space Mono"),
                                  xaxis=dict(gridcolor="#222"), yaxis=dict(gridcolor="#222"),
                                  margin=dict(t=20, b=20, l=20, r=20), height=300, legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig_bar, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Timeline chart
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>// Tren Severity dari Waktu ke Waktu</div>", unsafe_allow_html=True)
        df["timestamp_dt"] = pd.to_datetime(df["timestamp"])
        sev_map = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
        df["sev_num"] = df["severity"].map(sev_map)
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(x=df["timestamp_dt"], y=df["sev_num"], mode="lines+markers",
                                       line=dict(color="#f5a623", width=2), marker=dict(size=8, color=[color_map.get(s, "#f5a623") for s in df["severity"]]),
                                       hovertemplate="<b>%{text}</b><br>Severity: %{customdata}<br>%{x}<extra></extra>",
                                       text=df["machine_name"], customdata=df["severity"]))
        fig_line.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                               font=dict(color="#ccc", family="Space Mono"),
                               yaxis=dict(tickvals=[1, 2, 3], ticktext=["LOW", "MEDIUM", "HIGH"], gridcolor="#222"),
                               xaxis=dict(gridcolor="#222"), margin=dict(t=20, b=20, l=20, r=20), height=280, showlegend=False)
        st.plotly_chart(fig_line, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # History table
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>// Riwayat Lengkap</div>", unsafe_allow_html=True)
        table_df = df[["timestamp", "machine_name", "machine_type", "severity", "machine_age"]].copy()
        table_df.columns = ["Waktu", "Mesin", "Tipe", "Severity", "Usia (th)"]
        st.dataframe(table_df, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='background:#161616;border:1px dashed #2a2a2a;border-radius:12px;padding:60px;text-align:center;color:#444;margin-top:20px'>
            <div style='font-size:2.5rem;margin-bottom:12px'>📊</div>
            <div style='font-family:monospace;font-size:0.85rem'>Belum ada data diagnosa.<br>Lakukan diagnosa pertama di tab Diagnosa!</div>
        </div>
        """, unsafe_allow_html=True)
