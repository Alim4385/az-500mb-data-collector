# AZ 500MB Data Collector

Azərbaycan dilində 500 MB təmiz mətn (`.txt`) yığmaq üçün kod. LLM / NLLB üçün.

## 👉 KODLAR: [KODLAR.md](KODLAR.md)

**7 hüceyrə, 1 → 7 sıra ilə.** Hər hüceyrə ayrı fayl kimi də var:

| # | Fayl | Vacib? | Vaxt |
|---|---|---|---|
| 1 | [01_qurasdirma](hucreler/01_qurasdirma.md) | MÜTLƏQ | 2–5 san |
| 2 | [02_hf_token](hucreler/02_hf_token.md) | istəyə bağlı | 2 san |
| 3 | [03_sekilciler](hucreler/03_sekilciler.md) | MÜTLƏQ | dərhal |
| 4 | [04_filtrler](hucreler/04_filtrler.md) | MÜTLƏQ | dərhal |
| 5 | [05_menbeler](hucreler/05_menbeler.md) | MÜTLƏQ | dərhal |
| 6 | [06_yoxlama](hucreler/06_yoxlama.md) | MÜTLƏQ | 30–60 san |
| 7 | [07_yigma](hucreler/07_yigma.md) | MÜTLƏQ | 1–3 saat |

## Kaggle
- Settings: **Internet = ON**, Accelerator = **GPU T4**
- Çıxış: `/kaggle/working/az_data/`

## Nəticə
```
01_web_news.txt               175 MB
02_conversation_subtitle.txt  125 MB
03_encyclopedic_technical.txt 100 MB
04_official_legal.txt          50 MB
05_fiction.txt                 50 MB
az_all.txt               TAM 500 MB
```
`az_all.txt` = dəqiq **524 288 000 bayt**.

## Mənbələr — hamısı AÇIQ (gated olmayan)
| Kateqoriya | Mənbə |
|---|---|
| Veb + Xəbər | `fineweb-2` (azj_Latn), `community_oscar_azerbaijani`, `news_azerbaijan_2`, `news_azerbaijan` |
| Söhbət + Altyazı | `smoltalk_az`, `opus-100` (az-en) |
| Ensiklopedik | `wikimedia/wikipedia` (20231101.az) |
| Rəsmi / Hüquqi | `azerbaijan_legislation` |
| Bədii | `books_dataset` (ID üzrə birləşdirilir) |
| + token varsa | `CulturaX`, `OpenSubtitles2024`, `eqanun`, `aze-books` |

## Filtr
- Dəqiq dublikat (hash), dil yoxlaması, keyfiyyət (Gopher/FineWeb)
- Uzunluq 200–20000 simvol, **70% qısa / 30% uzun**
- **Məzmun sözü max 500** — şəkilçi/köməkçi sözlər azad, limit keçsə bütün mətn atılır
- `AUTO_RAISE_LIMIT = True` → limit çatmırsa avtomatik artır (1000, 2000, 5000...)

## Fayllar
- `KODLAR.md` — bütün hüceyrələr bir yerdə
- `hucreler/` — hər hüceyrə ayrı fayl
- `kaggle_az_collector.py` — hamısı bir `.py` faylda
