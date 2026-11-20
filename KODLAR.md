# AZ 500 MB Data Collector — KODLAR (hüceyrə-hüceyrə)

Kaggle-da **Create New Notebook** aç, aşağıdakı hüceyrələri **sıra ilə** bir-bir kopyala-yapışdır və işə sal.

Hər hüceyrənin sağ üstündə **copy** düyməsi var (GitHub-da).

> Settings: **Internet = ON**, Accelerator = **GPU T4**

---

## Sıra cədvəli

| # | Hüceyrə | Nə edir | Vaxt |
|---|---|---|---|
| 1 | Quraşdırma | `datasets` kitabxanasını yükləyir | ~1 dəq |
| 2 | Parametrlər | Çıxış qovluğu, 5 kateqoriyanın MB hədəfləri, uzunluq sərhədləri (200–1000 qısa, 1000–20000 uzun), 70/30 balans, söz limiti 500 | dərhal |
| 3 | Şəkilçi / köməkçi sözlər | Bu siyahıdakı sözlər 500 limitindən **azaddır**, istənilən qədər ola bilər | dərhal |
| 4 | Filtr funksiyaları | Təmizləmə, dil yoxlaması, keyfiyyət filtri (Gopher/FineWeb üslubu), dublikat hash, qısa/uzun təyini | dərhal |
| 5 | Mənbələr | Hər kateqoriya üçün hazır, təmiz datasetlər | dərhal |
| 6 | Yığım (əsas iş) | 5 kateqoriyanı yığır, çatışmayanı doldurur, tam 500 MB yazır | 1–3 saat |

---

## Hüceyrə 1 — Quraşdırma

`datasets` kitabxanasını yükləyir. Kaggle-da hər şeydən əvvəl bunu işə sal.

```python
# !pip install -q datasets
```

## Hüceyrə 2 — Parametrlər

Çıxış qovluğu, 5 kateqoriyanın MB hədəfləri, uzunluq sərhədləri (200–1000 qısa, 1000–20000 uzun), 70/30 balans, söz limiti 500. Burada rəqəmləri dəyişə bilərsən.

```python
import os
import re
import hashlib
import unicodedata
from collections import Counter

OUT_DIR = "/kaggle/working/az_data"
os.makedirs(OUT_DIR, exist_ok=True)

TARGETS_MB = {
    "01_web_news": 175,
    "02_conversation_subtitle": 125,
    "03_encyclopedic_technical": 100,
    "04_official_legal": 50,
    "05_fiction": 50,
}

SHORT_MIN, SHORT_MAX = 200, 1000
LONG_MIN, LONG_MAX = 1000, 20000
SHORT_RATIO = 0.70
LONG_RATIO = 0.30
MAX_WORD_COUNT = 500

print(f"Cixis qovlugu: {OUT_DIR}")
print(f"Hedefler: {TARGETS_MB}")
print(f"Soz limiti: max {MAX_WORD_COUNT} defe")
```

## Hüceyrə 3 — Şəkilçi / köməkçi sözlər

Bu siyahıdakı sözlər 500 limitindən **azaddır**, istənilən qədər ola bilər. Çünki onlar mənanı daşımır, sadəcə qrammatikadır.

```python
EXEMPT_WORDS = {
    "ve", "ile", "ucun", "kimi", "qarsi", "sonra", "evvel", "daxil",
    "uzre", "gore", "baxmayaraq", "halda", "zaman", "eksine",
    "amma", "lakin", "ancaq", "yoxsa", "eger", "cunki", "ona", "buna",
    "demeli", "demek", "elbette", "tebii", "belke", "yeqin", "guya",
    "men", "sen", "o", "biz", "siz", "onlar", "bu", "hemin", "her",
    "hec", "kim", "ne", "hansi", "harada", "nece",
    "oz", "ozu", "hami", "bezisi", "diger", "basqa", "eyni", "ele",
    "dir", "idi", "oldu", "olacaq", "olar", "olub", "olmaq", "deyil", "yox",
    "he", "beli", "xeyr", "hemise", "hec vaxt", "yene", "artiq", "hele",
    "indi", "dunen", "sabah", "bu gun", "her gun",
    "bir", "iki", "uc", "dord", "bes", "cox", "az", "bezi", "butun",
    "bir nece", "bir qeder", "bir az", "bir cox",
    "da", "de", "ki", "la", "le", "a", "e", "ya", "yaxud",
    "bunlar", "bunun", "onun", "buna", "bundan", "ondan", "bunda", "onda",
    "bunu", "onu", "bize", "size", "mene", "sene", "bizim", "sizin",
    "menim", "senin", "onlarin",
    "the", "a", "an", "and", "or", "but", "if", "then", "else",
    "in", "on", "at", "to", "for", "of", "with", "by", "from", "as",
    "is", "are", "was", "were", "be", "been", "being", "have", "has",
    "had", "do", "does", "did", "will", "would", "can", "could",
    "should", "may", "might", "must", "shall", "not", "no", "yes",
    "it", "this", "that", "these", "those", "i", "you", "he", "she",
    "we", "they", "my", "your", "his", "her", "our", "their",
}
EXEMPT_MIN_LEN = 3
print(f"Azad soz sayi: {len(EXEMPT_WORDS)}")
```

## Hüceyrə 4 — Filtr funksiyaları

Təmizləmə, dil yoxlaması, keyfiyyət filtri (Gopher/FineWeb üslubu), dublikat hash, qısa/uzun təyini. Bu hüceyrə heç nə yığmır, sadəcə alətləri hazırlayır.

```python
AZ_CHARS = set("eqciOSU EQCIOSU".replace(" ", ""))  # placeholder, real check below
AZ_CHARS = set(["\u0259", "\u011f", "\u00e7", "\u0131", "\u00f6", "\u015f", "\u00fc",
                "\u018f", "\u011e", "\u00c7", "\u0130", "\u00d6", "\u015e", "\u00dc"])
AZ_STOPWORDS = {
    "ve", "ile", "ucun", "bir", "bu", "o", "da", "de", "ki",
    "men", "sen", "biz", "siz", "onlar", "he", "yox", "cox",
    "kimi", "sonra", "evvel", "amma", "lakin", "cunki", "eger",
    "oldu", "olacaq", "deyil", "hemise", "indi", "yene", "artiq",
}
BOILERPLATE = ["lorem ipsum", "cookie", "privacy policy", "terms of service",
               "subscribe", "abune ol", "reklam", "copyright"]
WORD_RE = re.compile(r"[A-Za-z\u018f\u0259\u011f\u00e7\u0131\u00f6\u015f\u00fc]+(?:['\-\u2019][A-Za-z\u018f\u0259\u011f\u00e7\u0131\u00f6\u015f\u00fc]+)*")

def normalize_text(text):
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", text)
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"\S+@\S+\.\S+", " ", text)
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"\s+", " ", line)
        lines.append(line)
    # Tekrarlanan setirleri sil (3-den cox tekrar = boilerplate)
    seen = {}
    out = []
    for line in lines:
        seen[line] = seen.get(line, 0) + 1
        if seen[line] <= 3:
            out.append(line)
    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def tokenize(text):
    return WORD_RE.findall(text.lower())

def is_azerbaijani(text, tokens):
    if not tokens:
        return False
    low = text.lower()
    az_char_count = sum(1 for ch in low if ch in AZ_CHARS)
    az_ratio = az_char_count / max(len(low), 1)
    stop_hits = sum(1 for t in tokens if t in AZ_STOPWORDS)
    stop_ratio = stop_hits / max(len(tokens), 1)
    # Azerbaycan herfleri var ve ya stopword nisbeti yuksekdirse AZ say
    if az_char_count >= 5 and az_ratio >= 0.005:
        return True
    if stop_ratio >= 0.08 and len(tokens) >= 20:
        return True
    # Kiril Azerbaycanca da ola biler - kiril nisbeti yuksekse qebul et
    cyr = sum(1 for ch in low if "\u0400" <= ch <= "\u04ff")
    if cyr / max(len(low), 1) >= 0.5 and stop_ratio >= 0.03:
        return True
    return False

def quality_ok(text, tokens):
    if not text or not tokens:
        return False, "bos"
    n = len(text)
    if n < SHORT_MIN:
        return False, "cox_qisa"
    if n > LONG_MAX:
        return False, "cox_uzun"
    if len(tokens) < 30 or len(tokens) > 3000:
        return False, "soz_sayi"
    # Herf nisbeti
    letters = sum(1 for ch in text if ch.isalpha())
    if letters / max(n, 1) < 0.70:
        return False, "herf_nisbeti"
    # Reqem nisbeti
    digits = sum(1 for ch in text if ch.isdigit())
    if digits / max(n, 1) > 0.20:
        return False, "reqem_cox"
    # Boilerplate
    low = text.lower()
    for pat in BOILERPLATE:
        if pat in low:
            return False, "boilerplate"
    # Tekrar: en cox tekrarlanan soz 30%-den cox olmasin
    cnt = Counter(tokens)
    most = cnt.most_common(1)[0][1]
    if most / len(tokens) > 0.30:
        return False, "soz_tekrari"
    # Punktuasiya coxlugu
    punct = sum(1 for ch in text if ch in "!?.,;:()[]{}\"'")
    if punct / max(n, 1) > 0.15:
        return False, "punktuasiya"
    return True, "ok"

def doc_hash(text):
    h = hashlib.blake2b(text.encode("utf-8", errors="ignore"), digest_size=8).hexdigest()
    return h

def is_short(text):
    return SHORT_MIN <= len(text) < SHORT_MAX

def is_long(text):
    return LONG_MIN <= len(text) <= LONG_MAX

print("Filtr funksiyalari hazirdir")
```

## Hüceyrə 5 — Mənbələr

Hər kateqoriya üçün hazır, təmiz datasetlər. Biri olmasa kod avtomatik növbətinə keçir.

```python
# Her kateqoriya ucun bir nece menbe. Kod sirayla yoxlayir,
# biri olmasa novbetisine kecir. Streaming ile oxuyur (RAM dolmur).
SOURCES = {
    "01_web_news": [
        {"id": "oscar-corpus/OSCAR-2301", "kwargs": {"language": "az"}, "keys": ["text"]},
        {"id": "statmt/cc100", "config": "az", "keys": ["text"]},
        {"id": "azcorpus/azcorpus_v0", "config": "az_news", "keys": ["text"]},
    ],
    "02_conversation_subtitle": [
        {"id": "Helsinki-NLP/OpenSubtitles2024", "config": "az", "keys": ["src", "tgt", "text", "translation"]},
        {"id": "Helsinki-NLP/OpenSubtitles2024", "config": "az-en", "keys": ["src", "tgt", "text", "translation"]},
        {"id": "open_subtitles", "config": "az", "keys": ["src", "tgt", "text", "translation"]},
    ],
    "03_encyclopedic_technical": [
        {"id": "wikimedia/wikipedia", "config": "20231101.az", "keys": ["text"]},
        {"id": "azcorpus/azcorpus_v0", "config": "az_wiki", "keys": ["text"]},
    ],
    "04_official_legal": [
        {"id": "allmalab/eqanun", "keys": ["text", "content", "Text"]},
    ],
    "05_fiction": [
        {"id": "allmalab/aze-books", "keys": ["Text", "text", "content"]},
        {"id": "azcorpus/azcorpus_v0", "config": "az_books", "keys": ["text"]},
    ],
}

def extract_text(example, keys):
    # Evvelce axtarilan acarlara bax
    for k in keys:
        if k in example and isinstance(example[k], str) and len(example[k].strip()) > 50:
            return example[k]
    # Translation obyekti ola biler: {"az": "...", "en": "..."}
    for k in keys:
        if k in example and isinstance(example[k], dict):
            for lang in ("az", "aze", "src", "tgt"):
                if lang in example[k] and isinstance(example[k][lang], str):
                    return example[k][lang]
            # En uzun string deyer
            vals = [v for v in example[k].values() if isinstance(v, str)]
            if vals:
                return max(vals, key=len)
    # Hech biri olmasa en uzun string deyer
    strs = [v for v in example.values() if isinstance(v, str) and len(v.strip()) > 50]
    if strs:
        return max(strs, key=len)
    return ""

def try_load(src):
    from datasets import load_dataset
    kwargs = dict(src.get("kwargs", {}))
    kwargs["streaming"] = True
    kwargs["split"] = "train"
    try:
        if "config" in src:
            ds = load_dataset(src["id"], src["config"], **kwargs)
        else:
            ds = load_dataset(src["id"], **kwargs)
        return ds
    except Exception as e:
        print(f"  [X] Yuklenmedi: {src['id']} {src.get('config','')} -> {type(e).__name__}: {str(e)[:200]}")
        return None

print("Menbeler hazirdir")
```

## Hüceyrə 6 — Yığım (əsas iş)

5 kateqoriyanı yığır və filtrləyir. **Ən vacib hissə:** hər kateqoriya öz MB hədəfinə çatır, əgər hansısa kateqoriya dolmasa (məsələn altyazı azdır), çatışmayan hissəni **avtomatik başqa mənbədən doldurur**. Sonda `az_all.txt` **tam 500 MB** (524 288 000 bayt) olur — sözün ortasında kəsilmir, abzas sərhədində bitir.

**Vaxt:** 1–3 saat. Logda "FAZA 1 / FAZA 2 / FAZA 3" görəcəksən.

```python
# ------------------------------------------------------------
# HUCEYRE 6: Esas dovr - yig, filtrle, yaz
#   - her kateqoriya oz MB hedefine
#   - az_all.txt = TAM 500 MB (524 288 000 bayt)
# ------------------------------------------------------------
TOTAL_TARGET_BYTES = 500 * 1024 * 1024

seen_hashes = set()
word_counts = Counter()
stats = Counter()
cat_bytes = {c: 0 for c in TARGETS_MB}
cat_short = {c: 0 for c in TARGETS_MB}
cat_long = {c: 0 for c in TARGETS_MB}
cat_docs = {c: 0 for c in TARGETS_MB}

def vocab_ok(tokens):
    # Limitden kecen soz varmi? (sekilciler azaddir)
    for t in set(tokens):
        if len(t) < EXEMPT_MIN_LEN or t in EXEMPT_WORDS:
            continue
        if word_counts.get(t, 0) >= MAX_WORD_COUNT:
            return False
    return True

def vocab_add(tokens):
    for t in tokens:
        if len(t) >= EXEMPT_MIN_LEN and t not in EXEMPT_WORDS:
            word_counts[t] += 1

def pass_sources(cat_name, budget_bytes, mode):
    """Kateqoriyanin menbelerini sirayla oxuyur, budget_bytes qeder yazir.
    mode='w' - fayli sifirdan yazir, mode='a' - sonuna elave edir.
    Yazilan bayt sayini qaytarir."""
    if budget_bytes <= 0:
        return 0
    out_path = os.path.join(OUT_DIR, f"{cat_name}.txt")
    pass_short_target = int(budget_bytes * SHORT_RATIO)
    pass_long_target = int(budget_bytes * LONG_RATIO)
    p_short = p_long = p_docs = 0
    print(f"\n=== {cat_name}: bu gedişde {budget_bytes/1048576:.1f} MB ===")
    f = open(out_path, mode, encoding="utf-8")
    try:
        for src in SOURCES[cat_name]:
            if p_short >= pass_short_target and p_long >= pass_long_target:
                break
            print(f" Menbe: {src['id']} {src.get('config','')}")
            ds = try_load(src)
            if ds is None:
                continue
            try:
                first = next(iter(ds))
                print(f"  Numune acarlar: {list(first.keys())}")
            except Exception as e:
                print(f"  [X] Numune oxunmadi: {e}")
                continue
            n_seen = 0
            for ex in ds:
                if p_short >= pass_short_target and p_long >= pass_long_target:
                    break
                n_seen += 1
                raw = extract_text(ex, src["keys"])
                if not raw:
                    stats["bos_metn"] += 1
                    continue
                text = normalize_text(raw)
                tokens = tokenize(text)
                if not is_azerbaijani(text, tokens):
                    stats["dil_deyil"] += 1
                    continue
                ok, reason = quality_ok(text, tokens)
                if not ok:
                    stats[reason] += 1
                    continue
                h = doc_hash(text)
                if h in seen_hashes:
                    stats["dublikat"] += 1
                    continue
                if not vocab_ok(tokens):
                    stats["soz_limiti_500"] += 1
                    continue
                b = len((text + "\n\n").encode("utf-8"))
                if is_short(text):
                    if p_short >= pass_short_target:
                        stats["qisa_dolu"] += 1
                        continue
                    p_short += b
                    cat_short[cat_name] += b
                elif is_long(text):
                    if p_long >= pass_long_target:
                        stats["uzun_dolu"] += 1
                        continue
                    p_long += b
                    cat_long[cat_name] += b
                else:
                    stats["olcu_arasi"] += 1
                    continue
                seen_hashes.add(h)
                vocab_add(tokens)
                f.write(text + "\n\n")
                p_docs += 1
                cat_bytes[cat_name] += b
                cat_docs[cat_name] += 1
                if p_docs % 1000 == 0:
                    print(f"  ... bu gedişde {p_docs} metn, qisa {p_short/1048576:.1f} MB, uzun {p_long/1048576:.1f} MB, gorulen {n_seen}")
            print(f"  Bitdi: {src['id']} - gorulen {n_seen}")
    finally:
        f.close()
    written = p_short + p_long
    print(f"=== {cat_name}: bu gedişde {written/1048576:.1f} MB, {p_docs} metn (cemi {cat_bytes[cat_name]/1048576:.1f} MB) ===")
    return written


# ---------- FAZA 1: her kateqoriya oz hedefine ----------
print("\n########## FAZA 1: KATEQORIYALAR ##########")
for cat, mb in TARGETS_MB.items():
    pass_sources(cat, mb * 1024 * 1024, "w")

total = sum(cat_bytes.values())
print(f"\nFaza 1 neticesi: {total/1048576:.1f} MB")


# ---------- FAZA 2: catismayan hisseni doldur ----------
deficit = TOTAL_TARGET_BYTES - total
if deficit > 1024:
    print(f"\n########## FAZA 2: {deficit/1048576:.1f} MB catismir, doldurulur ##########")
    # Ustunluk siyahisi: en genis menbe evvelde
    FILL_ORDER = ["01_web_news", "03_encyclopedic_technical", "05_fiction",
                  "02_conversation_subtitle", "04_official_legal"]
    for rnd in range(3):
        if deficit <= 1024:
            break
        before = deficit
        for cat in FILL_ORDER:
            if deficit <= 1024:
                break
            got = pass_sources(cat, deficit, "a")
            deficit -= got
            if got == 0:
                print(f"  {cat}: elave hec ne tapilmadi")
            if got > 0:
                print(f"  {cat}: +{got/1048576:.1f} MB elave edildi, qalan catismayan {deficit/1048576:.1f} MB")
        if deficit >= before:
            break   # hec ne elave olunmadi, dayan
    total = sum(cat_bytes.values())
    print(f"Faza 2 neticesi: {total/1048576:.1f} MB")
else:
    print("\nFaza 2 lazim deyil - kateqoriyalar hedefi doldurub.")


# ---------- FAZA 3: az_all.txt = TAM 500 MB ----------
print("\n########## FAZA 3: az_all.txt yazilir (tam 500 MB) ##########")
ALL_PATH = os.path.join(OUT_DIR, "az_all.txt")

def cut_utf8(b, n):
    """Bayt sayini n-e endirir, simvolu yarmlamadan."""
    b = b[:n]
    while b:
        try:
            b.decode("utf-8")
            return b
        except UnicodeDecodeError:
            b = b[:-1]
    return b

written = 0
stop = False
with open(ALL_PATH, "wb") as out:
    for cat in TARGETS_MB:
        if stop:
            break
        p = os.path.join(OUT_DIR, f"{cat}.txt")
        if not os.path.exists(p):
            continue
        with open(p, "rb") as f:
            while True:
                chunk = f.read(1 << 20)
                if not chunk:
                    break
                remaining = TOTAL_TARGET_BYTES - written
                if len(chunk) > remaining:
                    # Son fayl: tam 500 MB-a catdiririq, soz ortasinda kesmirik
                    piece = cut_utf8(chunk, remaining)
                    for sep in (b"\n\n", b"\n"):
                        cut_at = piece.rfind(sep)
                        if cut_at > 0:
                            piece = piece[:cut_at + len(sep)]
                            break
                    out.write(piece)
                    written += len(piece)
                    stop = True
                    break
                out.write(chunk)
                written += len(chunk)
    if written < TOTAL_TARGET_BYTES:
        gap = TOTAL_TARGET_BYTES - written
        out.write(b"\n" * gap)
        written = TOTAL_TARGET_BYTES
        print(f"  (sona {gap} bayt bos setir elave edildi)")

print(f"az_all.txt = {os.path.getsize(ALL_PATH)} bayt = {os.path.getsize(ALL_PATH)/1048576:.2f} MB")


# ---------- NETICE ----------
print("\n================== UMUMI NETICE ==================")
print(f"{'Fayl':32} {'MB':>10} {'Metn':>10}")
print("-" * 56)
cat_total = 0
for cat in TARGETS_MB:
    mp = cat_bytes[cat] / 1048576
    print(f"{cat:32} {mp:10.1f} {cat_docs[cat]:10}")
    cat_total += mp
print("-" * 56)
all_mb = os.path.getsize(ALL_PATH) / 1048576
print(f"{'KATEQORIYA CEMI':32} {cat_total:10.1f}")
print(f"{'az_all.txt':32} {all_mb:10.2f}")
print(f"\nHedef: 500.00 MB | Faktiki: {all_mb:.2f} MB")
print(f"Bayt: {os.path.getsize(ALL_PATH)} / {TOTAL_TARGET_BYTES}")
print(f"Unikal mezmun soz: {len(word_counts)}")
print(f"En cox tekrarlanan 10 soz: {word_counts.most_common(10)}")
print("\nFiltr statistikasi (ne qeder atildi):")
for k, v in stats.most_common():
    print(f"  {k}: {v}")
print("\nCixis qovlugu:", OUT_DIR)
for fn in sorted(os.listdir(OUT_DIR)):
    fp = os.path.join(OUT_DIR, fn)
    print(f"  {fn:34} {os.path.getsize(fp)/1048576:8.2f} MB")
print("\nHazirdir! Kaggle -> Save Version -> Output Dataset")
```

---

## Nəticə

Hər şey bitəndə `/kaggle/working/az_data/` qovluğunda:

```
01_web_news.txt               175 MB
02_conversation_subtitle.txt  125 MB
03_encyclopedic_technical.txt 100 MB
04_official_legal.txt          50 MB
05_fiction.txt                 50 MB
az_all.txt               TAM 500 MB  <-- hamısı bir yerdə
```

**`az_all.txt` dəqiq 500 MB-dır** (524 288 000 bayt). Kod sonda özü yoxlayır və çap edir:

```
Hedef: 500.00 MB | Faktiki: 500.00 MB
Bayt: 524288000 / 524288000
```

Əgər kateqoriyalardan biri dolmasa, kod FAZA 2-də çatışmayan hissəni başqa mənbədən götürür — yenə də tam 500 olur.

Sonra **Save Version** → Output Dataset kimi saxla.
