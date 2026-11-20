# AZ 500 MB Data Collector — KODLAR (hüceyrə-hüceyrə)

Kaggle-da hüceyrələri **sıra ilə** kopyala-yapışdır və işə sal.

> Settings: **Internet = ON**, Accelerator = **GPU T4**

## Nə dəyişdi?

Köhnə versiyada OSCAR, cc100, azcorpus, OpenSubtitles işləmirdi (gated + skript qadağası). Hamısı **açıq datasetlərlə** əvəz olundu.

| # | Hüceyrə | Vəziyyət |
|---|---|---|
| 1 | Quraşdırma + parametrlər | **DÜZƏLDİLDİ** (pip sətri silindi) |
| 1B | HF token | **YENİ** |
| 2 | Şəkilçi sözlər | dəyişməyib |
| 3 | Filtr funksiyaları | dəyişməyib |
| 4 | Mənbələr | **YENİLƏNDİ** |
| 4B | Mənbə yoxlaması | **YENİ** |
| 5 | Yığım | **YENİLƏNDİ** |

---

## Hüceyrə 1 — Quraşdırma + parametrlər (DÜZƏLDİLDİ)

**Vacib:** `!pip install -U datasets` sətri **silahdan çıxarıldı** — Kaggle-da `datasets` artıq qurulub, yeniləmə pip-in asılılıq həllini uzadıb 10+ dəqiqə ilişib qalırdı. İndi yoxlayıb keçir.

```python
import os
import re
import sys
import hashlib
import unicodedata
from collections import Counter

# ------------------------------------------------------------
# DIQQET: "!pip install -U datasets" LAZIM DEYIL!
# Kaggle-da datasets artiq qurulub. Yenileme pip-in asililiq
# hellini uzadir ve 10+ deqiqe cekir. Ona gore yoxlayib kecirik.
# ------------------------------------------------------------
import datasets
print("datasets:", datasets.__version__)

try:
    import huggingface_hub
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "huggingface_hub"], check=False)
    import huggingface_hub
print("huggingface_hub:", huggingface_hub.__version__)

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
print("HUCeyre 1 HAZIRDIR - novbeti hucreye kec")
```

## Hüceyrə 1B — HF token (YENİ)

**Vacibdir.** Gated datasetlər üçün token. Token olmasa da kod işləyir — sadəcə 4 mənbə atlanır.

Token: [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) → New token (Read) → kopyala → Kaggle-da **Add-ons → Secrets → New secret**, ad: `HF_TOKEN`.

```python
# ------------------------------------------------------------
# HUCEYRE 1B (YENI): HF TOKEN
# Gated datasetler ucun lazimdir (CulturaX, OpenSubtitles2024,
# eqanun, aze-books). Token olmasa da qalan menbeler isleyir.
# ------------------------------------------------------------
import os
HF_TOKEN = None
try:
    from kaggle_secrets import UserSecretsClient
    HF_TOKEN = UserSecretsClient().get_secret("HF_TOKEN")
except Exception:
    pass
if not HF_TOKEN:
    HF_TOKEN = os.environ.get("HF_TOKEN")

if HF_TOKEN:
    from huggingface_hub import login
    login(token=HF_TOKEN, add_to_git_credential=False)
    print("[OK] HF token qebul edildi - gated datasetler de isleyecek")
else:
    print("[!] HF token yoxdur - gated datasetler atlanacaq, qalanlari isleyecek")
    print("    Kaggle -> Add-ons -> Secrets -> New secret, ad: HF_TOKEN")
```

## Hüceyrə 2 — Şəkilçi / köməkçi sözlər

Bu siyahıdakı sözlər 500 limitindən **azaddır**. **Dəyişməyib.**

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

## Hüceyrə 3 — Filtr funksiyaları

Təmizləmə, dil yoxlaması, keyfiyyət, dublikat, qısa/uzun təyini. **Dəyişməyib.**

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

## Hüceyrə 4 — Mənbələr (YENİLƏNDİ)

**Bütün mənbələr dəyişdi.** OSCAR/cc100 gated + skriptli idi, işləmirdi. İndi hamısı açıq datasetlərdir:

| Kateqoriya | Mənbə |
|---|---|
| Veb+Xəbər | `fineweb-2` (azj_Latn), `community_oscar_azerbaijani`, `news_azerbaijan_2`, `news_azerbaijan` |
| Söhbət | `smoltalk_az`, `opus-100` (az-en) |
| Ensiklopedik | `wikimedia/wikipedia` (20231101.az) |
| Rəsmi | `azerbaijan_legislation` |
| Bədii | `books_dataset` (ID üzrə birləşdirilir) |

```python
# ------------------------------------------------------------
# MENBELER - hamisi ACIQ (gated olmayan) datasetler
# Sira ile yoxlanir: biri islemese novbetisine kecir.
# ------------------------------------------------------------
SOURCES = {
    # ---- VEB + XEBER ----
    "01_web_news": [
        {"id": "HuggingFaceFW/fineweb-2", "config": "azj_Latn", "field": "text"},
        {"id": "LocalDoc/community_oscar_azerbaijani", "field": "content"},
        {"id": "LocalDoc/news_azerbaijan_2", "field": "text"},
        {"id": "LocalDoc/news_azerbaijan", "field": "text"},
        {"id": "uonlp/CulturaX", "config": "az", "field": "text"},          # gated (token varsa)
    ],
    # ---- SOHBET + ALTYAZI ----
    "02_conversation_subtitle": [
        {"id": "LocalDoc/smoltalk_az", "field": "messages_az"},
        {"id": "Helsinki-NLP/opus-100", "config": "az-en", "field": ["translation", "az", "src", "text"]},
        {"id": "Helsinki-NLP/OpenSubtitles2024", "config": "az-en",
         "field": ["translation", "az", "text"]},                            # gated (token varsa)
    ],
    # ---- ENSIKLOPEDIK + TEXNIKI ----
    "03_encyclopedic_technical": [
        {"id": "wikimedia/wikipedia", "config": "20231101.az", "field": "text"},
        {"id": "LocalDoc/azerbaijani-pretrain-corpus", "field": "text"},
    ],
    # ---- RESMI / HUQUQI ----
    "04_official_legal": [
        {"id": "LocalDoc/azerbaijan_legislation", "field": "text"},
        {"id": "allmalab/eqanun", "field": ["text", "content", "article"]},  # gated (token varsa)
    ],
    # ---- BEDII ----
    "05_fiction": [
        # Kitablar setir-setir gelir -> ID uzre birlesdirib abzaslara boluruq
        {"id": "LocalDoc/books_dataset", "join_by": "ID", "join_field": " Sentence"},
        {"id": "allmalab/aze-books", "field": ["Text", "text", "content"]},  # gated (token varsa)
    ],
}

def try_load(src):
    """Dataseti streaming rejiminde acir. Alinmasa None qaytarir (kod novbeti menbeye kecir)."""
    from datasets import load_dataset
    kw = {"streaming": True, "split": "train"}
    name = src["id"] + (f" [{src['config']}]" if src.get("config") else "")
    try:
        if src.get("config"):
            return load_dataset(src["id"], src["config"], **kw)
        return load_dataset(src["id"], **kw)
    except Exception as e:
        print(f"  [X] {name}: {type(e).__name__}: {str(e)[:140]}")
        return None

print("Menbe sayi:", sum(len(v) for v in SOURCES.values()))
for cat, srcs in SOURCES.items():
    print(f"  {cat}: {len(srcs)} menbe")
```

## Hüceyrə 4B — Mənbə yoxlaması (YENİ)

30 saniyəlik yoxlama — hansı mənbənin işlədiyini göstərir. Uzun yığımdan **əvvəl** işə sal.

```python
# ------------------------------------------------------------
# MENBE YOXLAMASI - her menbeden 1 numune oxuyur
# Ishlemezden evvel bunu ise salin (30 saniye)
# ------------------------------------------------------------
from datasets import load_dataset

print("MENBE YOXLAMASI\n" + "=" * 62)
isleyen, islemeyen = [], []

for cat, srcs in SOURCES.items():
    print(f"\n--- {cat} ---")
    for src in srcs:
        name = src["id"] + (f" [{src['config']}]" if src.get("config") else "")
        try:
            kw = {"streaming": True, "split": "train"}
            if src.get("config"):
                ds = load_dataset(src["id"], src["config"], **kw)
            else:
                ds = load_dataset(src["id"], **kw)
            ex = next(iter(ds))
            fields = [k for k in ex.keys()][:8]
            print(f"  [OK] {name}")
            print(f"       saheler: {fields}")
            isleyen.append(name)
        except Exception as e:
            msg = str(e).replace("\n", " ")[:120]
            print(f"  [X ] {name}")
            print(f"       {type(e).__name__}: {msg}")
            islemeyen.append(name)

print("\n" + "=" * 62)
print(f"ISLEYEN: {len(isleyen)} | ISLEMEYEN: {len(islemeyen)}")
if islemeyen:
    print("\nIslemeyenler:")
    for n in islemeyen:
        print("  -", n)
print("\nQeyd: 'gated' xetasi = HF token lazimdir (yuxaridaki kimi).")
print("Diger xetalar olsa, hemin menbe sadece atlanacaq, qalanlar isleyecek.")
```

## Hüceyrə 5 — Yığım (ƏSAS İŞ) — YENİLƏNDİ

3 faza: kateqoriyalar → çatışmayanı doldur → tam 500 MB `az_all.txt`. Kitablar ID üzrə birləşdirilib abzaslara bölünür (70% qısa / 30% uzun).

```python
# ------------------------------------------------------------
# HUCEYRE 6: Esas dovr - yig, filtrle, yaz
#   FAZA 1: her kateqoriya oz MB hedefine
#   FAZA 2: catismayan hisseni basqa menbeden doldur
#   FAZA 3: az_all.txt = TAM 500 MB
# ------------------------------------------------------------
TOTAL_TARGET_BYTES = 500 * 1024 * 1024   # tam 500 MB

seen_hashes = set()
word_counts = Counter()
stats = Counter()
cat_bytes = {c: 0 for c in TARGETS_MB}
cat_docs = {c: 0 for c in TARGETS_MB}

def vocab_ok(tokens):
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

# ---------- saheden metn cixarma ----------
def to_text(value):
    """str / dict / list-of-dicts -> metn"""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for k in ("az", "aze", "src", "content", "text"):
            if isinstance(value.get(k), str):
                return value[k]
        strs = [v for v in value.values() if isinstance(v, str)]
        return max(strs, key=len) if strs else ""
    if isinstance(value, list):
        parts = []
        for m in value:
            if isinstance(m, dict):
                c = m.get("content") or m.get("text") or m.get("value") or ""
                role = m.get("role", "")
                if c:
                    parts.append(f"{role}: {c}" if role else c)
            elif isinstance(m, str):
                parts.append(m)
        return "\n".join(parts)
    return ""

def extract_text(ex, field):
    if field is None:
        strs = [v for v in ex.values() if isinstance(v, str)]
        return max(strs, key=len) if strs else ""
    fields = field if isinstance(field, list) else [field]
    for f in fields:
        if f in ex:
            t = to_text(ex[f])
            if t and len(t.strip()) > 20:
                return t
    return ""

# ---------- kitablari abzaslara bolme ----------
CHUNK_CYCLE = [950] * 7 + [6000] * 3   # 70% qisa, 30% uzun

def split_pieces(text, sizes=CHUNK_CYCLE):
    out, pos, i, n = [], 0, 0, len(text)
    while pos < n:
        size = sizes[i % len(sizes)]
        end = min(pos + size, n)
        if end < n:
            cut = text.rfind(". ", pos, end)
            if cut > pos + size // 2:
                end = cut + 2
        piece = text[pos:end].strip()
        if len(piece) >= 80:
            out.append(piece)
        pos = end
        i += 1
    return out

def iter_join(src):
    """Setir-setir gelen kitabi ID uzre birlesdirib abzaslara bolur."""
    ds = try_load(src)
    if ds is None:
        return
    key, fld = src["join_by"], src["join_field"]
    buf, cur, n_docs = [], None, 0
    for ex in ds:
        k = ex.get(key)
        sent = (ex.get(fld) or "").strip()
        if cur is None:
            cur = k
        if k != cur:
            for piece in split_pieces(" ".join(buf)):
                yield piece
                n_docs += 1
            buf, cur = [], k
        if sent:
            buf.append(sent)
    if buf:
        for piece in split_pieces(" ".join(buf)):
            yield piece
            n_docs += 1
    print(f"  [kitab rejimi] {n_docs} abzas hazirlandi")

def iter_docs(src):
    if src.get("join_by"):
        yield from iter_join(src)
        return
    ds = try_load(src)
    if ds is None:
        return
    for ex in ds:
        t = extract_text(ex, src.get("field"))
        if t:
            yield t

# ---------- bir gediş ----------
def pass_sources(cat_name, budget_bytes, mode):
    """Kateqoriyanin menbelerini sirayla oxuyur, budget_bytes qeder yazir."""
    if budget_bytes <= 0:
        return 0
    out_path = os.path.join(OUT_DIR, f"{cat_name}.txt")
    short_target = int(budget_bytes * SHORT_RATIO)
    long_target = int(budget_bytes * LONG_RATIO)
    p_short = p_long = p_docs = 0
    print(f"\n=== {cat_name}: bu gedişde {budget_bytes/1048576:.1f} MB ===")
    with open(out_path, mode, encoding="utf-8") as f:
        for src in SOURCES[cat_name]:
            if p_short >= short_target and p_long >= long_target:
                break
            name = src["id"] + (f" [{src['config']}]" if src.get("config") else "")
            print(f" Menbe: {name}")
            n_seen = 0
            try:
                for raw in iter_docs(src):
                    if p_short >= short_target and p_long >= long_target:
                        break
                    n_seen += 1
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
                    if len(text) < SHORT_MAX:
                        if p_short >= short_target:
                            stats["qisa_dolu"] += 1
                            continue
                        p_short += b
                    else:
                        if p_long >= long_target:
                            stats["uzun_dolu"] += 1
                            continue
                        p_long += b
                    seen_hashes.add(h)
                    vocab_add(tokens)
                    f.write(text + "\n\n")
                    p_docs += 1
                    cat_bytes[cat_name] += b
                    cat_docs[cat_name] += 1
                    if p_docs % 2000 == 0:
                        print(f"  ... {p_docs} metn | qisa {p_short/1048576:.1f} MB | uzun {p_long/1048576:.1f} MB | baxilan {n_seen}")
            except Exception as e:
                print(f"  [X] {name}: {type(e).__name__}: {str(e)[:120]} - novbeti menbeye kecirik")
                continue
            print(f"  Bitdi: {name} - baxilan {n_seen}, qebul {p_docs}")
    written = p_short + p_long
    print(f"=== {cat_name}: +{written/1048576:.1f} MB, {p_docs} metn (cemi {cat_bytes[cat_name]/1048576:.1f} MB) ===")
    return written

# =========== FAZA 1 ===========
print("\n########## FAZA 1: KATEQORIYALAR ##########")
for cat, mb in TARGETS_MB.items():
    pass_sources(cat, mb * 1024 * 1024, "w")

total = sum(cat_bytes.values())
print(f"\nFaza 1 neticesi: {total/1048576:.1f} MB")

# =========== FAZA 2 ===========
# Qeyd: 500 soz limiti cok sertdir. Real datada kateqoriyalar dolmaya biler.
# AUTO_RAISE_LIMIT = True etsen, kod limiti avtomatik artiracaq (1000, 2000, ...)
AUTO_RAISE_LIMIT = False
FILL_ORDER = ["01_web_news", "03_encyclopedic_technical", "02_conversation_subtitle",
              "05_fiction", "04_official_legal"]

deficit = TOTAL_TARGET_BYTES - total
if deficit > 1024:
    print(f"\n########## FAZA 2: {deficit/1048576:.1f} MB catismir ##########")
    for rnd in range(3):
        if deficit <= 1024:
            break
        before = deficit
        for cat in FILL_ORDER:
            if deficit <= 1024:
                break
            got = pass_sources(cat, deficit, "a")
            deficit -= got
            if got > 0:
                print(f"  {cat}: +{got/1048576:.1f} MB, qalan catismayan {deficit/1048576:.1f} MB")
        if deficit >= before:
            print("  Hec bir menbeden elave data tapilmadi.")
            if not AUTO_RAISE_LIMIT:
                print("  FAZA 2 dayandirilir. (AUTO_RAISE_LIMIT = True etsen, soz limiti artirilacaq)")
            break
else:
    print("\nFaza 2 lazim deyil.")

# ---------- FAZA 2B: soz limitini artirmaq (istege bagli) ----------
if AUTO_RAISE_LIMIT:
    for new_limit in (1000, 2000, 5000, 10000, 25000, 50000):
        deficit = TOTAL_TARGET_BYTES - sum(cat_bytes.values())
        if deficit <= 1024:
            break
        MAX_WORD_COUNT = new_limit
        print(f"\n#### FAZA 2B: soz limiti {new_limit}-e qaldirildi, catismayan {deficit/1048576:.1f} MB ####")
        for cat in FILL_ORDER:
            deficit = TOTAL_TARGET_BYTES - sum(cat_bytes.values())
            if deficit <= 1024:
                break
            got = pass_sources(cat, deficit, "a")
            if got > 0:
                print(f"  {cat}: +{got/1048576:.1f} MB")
    print(f"Son soz limiti: {MAX_WORD_COUNT}")

# =========== FAZA 3 ===========
print("\n########## FAZA 3: az_all.txt (tam 500 MB) ##########")
ALL_PATH = os.path.join(OUT_DIR, "az_all.txt")

def cut_utf8(b, n):
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
        print(f"  (sona {gap} bayt bos setir elave edildi)")

# =========== NETICE ===========
print("\n================== UMUMI NETICE ==================")
print(f"{'Fayl':32} {'MB':>9} {'Metn':>9}")
print("-" * 54)
cat_total = 0
for cat in TARGETS_MB:
    mb = cat_bytes[cat] / 1048576
    print(f"{cat:32} {mb:9.1f} {cat_docs[cat]:9}")
    cat_total += mb
print("-" * 54)
all_size = os.path.getsize(ALL_PATH)
print(f"{'KATEQORIYA CEMI':32} {cat_total:9.1f}")
print(f"{'az_all.txt':32} {all_size/1048576:9.2f}")
print(f"\nHedef: 500.00 MB | Faktiki: {all_size/1048576:.2f} MB")
print(f"Bayt: {all_size} / {TOTAL_TARGET_BYTES}")
print(f"Unikal mezmun soz: {len(word_counts)}")
print(f"En cox tekrarlanan 10 soz: {word_counts.most_common(10)}")
print("\nFiltr statistikasi:")
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

`/kaggle/working/az_data/`:

```
01_web_news.txt               175 MB
02_conversation_subtitle.txt  125 MB
03_encyclopedic_technical.txt 100 MB
04_official_legal.txt          50 MB
05_fiction.txt                 50 MB
az_all.txt               TAM 500 MB
```

`az_all.txt` dəqiq 524 288 000 bayt. Kod sonda çap edir:

```
Hedef: 500.00 MB | Faktiki: 500.00 MB
Bayt: 524288000 / 524288000
```
