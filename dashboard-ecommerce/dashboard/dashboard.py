from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import pydeck as pdk
import seaborn as sns
import streamlit as st

# ---------------------------------------------------------------------------
# Pengaturan halaman dan warna
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Dashboard E-Commerce 2017", page_icon="📦", layout="wide")
sns.set_style("whitegrid")

WARNA_SOROT = "#D1495B"
WARNA_BIASA = "#9AA5B1"
WARNA_UTAMA = "#2E6F95"
NAMA_BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


# ---------------------------------------------------------------------------
# Memuat data
# ---------------------------------------------------------------------------
@st.cache_data
def muat_data():
    lokasi = Path(__file__).parent / "main_data.csv"
    df = pd.read_csv(lokasi, parse_dates=["order_purchase_timestamp"])
    df["bulan"] = df["order_purchase_timestamp"].dt.month
    df["kuartal"] = "Q" + df["order_purchase_timestamp"].dt.quarter.astype(str)
    return df


def ringkas_state(pesanan, n_top):
    """Ringkasan keterlambatan dan skor review untuk n_top negara bagian dengan pesanan terbanyak."""
    top = pesanan["customer_state"].value_counts().head(n_top).index
    data = pesanan[pesanan["customer_state"].isin(top)]
    ringkasan = data.groupby("customer_state").agg(
        jumlah_pesanan=("order_id", "nunique"),
        persen_terlambat=("terlambat", lambda x: x.mean() * 100),
        rata_durasi_hari=("durasi_kirim_hari", "mean"),
        rata_estimasi_hari=("estimasi_hari", "mean"),
        rata_skor_review=("review_score", "mean"),
    )
    ringkasan["buffer_estimasi_hari"] = ringkasan["rata_estimasi_hari"] - ringkasan["rata_durasi_hari"]
    ringkasan["median_hari_terlambat"] = data[data["terlambat"]].groupby("customer_state")["selisih_hari"].median()
    return ringkasan.sort_values("persen_terlambat", ascending=False).round(2)


def hitung_pareto(item):
    """Pendapatan per kategori beserta persentase dan persentase kumulatifnya."""
    pendapatan = (
        item.groupby("product_category_name_english")["price"].sum()
        .sort_values(ascending=False)
        .reset_index(name="pendapatan")
    )
    pendapatan["persen"] = pendapatan["pendapatan"] / pendapatan["pendapatan"].sum() * 100
    pendapatan["persen_kumulatif"] = pendapatan["persen"].cumsum()
    pendapatan["kumulatif_sebelumnya"] = pendapatan["persen_kumulatif"] - pendapatan["persen"]
    return pendapatan


df = muat_data()

# ---------------------------------------------------------------------------
# Sidebar: filter
# ---------------------------------------------------------------------------
st.sidebar.header("Filter")
bulan_awal, bulan_akhir = st.sidebar.select_slider(
    "Rentang bulan pembelian (2017)",
    options=NAMA_BULAN,
    value=(NAMA_BULAN[0], NAMA_BULAN[-1]),
)
idx_awal = NAMA_BULAN.index(bulan_awal) + 1
idx_akhir = NAMA_BULAN.index(bulan_akhir) + 1

data = df[(df["bulan"] >= idx_awal) & (df["bulan"] <= idx_akhir)]
if data.empty:
    st.warning("Tidak ada data pada rentang bulan yang dipilih.")
    st.stop()

pesanan = data.drop_duplicates("order_id")  # satu baris per pesanan
item = data.dropna(subset=["price"])  # satu baris per item terjual

st.sidebar.caption(
    "Data: E-Commerce Public Dataset (pesanan terkirim yang dibeli pada 2017). "
    "Pesanan dianggap terlambat jika tiba setelah tanggal estimasi."
)

# ---------------------------------------------------------------------------
# Judul dan ringkasan
# ---------------------------------------------------------------------------
st.title("📦 Dashboard Analisis E-Commerce 2017")
st.write("Menjawab dua pertanyaan bisnis: ketepatan pengiriman per negara bagian, dan kategori produk penyumbang pendapatan.")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Pesanan terkirim", f"{pesanan['order_id'].nunique():,}")
k2.metric("Pesanan terlambat", f"{pesanan['terlambat'].mean() * 100:.1f}%")
k3.metric("Rata-rata skor review", f"{pesanan['review_score'].mean():.2f}")
k4.metric("Total pendapatan", f"{item['price'].sum():,.0f}")

tab1, tab2, tab3, tab4 = st.tabs([
    "1. Pengiriman & Review",
    "2. Kategori Produk",
    "Peta Keterlambatan",
    "Kelas Kategori (A/B/C)",
])

# ---------------------------------------------------------------------------
# Tab 1: Pertanyaan 1
# ---------------------------------------------------------------------------
with tab1:
    st.subheader("Ketepatan pengiriman dan skor review per negara bagian")
    n_top = st.slider("Jumlah negara bagian teratas (berdasarkan jumlah pesanan)", 3, 10, 5)
    ringkasan = ringkas_state(pesanan, n_top)

    state_tertinggi = ringkasan["persen_terlambat"].idxmax()
    warna_state = [WARNA_SOROT if s == state_tertinggi else WARNA_BIASA for s in ringkasan.index]

    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))

    bars = axes[0].bar(ringkasan.index, ringkasan["persen_terlambat"], color=warna_state)
    axes[0].bar_label(bars, fmt="%.1f%%", padding=3)
    axes[0].set_title("Pesanan terlambat per negara bagian", fontsize=12, loc="left")
    axes[0].set_ylabel("% pesanan terkirim")
    axes[0].set_ylim(0, max(ringkasan["persen_terlambat"].max() * 1.2, 1))

    bars = axes[1].bar(ringkasan.index, ringkasan["rata_skor_review"], color=warna_state)
    axes[1].bar_label(bars, fmt="%.2f", padding=3)
    axes[1].set_title("Rata-rata skor review", fontsize=12, loc="left")
    axes[1].set_ylabel("Skor (1-5)")
    axes[1].set_ylim(0, 5)

    skor_ketepatan = (
        pesanan.groupby("terlambat")["review_score"].mean()
        .rename(index={False: "Tepat waktu", True: "Terlambat"})
    )
    warna_ketepatan = [WARNA_SOROT if k == "Terlambat" else WARNA_BIASA for k in skor_ketepatan.index]
    bars = axes[2].bar(skor_ketepatan.index, skor_ketepatan.values, color=warna_ketepatan)
    axes[2].bar_label(bars, fmt="%.2f", padding=3)
    axes[2].set_title("Skor review: tepat waktu vs terlambat", fontsize=12, loc="left")
    axes[2].set_ylim(0, 5)

    for ax in axes:
        ax.set_xlabel("")
        ax.grid(axis="x", visible=False)
        sns.despine(ax=ax)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    st.markdown(
        f"**Temuan:** {state_tertinggi} paling sering terlambat "
        f"({ringkasan.loc[state_tertinggi, 'persen_terlambat']:.1f}% pesanan) dengan cadangan waktu estimasi "
        f"{ringkasan.loc[state_tertinggi, 'buffer_estimasi_hari']:.1f} hari. Pesanan yang terlambat "
        "cenderung mendapat skor review jauh lebih rendah."
    )
    st.dataframe(ringkasan)

# ---------------------------------------------------------------------------
# Tab 2: Pertanyaan 2
# ---------------------------------------------------------------------------
with tab2:
    st.subheader("Kategori produk penyumbang pendapatan")
    if item.empty:
        st.info("Tidak ada penjualan pada rentang bulan ini.")
    else:
        batas = st.slider("Batas pendapatan kumulatif (%)", 50, 95, 80)
        pareto = hitung_pareto(item)
        kategori_batas = pareto[pareto["kumulatif_sebelumnya"] < batas]

        data_pareto = kategori_batas.sort_values("pendapatan")
        warna_kategori = [WARNA_BIASA if k == "unknown" else WARNA_UTAMA for k in data_pareto["product_category_name_english"]]

        fig, ax = plt.subplots(figsize=(11, max(4, 0.45 * len(data_pareto))))
        bars = ax.barh(data_pareto["product_category_name_english"], data_pareto["pendapatan"] / 1000, color=warna_kategori)
        ax.bar_label(
            bars,
            labels=[f"{p:.1f}% (kumulatif {k:.0f}%)" for p, k in zip(data_pareto["persen"], data_pareto["persen_kumulatif"])],
            padding=4, fontsize=9,
        )
        ax.set_xlim(0, (data_pareto["pendapatan"] / 1000).max() * 1.35)
        ax.set_xlabel("Pendapatan (ribu)")
        ax.set_ylabel("")
        ax.set_title(
            f"{len(kategori_batas)} dari {len(pareto)} kategori menyumbang {batas}% pendapatan",
            fontsize=13, loc="left",
        )
        ax.grid(axis="y", visible=False)
        sns.despine()
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        st.markdown("**Porsi tiap kategori utama dalam pendapatan per kuartal (%)**")
        pivot = (
            item[item["product_category_name_english"].isin(kategori_batas["product_category_name_english"])]
            .pivot_table(index="product_category_name_english", columns="kuartal", values="price", aggfunc="sum", fill_value=0)
            .reindex(kategori_batas["product_category_name_english"])
        )
        persen_kuartal = (pivot / pivot.sum() * 100).round(1)

        fig, ax = plt.subplots(figsize=(8, max(4, 0.45 * len(persen_kuartal))))
        sns.heatmap(
            persen_kuartal, annot=True, fmt=".1f", cmap="Blues", linewidths=0.5,
            cbar_kws={"label": "% dari pendapatan seluruh kategori utama pada kuartal itu"}, ax=ax,
        )
        ax.set_xlabel("Kuartal")
        ax.set_ylabel("")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

# ---------------------------------------------------------------------------
# Tab 3: Peta (analisis geospasial)
# ---------------------------------------------------------------------------
with tab3:
    st.subheader("Persentase pesanan terlambat per negara bagian")
    peta_df = (
        pesanan.groupby("customer_state")
        .agg(
            jumlah_pesanan=("order_id", "nunique"),
            persen_terlambat=("terlambat", lambda x: x.mean() * 100),
            rata_skor_review=("review_score", "mean"),
            state_lat=("state_lat", "first"),
            state_lng=("state_lng", "first"),
        )
        .reset_index()
    )
    peta_df["persen_terlambat"] = peta_df["persen_terlambat"].round(1)
    peta_df["rata_skor_review"] = peta_df["rata_skor_review"].round(2)
    peta_df["radius"] = 25000 + peta_df["jumlah_pesanan"] ** 0.5 * 1500

    def warna_titik(persen):
        if persen >= 10:
            return [209, 73, 91, 190]
        if persen >= 5:
            return [233, 162, 59, 190]
        return [46, 111, 149, 190]

    peta_df["warna"] = peta_df["persen_terlambat"].apply(warna_titik)

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=peta_df,
        get_position="[state_lng, state_lat]",
        get_radius="radius",
        get_fill_color="warna",
        pickable=True,
    )
    tampilan = pdk.ViewState(latitude=-14.2, longitude=-51.9, zoom=3.2)
    st.pydeck_chart(
        pdk.Deck(
            layers=[layer],
            initial_view_state=tampilan,
            tooltip={"text": "{customer_state}\n{persen_terlambat}% terlambat\n{jumlah_pesanan} pesanan\nSkor review {rata_skor_review}"},
        )
    )
    st.caption(
        "Merah: terlambat ≥ 10%, oranye: 5%-10%, biru: < 5%. Ukuran titik menunjukkan jumlah pesanan. "
        "Negara bagian dengan pesanan sedikit (misalnya di bawah 100) memiliki persentase yang kurang stabil."
    )
    st.dataframe(
        peta_df.drop(columns=["state_lat", "state_lng", "radius", "warna"])
        .sort_values("persen_terlambat", ascending=False)
        .reset_index(drop=True),
    )

# ---------------------------------------------------------------------------
# Tab 4: Binning kelas kategori
# ---------------------------------------------------------------------------
with tab4:
    st.subheader("Pengelompokan kategori berdasarkan kontribusi pendapatan")
    st.write(
        "Kategori dibagi menjadi tiga kelas menurut persentase pendapatan kumulatif: "
        "**A** (hingga 80%), **B** (80%-95%), dan **C** (sisa 5%)."
    )
    if item.empty:
        st.info("Tidak ada penjualan pada rentang bulan ini.")
    else:
        pareto = hitung_pareto(item)
        pareto["kelas"] = pd.cut(
            pareto["kumulatif_sebelumnya"],
            bins=[0, 80, 95, 100.0001],
            labels=["A (hingga 80%)", "B (80%-95%)", "C (sisa 5%)"],
            right=False,
        )
        ringkasan_kelas = pareto.groupby("kelas", observed=True).agg(
            jumlah_kategori=("product_category_name_english", "count"),
            total_pendapatan=("pendapatan", "sum"),
            persen_pendapatan=("persen", "sum"),
        ).round(2)

        kiri, kanan = st.columns(2)
        with kiri:
            st.dataframe(ringkasan_kelas)
        with kanan:
            fig, ax = plt.subplots(figsize=(6, 3.5))
            bars = ax.bar(
                [str(k).split(" ")[0] for k in ringkasan_kelas.index],
                ringkasan_kelas["persen_pendapatan"],
                color=[WARNA_UTAMA, WARNA_BIASA, WARNA_BIASA][: len(ringkasan_kelas)],
            )
            ax.bar_label(bars, fmt="%.1f%%", padding=3)
            ax.set_ylim(0, 100)
            ax.set_ylabel("% pendapatan")
            ax.set_title("Kontribusi pendapatan per kelas", fontsize=12, loc="left")
            ax.grid(axis="x", visible=False)
            sns.despine()
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

        kelas_dipilih = st.selectbox("Lihat daftar kategori pada kelas", ringkasan_kelas.index.astype(str).tolist())
        daftar = pareto[pareto["kelas"].astype(str) == kelas_dipilih][["product_category_name_english", "pendapatan", "persen"]]
        st.dataframe(daftar.round(2).reset_index(drop=True))
