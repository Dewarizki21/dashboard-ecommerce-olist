# Proyek Analisis Data: E-Commerce Public Dataset

Proyek akhir kelas **Belajar Fundamental Analisis Data** (Dicoding).
Analisis memakai E-Commerce Public Dataset (Olist) dengan dua pertanyaan bisnis pada tahun 2017:

1. Di 5 negara bagian dengan pesanan terkirim terbanyak, berapa persentase pesanan yang terlambat, berapa rata-rata skor review-nya, dan negara bagian mana yang estimasi pengirimannya paling perlu dikoreksi?
2. Kategori produk apa saja yang menyumbang 80% pendapatan, dan bagaimana kontribusinya per kuartal?

Teknik analisis lanjutan: analisis geospasial (peta keterlambatan per negara bagian) dan binning (kelas A/B/C kategori produk).

## Struktur Proyek

```
submission
├── dashboard
│   ├── main_data.csv
│   └── dashboard.py
├── data
│   └── (9 berkas CSV E-Commerce Public Dataset)
├── notebook.ipynb
├── README.md
├── requirements.txt
└── url.txt
```

## Menjalankan Notebook

1. Pastikan seluruh berkas CSV dataset berada di folder `data/`.
2. Buka `notebook.ipynb` di Jupyter atau Google Colab, lalu jalankan semua sel.
3. Sel terakhir sebelum kesimpulan akan menulis ulang `dashboard/main_data.csv`.

## Menjalankan Dashboard Streamlit di Lokal

1. Pasang kebutuhan:
   ```
   pip install -r requirements.txt
   ```
2. Jalankan dashboard dari folder utama proyek:
   ```
   streamlit run dashboard/dashboard.py
   ```
3. Buka alamat yang ditampilkan di terminal (biasanya http://localhost:8501).

## Dashboard Online

Tautan dashboard di Streamlit Community Cloud tersimpan di `url.txt`.
