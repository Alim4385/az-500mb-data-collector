# AZ 500MB Data Collector (v3 — datatrove paralel)

Azərbaycan dilində 500 MB təmiz mətn (`.txt`) — LLM / NLLB üçün.

## 👉 KODLAR: [KODLAR.md](KODLAR.md) — 8 hüceyrə, 1 → 8 sıra

| # | Fayl | Vacib? | Vaxt |
|---|---|---|---|
| 1 | [01_qurasdirma](hucreler/01_qurasdirma.md) | MÜTLƏQ | 2–5 san |
| 2 | [02_hf_token](hucreler/02_hf_token.md) | istəyə bağlı | 2 san |
| 3 | [03_sekilciler](hucreler/03_sekilciler.md) | MÜTLƏQ | dərhal |
| 4 | [04_filtrler](hucreler/04_filtrler.md) | MÜTLƏQ | dərhal |
| 5 | [05_menbeler](hucreler/05_menbeler.md) | MÜTLƏQ | dərhal |
| 6 | [06_yoxlama](hucreler/06_yoxlama.md) | MÜTLƏQ | 30–60 san |
| 7 | [07_merhele_a](hucreler/07_merhele_a.md) | MÜTLƏQ | 8–15 dəq |
| 8 | [08_merhele_b](hucreler/08_merhele_b.md) | MÜTLƏQ | 5–10 dəq |

## 2 mərhələli arxitektura
```
MƏRHƏLƏ A (datatrove, 4 nüvə)  →  pool/*.jsonl.gz   (8-15 dəq)
MƏRHƏLƏ B (tək proses)         →  az_data/*.txt    (5-10 dəq)
```
Səbəb: qlobal söz limiti (3000) paralel proseslərdə paylaşıla bilmir → ağır iş paralel, sayım tək prosesdə.

**Ümumi vaxt: ~20-25 dəqiqə** (tək hüceyrə versiyası 1-2.5 saat idi).

## Ölçülmüş sürət
| Üsul | Sürət |
|---|---|
| Köhnə (sətir-sətir Python) | ~600 sənəd/san |
| datatrove 1 nüvə | 2 243 sənəd/san |
| datatrove 4 nüvə (Kaggle) | ~4 000–9 000 sənəd/san |

## Mənbələr — hamısı açıq (gated olmayan)
| Kateqoriya | Mənbə |
|---|---|
| Veb + Xəbər | `fineweb-2` (azj_Latn), `community_oscar_azerbaijani`, `news_azerbaijan_2`, `news_azerbaijan` |
| Söhbət + Altyazı | `smoltalk_az`, `opus-100` (az-en) |
| Ensiklopedik | `wikimedia/wikipedia`, `azerbaijani-pretrain-corpus` |
| Rəsmi / Hüquqi | `azerbaijan_legislation` |
| Bədii | `books_dataset` (ID üzrə birləşdirilir, Mərhələ B-də) |
| token varsa | +`CulturaX`, `OpenSubtitles2024`, `eqanun`, `aze-books` |

## Filtr
- Dəqiq dublikat (hash), dil yoxlaması, keyfiyyət (Gopher/FineWeb üslubu)
- Uzunluq 200–20000 simvol, **70% qısa / 30% uzun**
- **Məzmun sözü max 3000** — şəkilçi/köməkçi sözlər azaddır, limit keçsə bütün mətn atılır
- Qeyd: 500 limiti ilə 500 MB **mümkün deyil** (500 MB ≈ 80M söz → 160k fərqli söz forması lazım)

## Nəticə
```
01_web_news.txt               175 MB
02_conversation_subtitle.txt  125 MB
03_encyclopedic_technical.txt 100 MB
04_official_legal.txt          50 MB
05_fiction.txt                 50 MB
az_all.txt               TAM 500 MB   (524 288 000 bayt)
```
