# AZ 500MB Data Collector

Azərbaycan dilində 500 MB təmiz mətn (`.txt`) yığmaq üçün kod. LLM / NLLB üçün.

## 👉 KODLAR: [KODLAR.md](KODLAR.md)

Hüceyrə-hüceyrə kod. Kaggle-da notebook aç, hər hüceyrəni sıra ilə kopyala-yapışdır.

Ayrı fayllar — [`hucreler/`](hucreler/):

| # | Fayl |
|---|---|
| 1 | [01_qurasdirma](hucreler/01_qurasdirma.md) — quraşdırma + parametrlər |
| 1B | [01b_token](hucreler/01b_token.md) — **HF token (yeni)** |
| 2 | [02_sekilciler](hucreler/02_sekilciler.md) — şəkilçi sözlər |
| 3 | [03_filtrler](hucreler/03_filtrler.md) — filtr funksiyaları |
| 4 | [04_menbeler](hucreler/04_menbeler.md) — **mənbələr (yeniləndi)** |
| 4B | [04b_yoxlama](hucreler/04b_yoxlama.md) — **mənbə yoxlaması (yeni)** |
| 5 | [05_yigma](hucreler/05_yigma.md) — yığım |

## ⚠️ Nə dəyişdi (v2)
Köhnə mənbələr işləmirdi:
- `oscar-corpus/OSCAR-2301`, `azcorpus` → **manual gated** (icazə tələb edir)
- `statmt/cc100`, `open_subtitles` → **Python skript** (yeni `datasets` qəbul etmir)
- `OpenSubtitles2024`, `eqanun`, `aze-books`, `CulturaX` → **auto gated** (token lazım)

İndi hamısı **açıq datasetlərlə** əvəz olundu.

## Mənbələr (v2)
| Kateqoriya | Mənbə | Gated? |
|---|---|---|
| Veb + Xəbər | `HuggingFaceFW/fineweb-2` (azj_Latn) | ❌ |
| | `LocalDoc/community_oscar_azerbaijani` | ❌ |
| | `LocalDoc/news_azerbaijan_2`, `news_azerbaijan` | ❌ |
| | `uonlp/CulturaX` (az) | ✅ token |
| Söhbət + Altyazı | `LocalDoc/smoltalk_az` | ❌ |
| | `Helsinki-NLP/opus-100` (az-en) | ❌ |
| | `Helsinki-NLP/OpenSubtitles2024` (az-en) | ✅ token |
| Ensiklopedik | `wikimedia/wikipedia` (20231101.az) | ❌ |
| Rəsmi / Hüquqi | `LocalDoc/azerbaijan_legislation` | ❌ |
| Bədii | `LocalDoc/books_dataset` (ID üzrə birləşdirilir) | ❌ |

## HF token (tövsiyə olunur)
1. https://huggingface.co/settings/tokens → **New token → Read**
2. Kaggle → **Add-ons → Secrets → New secret**: ad `HF_TOKEN`

## Nəticə
`/kaggle/working/az_data/`:
```
01_web_news.txt               175 MB
02_conversation_subtitle.txt  125 MB
03_encyclopedic_technical.txt 100 MB
04_official_legal.txt          50 MB
05_fiction.txt                 50 MB
az_all.txt               TAM 500 MB
```
`az_all.txt` = dəqiq 524 288 000 bayt.

## Filtr
- Dəqiq dublikat (hash), dil yoxlaması, keyfiyyət (Gopher/FineWeb)
- Uzunluq 200–20000 simvol, 70% qısa / 30% uzun
- **Məzmun sözü max 500** (şəkilçilər azad, limit keçsə bütün mətn atılır)
- `AUTO_RAISE_LIMIT = True` → limit doldurmağa çatmırsa avtomatik artır (1000, 2000, 5000...)

## Fayllar
- `KODLAR.md` — bütün hüceyrələr
- `hucreler/` — hər hüceyrə ayrı
- `kaggle_az_collector.py` — hamısı bir `.py` faylda
