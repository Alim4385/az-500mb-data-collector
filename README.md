# AZ 500MB Data Collector

Azərbaycan dilində 500 MB təmiz mətn (`.txt`) yığmaq üçün kod.
LLM / NLLB üçün keyfiyyətli, söz əhatəsi geniş data.

## 👉 KODLAR: [KODLAR.md](KODLAR.md)

Hüceyrə-hüceyrə kod. Kaggle-da notebook aç, hər hüceyrəni sıra ilə kopyala-yapışdır, işə sal.

Ayrı fayllar da var — [`hucreler/`](hucreler/) qovluğu:

1. [01_quraşdırma](hucreler/01_qurasdirma.md)
2. [02_parametrler](hucreler/02_parametrler.md)
3. [03_sekilciler](hucreler/03_sekilciler.md)
4. [04_filtrler](hucreler/04_filtrler.md)
5. [05_menbeler](hucreler/05_menbeler.md)
6. [06_yigma](hucreler/06_yigma.md)

## Kateqoriyalar (cəmi 500 MB)
| Fayl | MB |
|---|---|
| 01_web_news | 175 |
| 02_conversation_subtitle | 125 |
| 03_encyclopedic_technical | 100 |
| 04_official_legal | 50 |
| 05_fiction | 50 |

## Filtr (sərt, LLM standartı)
- Dəqiq dublikat silmə (hash)
- Uzunluq: 200–20000 simvol (qısa 200–1000, uzun 1000–20000)
- Dil yoxlaması (AZ hərfləri + stopword nisbəti)
- Keyfiyyət: hərf nisbəti, rəqəm, boilerplate, söz təkrarı, punktuasiya
- **Məzmun sözü max 500 dəfə** — şəkilçi/köməkçi sözlər azaddır, limit keçsə bütün mətn atılır
- Balans: 70% qısa / 30% uzun

## Kaggle
- Settings: **Internet = ON**, Accelerator = **GPU T4**
- Çıxış: `/kaggle/working/az_data/`
- Bitəndə **Save Version** → Output Dataset

## Mənbələr
| Kateqoriya | Dataset |
|---|---|
| Veb + Xəbər | `oscar-corpus/OSCAR-2301` (az), `statmt/cc100` (az), `azcorpus/azcorpus_v0` (az_news) |
| Söhbət + Altyazı | `Helsinki-NLP/OpenSubtitles2024` (az) |
| Ensiklopedik | `wikimedia/wikipedia` (20231101.az), `azcorpus/azcorpus_v0` (az_wiki) |
| Rəsmi / Hüquqi | `allmalab/eqanun` |
| Bədii | `allmalab/aze-books`, `azcorpus/azcorpus_v0` (az_books) |

## Fayllar
- `KODLAR.md` — bütün hüceyrələr bir yerdə
- `hucreler/` — hər hüceyrə ayrı fayl
- `kaggle_az_collector.py` — eyni kod tək `.py` fayl kimi (istəsən birbaşa yükləyib işə sal)
