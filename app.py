import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# ==========================================
# 1. FUNGSI PERHITUNGAN PAJAK PROGRESIF (PPh 21 - UU HPP)
# ==========================================
def hitung_pajak_progresif(pkp):
    if pkp <= 0:
        return 0.0

    pajak = 0.0
    # Lapisan 1: Rp 0 s.d. Rp 60 Juta (5%)
    if pkp > 0:
        pajak += min(pkp, 60_000_000) * 0.05

    # Lapisan 2: > Rp 60 Juta s.d. Rp 250 Juta (15%)
    if pkp > 60_000_000:
        pajak += min(pkp - 60_000_000, 190_000_000) * 0.15

    # Lapisan 3: > Rp 250 Juta s.d. Rp 500 Juta (25%)
    if pkp > 250_000_000:
        pajak += min(pkp - 250_000_000, 250_000_000) * 0.25

    # Lapisan 4: > Rp 500 Juta s.d. Rp 5 Miliar (30%)
    if pkp > 500_000_000:
        pajak += min(pkp - 500_000_000, 4_500_000_000) * 0.30

    # Lapisan 5: > Rp 5 Miliar (35%)
    if pkp > 5_000_000_000:
        pajak += (pkp - 5_000_000_000) * 0.35

    return pajak


# Vektorisasi agar perhitungan array NumPy super cepat
v_hitung_pajak = np.vectorize(hitung_pajak_progresif)


# ==========================================
# 2. KONFIGURASI HALAMAN STREAMLIT
# ==========================================
st.set_page_config(
    page_title="Simulasi Monte Carlo Pajak Progresif",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Simulasi Monte Carlo: Pajak Progresif (PPh 21)")
st.caption(
    "Dashboard Interaktif untuk Proyeksi Beban Pajak, Analisis CDF, dan Ekspor Data CSV"
)


# ==========================================
# 3. SIDEBAR PARAMETER INPUT
# ==========================================
st.sidebar.header("⚙️ Parameter Input")

mean_pkp = st.sidebar.number_input(
    "Rata-rata PKP Tahunan (Rp)",
    value=300_000_000,
    step=10_000_000,
    format="%d",
)

std_dev_pkp = st.sidebar.number_input(
    "Standar Deviasi / Fluktuasi (Rp)",
    value=75_000_000,
    step=5_000_000,
    format="%d",
)

N = st.sidebar.selectbox(
    "Jumlah Iterasi Simulasi (N)",
    options=[1_000, 10_000, 50_000, 100_000],
    index=1,
)


# ==========================================
# 4. PROSES SIMULASI MONTE CARLO
# ==========================================
np.random.seed(42)  # Menjaga hasil acak konsisten saat di-refresh
pkp_simulasi = np.maximum(0, np.random.normal(mean_pkp, std_dev_pkp, N))
pajak_simulasi = v_hitung_pajak(pkp_simulasi)

# Statistik Utama
rata_pajak = np.mean(pajak_simulasi)
p50_pajak = np.percentile(pajak_simulasi, 50)
p90_pajak = np.percentile(pajak_simulasi, 90)
prob_30 = (np.sum(pkp_simulasi > 500_000_000) / N) * 100


# ==========================================
# 5. METRIK RINGKASAN DASHBOARD
# ==========================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Rata-rata Pajak", f"Rp {rata_pajak:,.0f}")
with col2:
    st.metric("Pajak Median (P50)", f"Rp {p50_pajak:,.0f}")
with col3:
    st.metric("Cadangan Aman (P90)", f"Rp {p90_pajak:,.0f}")
with col4:
    st.metric("Probabilitas > 500M", f"{prob_30:.2f}%")

st.divider()


# ==========================================
# 6. FITUR EKSPOR & TABEL DATA PENUH
# ==========================================
st.subheader("📋 Data Hasil Simulasi Penuh")

# Membuat DataFrame dari seluruh iterasi simulasi
df_simulasi = pd.DataFrame({
    "Iterasi": np.arange(1, N + 1),
    "PKP_Simulasi_Rp": np.round(pkp_simulasi, 2),
    "Beban_Pajak_Rp": np.round(pajak_simulasi, 2),
    "Tarif_Efektif_Persen": np.round(
        (pajak_simulasi / np.maximum(1, pkp_simulasi)) * 100, 2
    ),
})


@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode("utf-8")


csv_data = convert_df_to_csv(df_simulasi)

# Tombol Download & Info Jumlah Baris Data
col_exp1, col_exp2 = st.columns([1, 2])

with col_exp1:
    st.download_button(
        label="📄 Unduh Data CSV Lengkap",
        data=csv_data,
        file_name=f"simulasi_monte_carlo_pajak_N{N}.csv",
        mime="text/csv",
        help="Klik untuk mengunduh seluruh data iterasi simulasi dalam format CSV",
    )

with col_exp2:
    st.info(f"💡 Menampilkan seluruh **{N:,} baris** data hasil iterasi.")

# TAMPILAN TABEL PENUH
# Catatan: Parameter height=400 memberikan scrollbar internal agar halaman utama tidak terlalu panjang.
st.dataframe(df_simulasi, use_container_width=True, height=400)

st.divider()


# ==========================================
# 7. GRAFIK PLOTLY INTERAKTIF (TAB HISTOGRAM & CDF)
# ==========================================
st.subheader("📈 Analisis Visual Hasil Simulasi")

tab1, tab2 = st.tabs(
    ["📊 Histogram Frekuensi", "📈 Kumulatif Probabilitas (CDF)"]
)

pajak_juta = pajak_simulasi / 1e6
p50_juta = p50_pajak / 1e6
p90_juta = p90_pajak / 1e6

# --- TAB 1: HISTOGRAM FREKUENSI ---
with tab1:
    fig_hist = go.Figure()

    fig_hist.add_trace(
        go.Histogram(
            x=pajak_juta,
            nbinsx=35,
            name="Frekuensi",
            marker_color="#38bdf8",
            opacity=0.85,
            hovertemplate="Beban Pajak: <b>Rp %{x:.1f} Juta</b><br>Frekuensi: <b>%{y} Skenario</b><extra></extra>",
        )
    )

    fig_hist.add_vline(
        x=p90_juta,
        line_dash="dash",
        line_color="#f59e0b",
        line_width=2.5,
        annotation_text=f"Batas Aman P90 (Rp {p90_juta:.1f} Juta)",
        annotation_position="top right",
        annotation_font_color="#f59e0b",
    )

    fig_hist.update_layout(
        xaxis_title="Beban Pajak (Juta Rupiah)",
        yaxis_title="Jumlah Skenario (Frekuensi)",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=30, b=20),
        hoverlabel=dict(
            bgcolor="#1e293b", font_size=13, font_family="sans-serif"
        ),
    )

    st.plotly_chart(fig_hist, use_container_width=True)

# --- TAB 2: GRAFIK CDF INTERAKTIF ---
with tab2:
    pajak_sorted = np.sort(pajak_simulasi) / 1e6
    cdf_persen = (np.arange(1, N + 1) / N) * 100

    fig_cdf = go.Figure()

    # Kurva Utama CDF
    fig_cdf.add_trace(
        go.Scatter(
            x=pajak_sorted,
            y=cdf_persen,
            mode="lines",
            name="CDF",
            line=dict(color="#38bdf8", width=3),
            hovertemplate="Beban Pajak: <b>Rp %{x:.2f} Juta</b><br>Probabilitas Kumulatif: <b>%{y:.2f}%%</b><extra></extra>",
        )
    )

    # Indikator P50 (Median)
    fig_cdf.add_hline(
        y=50,
        line_dash="dot",
        line_color="#10b981",
        line_width=1.5,
        annotation_text=f"P50 (Median): Rp {p50_juta:.1f} M",
        annotation_position="bottom right",
        annotation_font_color="#10b981",
    )
    fig_cdf.add_vline(
        x=p50_juta, line_dash="dot", line_color="#10b981", line_width=1.5
    )

    # Indikator P90 (Batas Aman)
    fig_cdf.add_hline(
        y=90,
        line_dash="dot",
        line_color="#f59e0b",
        line_width=1.5,
        annotation_text=f"P90 (Batas Aman): Rp {p90_juta:.1f} M",
        annotation_position="top left",
        annotation_font_color="#f59e0b",
    )
    fig_cdf.add_vline(
        x=p90_juta, line_dash="dot", line_color="#f59e0b", line_width=1.5
    )

    fig_cdf.update_layout(
        xaxis_title="Beban Pajak (Juta Rupiah)",
        yaxis_title="Probabilitas Kumulatif (%)",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=30, b=20),
        yaxis=dict(range=[0, 100]),
        hoverlabel=dict(
            bgcolor="#1e293b", font_size=13, font_family="sans-serif"
        ),
    )

    st.plotly_chart(fig_cdf, use_container_width=True)
