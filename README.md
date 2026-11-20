# AZ 500MB Data Collector

Azərbaycan dilində 500 MB təmiz mətn (.txt) yığmaq üçün Kaggle notebook-u.
LLM / NLLB üçün keyfiyyətli, söz əhatəsi geniş data.

## Kateqoriyalar (hər biri 500 MB içində)
- Veb + Xəbər — 175 MB
- Söhbət + Altyazı — 125 MB
- Ensiklopedik + Texniki — 100 MB
- Rəsmi / Hüquqi — 50 MB
- Bədii — 50 MB

## Filtr (sərt, LLM standartı)
- Dəqiq dublikat silmə
- Uzunluq: 200–20000 simvol
- Dil + keyfiyyət yoxlaması (Gopher/FineWeb üslubu)
- Məzmun sözü max 500 dəfə (şəkilçilər azaddır, limit keçsə bütün mətn atılır)
- 70% qısa / 30% uzun balansı

## Kaggle-da işə salmaq
1. Kaggle → Create New Notebook → Upload → `kaggle_az_collector.ipynb`
2. Settings: Internet = ON, GPU T4
3. Run All
4. Çıxış: `/kaggle/working/az_data/` qovluğunda `.txt` fayllar

## Mənbələr
- OSCAR-2301 AZ, CC100 AZ, Wikipedia AZ, OpenSubtitles2024 AZ,
  allmalab/eqanun, allmalab/aze-books, azcorpus
