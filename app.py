import matplotlib.pyplot as plt
import numpy as np
import streamlit as st


# --- 1. Fungsi Perhitungan Pajak Progresif PPh 21 (UU HPP) ---
def hitung_pajak_progresif(pkp):
    if pkp <= 0:
        return 0.0

    pajak = 0.0
    if pkp > 0:
        pajak += min(pkp, 60_000_000) * 0.05
    if pkp > 60_000_000:
        pajak += min(pkp - 60_000_000, 190_000_000) * 0.15
    if pkp > 250_000_000:
        pajak += min(pkp - 250_000_000, 250_000_000) * 0.25
    if pkp > 500_000_000:
        pajak += min(pkp - 500_000_000, 4_500_000_000) * 0.30
    if pkp > 5_000_000_000:
        pajak += (pkp - 5_000_000_000) * 0.35

    return pajak


# Vectorization agar eksekusi array NumPy sangat cepat
v_hitung_pajak = np.vectorize(hitung_pajak_progresif)

# --- 2. Konfigurasi Halaman Streamlit ---
st.set_page_config(
    page_title="Simulasi Monte Carlo Pajak", page_icon="📊", layout="wide"
)

st.title("📊 Simulasi Monte Carlo: Pajak Progresif (PPh 21)")
st.caption(
    "Aplikasi Web Berbasis Python (Streamlit) untuk Proyeksi Risiko Ketidakpastian Beban Pajak"
)

# --- 3. Sidebar Input Parameter ---
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

# --- 4. Proses Simulasi Monte Carlo ---
# Jalankan simulasi acak berdasarkan parameter
np.random.seed(42)  # Agar hasil konsisten
pkp_simulasi = np.maximum(0, np.random.normal(mean_pkp, std_dev_pkp, N))
pajak_simulasi = v_hitung_pajak(pkp_simulasi)

# Analisis Statistik
rata_pajak = np.mean(pajak_simulasi)
p50_pajak = np.percentile(pajak_simulasi, 50)
p90_pajak = np.percentile(pajak_simulasi, 90)
prob_30 = (np.sum(pkp_simulasi > 500_000_000) / N) * 100

# --- 5. Tampilan Dashboard ---
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

# --- 6. Visualisasi Grafik Histogram ---
st.subheader("Distribusi Frekuensi Estimasi Beban Pajak")

fig, ax = plt.subplots(figsize=(10, 4))
# Custom style untuk dark mode / clean look
fig.patch.set_facecolor("#0e1117")
ax.set_facecolor("#0e1117")

counts, bins, patches = ax.hist(
    pajak_simulasi / 1e6,
    bins=30,
    color="#38bdf8",
    edgecolor="#0284c7",
    alpha=0.8,
)

# Garis Indikator P90
ax.axvline(
    p90_pajak / 1e6,
    color="#f59e0b",
    linestyle="--",
    linewidth=2,
    label=f"Batas Aman P90 (Rp {p90_pajak/1e6:.1f} Juta)",
)

ax.set_xlabel("Beban Pajak (Juta Rupiah)", color="white")
ax.set_ylabel("Frekuensi Skenario", color="white")
ax.tick_params(colors="white")
ax.spines["bottom"].set_color("white")
ax.spines["top"].set_color("#334155")
ax.spines["right"].set_color("#334155")
ax.spines["left"].set_color("white")
ax.legend(facecolor="#1e293b", edgecolor="none", labelcolor="white")

st.pyplot(fig)
