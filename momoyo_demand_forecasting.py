import math
import pandas as pd
import plotly.express as px
import streamlit as st

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Momoyo Demand Forecasting",
    page_icon="🍦",
    layout="wide",
)

# ============================================================
# TITLE & INTRODUCTION
# ============================================================
st.title("🍦 Momoyo Ice Cream & Tea")
st.subheader("Demand Forecasting Application")
st.markdown(
    """
Aplikasi ini membantu memperkirakan permintaan produk Momoyo menggunakan empat pendekatan:

1. **Simple Four-Week Moving Average**
2. **Weighted Moving Average**
3. **Exponential Smoothing**
4. **Updated Exponential Smoothing**

> **Catatan data:** angka awal di bawah adalah *data contoh untuk demonstrasi*, bukan data penjualan resmi Momoyo. Ganti angka di tabel dengan data dari soal studi kasus atau data toko yang kamu miliki.
""")

# ============================================================
# SIDEBAR - PARAMETERS
# ============================================================
st.sidebar.header("⚙️ Parameter Forecasting")
alpha = st.sidebar.slider(
    "Alpha (α)",
    min_value=0.01,
    max_value=1.00,
    value=0.10,
    step=0.01,
    help="Alpha menentukan seberapa besar forecast merespons perubahan permintaan aktual.",
)

st.sidebar.markdown("---")
st.sidebar.subheader("Bobot Weighted Moving Average")
w_oldest = st.sidebar.number_input("4 Minggu Lalu", min_value=0.0, max_value=1.0, value=0.10, step=0.05, format="%.2f")
w_3weeks = st.sidebar.number_input("3 Minggu Lalu", min_value=0.0, max_value=1.0, value=0.20, step=0.05, format="%.2f")
w_2weeks = st.sidebar.number_input("2 Minggu Lalu", min_value=0.0, max_value=1.0, value=0.30, step=0.05, format="%.2f")
w_last = st.sidebar.number_input("Minggu Terakhir", min_value=0.0, max_value=1.0, value=0.40, step=0.05, format="%.2f")
weight_total = w_oldest + w_3weeks + w_2weeks + w_last
if not math.isclose(weight_total, 1.0, abs_tol=0.0001):
    st.sidebar.error(f"Total bobot = {weight_total:.2f}. Total bobot harus sama dengan 1.00.")
else:
    st.sidebar.success("Total bobot = 1.00 ✓")

# ============================================================
# HISTORICAL DATA - ILLUSTRATIVE DEFAULT VALUES
# Edit these values in the table inside the application.
# Units are cups per day / production period.
# ============================================================
days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
historical_defaults = pd.DataFrame({
    "Periode": days,
    "4 Minggu Lalu": [5200, 5400, 5800, 5600, 6500, 9000, 8500],
    "3 Minggu Lalu": [5400, 5600, 5900, 5800, 6700, 9300, 8800],
    "2 Minggu Lalu": [5600, 5700, 6200, 5900, 7000, 9600, 9100],
    "Minggu Terakhir": [5800, 6000, 6300, 6100, 7300, 10000, 9500],
})

# ============================================================
# SECTION 1 - HISTORICAL DEMAND
# ============================================================
st.header("1. Data Permintaan Historis")
st.info(
    "Masukkan jumlah cup/gelas yang terjual pada setiap hari. Data bawaan hanyalah simulasi, bukan data resmi. "
    "Klik sel pada tabel untuk mengganti angka sesuai studi kasus Momoyo kamu."
)
edited_data = st.data_editor(
    historical_defaults,
    key="momoyo_historical_demand_editor",
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
    column_config={
        "Periode": st.column_config.TextColumn("Hari", disabled=True),
        "4 Minggu Lalu": st.column_config.NumberColumn("4 Minggu Lalu (cup)", min_value=0, step=100, format="%d"),
        "3 Minggu Lalu": st.column_config.NumberColumn("3 Minggu Lalu (cup)", min_value=0, step=100, format="%d"),
        "2 Minggu Lalu": st.column_config.NumberColumn("2 Minggu Lalu (cup)", min_value=0, step=100, format="%d"),
        "Minggu Terakhir": st.column_config.NumberColumn("Minggu Terakhir (cup)", min_value=0, step=100, format="%d"),
    },
)

df = edited_data.set_index("Periode").copy()
number_columns = ["4 Minggu Lalu", "3 Minggu Lalu", "2 Minggu Lalu", "Minggu Terakhir"]
for column in number_columns:
    df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0).clip(lower=0)

weekly_actual_last = float(df["Minggu Terakhir"].sum())
weekly_actual_two_weeks = float(df["2 Minggu Lalu"].sum())

# ============================================================
# SECTION 2 - SIMPLE FOUR-WEEK MOVING AVERAGE
# ============================================================
st.header("2. Part A — Simple Four-Week Moving Average")
st.markdown(
    r"""
**Rumus**

\[
F_t = \frac{D_{t-1}+D_{t-2}+D_{t-3}+D_{t-4}}{4}
\]

Setiap hari menggunakan rata-rata permintaan pada hari yang sama selama empat minggu sebelumnya.
"""
)
df["SMA Forecast"] = df[number_columns].mean(axis=1)
sma_result = df[["SMA Forecast"]].reset_index()
sma_result["SMA Forecast"] = sma_result["SMA Forecast"].round(0).astype(int)
st.dataframe(sma_result, use_container_width=True, hide_index=True, column_config={"SMA Forecast": st.column_config.NumberColumn("Forecast SMA (cup)", format="%d")})
with st.expander("🔎 Contoh perhitungan untuk hari Senin"):
    monday_vals = df.loc["Senin", number_columns].tolist()
    st.latex(
        rf"F_{{Senin}} = \frac{{{monday_vals[0]:,.0f}+{monday_vals[1]:,.0f}+{monday_vals[2]:,.0f}+{monday_vals[3]:,.0f}}}{{4}} = {df.loc['Senin', 'SMA Forecast']:,.0f}"
    )

# ============================================================
# SECTION 3 - WEIGHTED MOVING AVERAGE
# ============================================================
st.header("3. Part B — Weighted Moving Average")
st.markdown(
    r"""
**Rumus**

\[
F_t = w_1D_{t-4}+w_2D_{t-3}+w_3D_{t-2}+w_4D_{t-1}
\]

Bobot awal: 0,10 untuk empat minggu lalu, 0,20 untuk tiga minggu lalu, 0,30 untuk dua minggu lalu, dan 0,40 untuk minggu terakhir. Bobot dapat diubah melalui sidebar, tetapi totalnya harus 1,00.
"""
)
if math.isclose(weight_total, 1.0, abs_tol=0.0001):
    df["WMA Forecast"] = (
        w_oldest * df["4 Minggu Lalu"]
        + w_3weeks * df["3 Minggu Lalu"]
        + w_2weeks * df["2 Minggu Lalu"]
        + w_last * df["Minggu Terakhir"]
    )
else:
    df["WMA Forecast"] = float("nan")
    st.warning("Forecast WMA belum dihitung karena total bobot bukan 1,00. Sesuaikan bobot di sidebar.")

wma_result = df[["WMA Forecast"]].reset_index()
wma_result["WMA Forecast"] = wma_result["WMA Forecast"].round(0)
st.dataframe(wma_result, use_container_width=True, hide_index=True, column_config={"WMA Forecast": st.column_config.NumberColumn("Forecast WMA (cup)", format="%.0f")})
with st.expander("🔎 Contoh perhitungan untuk hari Senin"):
    monday_vals = df.loc["Senin", number_columns].tolist()
    st.latex(
        rf"F_{{Senin}}={w_oldest:.2f}({monday_vals[0]:,.0f})+{w_3weeks:.2f}({monday_vals[1]:,.0f})+{w_2weeks:.2f}({monday_vals[2]:,.0f})+{w_last:.2f}({monday_vals[3]:,.0f})={df.loc['Senin', 'WMA Forecast']:,.0f}"
    )

# ============================================================
# SECTION 4 - METHOD COMPARISON
# ============================================================
st.header("4. Perbandingan SMA vs Weighted MA")
comparison = df[["SMA Forecast", "WMA Forecast"]].reset_index().rename(columns={"Periode": "Hari"})
comparison_display = comparison.copy()
comparison_display["SMA Forecast"] = comparison_display["SMA Forecast"].round(0)
comparison_display["WMA Forecast"] = comparison_display["WMA Forecast"].round(0)
st.dataframe(comparison_display, use_container_width=True, hide_index=True)
chart_df = comparison.melt(id_vars="Hari", value_vars=["SMA Forecast", "WMA Forecast"], var_name="Metode", value_name="Forecast")
fig = px.bar(
    chart_df,
    x="Hari",
    y="Forecast",
    color="Metode",
    barmode="group",
    title="Perkiraan Permintaan Momoyo per Hari: SMA vs Weighted MA",
    labels={"Hari": "Hari", "Forecast": "Perkiraan Permintaan (cup)", "Metode": "Metode Forecasting"},
)
fig.update_layout(legend_title_text="Metode Forecasting")
st.plotly_chart(fig, use_container_width=True)

# ============================================================
# SECTION 5 - EXPONENTIAL SMOOTHING
# ============================================================
st.header("5. Part C — Exponential Smoothing")
st.markdown(
    r"""
Pada bagian ini, unit yang digunakan adalah **total cup dalam satu minggu**.

**Rumus**

\[
F_t = F_{t-1}+\alpha(A_{t-1}-F_{t-1})
\]
"""
)
col1, col2, col3 = st.columns(3)
with col1:
    previous_forecast = st.number_input(
        "Forecast total minggu lalu (cup)", min_value=0.0, value=float(round(weekly_actual_two_weeks / 100.0) * 100), step=100.0,
        help="Nilai awal diisi dari total permintaan dua minggu lalu sebagai titik awal demonstrasi. Ganti jika soal menyediakan forecast minggu lalu."
    )
with col2:
    actual_last_week_input = st.number_input(
        "Aktual total minggu terakhir (cup)", min_value=0.0, value=weekly_actual_last, step=100.0,
        help="Nilai awal mengikuti total kolom Minggu Terakhir pada tabel historis."
    )
with col3:
    st.metric("Alpha (α)", f"{alpha:.2f}")

forecast_this_week = previous_forecast + alpha * (actual_last_week_input - previous_forecast)
st.success(f"Forecast total minggu ini = **{forecast_this_week:,.0f} cup**")
with st.expander("🔎 Lihat perhitungan Part C"):
    st.latex(rf"F_t={previous_forecast:,.0f}+{alpha:.2f}({actual_last_week_input:,.0f}-{previous_forecast:,.0f})={forecast_this_week:,.0f}")

# ============================================================
# SECTION 6 - UPDATED EXPONENTIAL SMOOTHING
# ============================================================
st.header("6. Part D — Forecast Minggu Berikutnya")
st.markdown(
    r"""
Masukkan total permintaan aktual minggu ini untuk memperbarui forecast minggu depan.

\[
F_{t+1}=F_t+\alpha(A_t-F_t)
\]
"""
)
actual_this_week = st.number_input("Aktual total minggu ini (cup)", min_value=0.0, value=float(round(weekly_actual_last * 1.02 / 100.0) * 100), step=100.0)
forecast_next_week = forecast_this_week + alpha * (actual_this_week - forecast_this_week)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Forecast minggu ini", f"{forecast_this_week:,.0f} cup")
with col2:
    st.metric("Aktual minggu ini", f"{actual_this_week:,.0f} cup")
with col3:
    st.metric("Forecast minggu depan", f"{forecast_next_week:,.0f} cup")
with st.expander("🔎 Lihat perhitungan Part D"):
    st.latex(rf"F_{{t+1}}={forecast_this_week:,.0f}+{alpha:.2f}({actual_this_week:,.0f}-{forecast_this_week:,.0f})={forecast_next_week:,.0f}")

# ============================================================
# SECTION 7 - SUMMARY
# ============================================================
st.header("7. Ringkasan Hasil")
summary = pd.DataFrame({
    "Bagian": ["A", "B", "C", "D"],
    "Metode": [
        "Simple Four-Week Moving Average",
        "Weighted Moving Average",
        "Exponential Smoothing",
        "Updated Exponential Smoothing",
    ],
    "Hasil": [
        "Forecast per hari ditampilkan pada tabel Part A",
        "Forecast per hari ditampilkan pada tabel Part B" if math.isclose(weight_total, 1.0, abs_tol=0.0001) else "Belum dihitung: total bobot harus 1,00",
        f"{forecast_this_week:,.0f} cup per minggu",
        f"{forecast_next_week:,.0f} cup per minggu",
    ],
})
st.dataframe(summary, use_container_width=True, hide_index=True)

# ============================================================
# SECTION 8 - INTERPRETATION
# ============================================================
st.header("8. Poin Pembelajaran")
st.markdown(
    """
**Simple Moving Average (SMA)**  
Semua data dari empat minggu sebelumnya memiliki bobot yang sama. Metode ini mudah dihitung dan dipahami.

**Weighted Moving Average (WMA)**  
Data terbaru bisa diberi bobot lebih tinggi. Pastikan seluruh bobot berjumlah 1,00 agar hasil perhitungan valid.

**Exponential Smoothing**  
Forecast diperbarui menggunakan forecast sebelumnya dan permintaan aktual. Alpha yang tinggi membuat forecast lebih responsif terhadap perubahan aktual.

**Pemanfaatan untuk Momoyo**  
Hasil forecast dapat menjadi masukan awal untuk perencanaan stok bahan baku, cup dan kemasan, serta penjadwalan tenaga kerja. Pertimbangkan juga promosi, cuaca, lokasi gerai, hari libur, dan tren produk sebelum membuat keputusan operasional.

**Penting:** hasil aplikasi mengikuti angka yang dimasukkan. Untuk tugas akademik, ganti semua angka contoh dengan data pada soal studi kasus Momoyo apabila tersedia.
"""
)
st.caption("Momoyo Demand Forecasting Application | Streamlit + Pandas + Plotly | Data contoh dapat diedit")
