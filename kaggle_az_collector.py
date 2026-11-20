# ============================================================
# AZ 500 MB DATA YIGICI - KAGGLE UCUN
# ============================================================
# Meqsed: Azerbaycan dilinde 500 MB temiz metn (.txt)
# 5 kateqoriya:
#   1. Veb + Xeber            175 MB
#   2. Sohbet + Altyazi       125 MB
#   3. Ensiklopedik + Texniki 100 MB
#   4. Resmi / Huquqi          50 MB
#   5. Bedii                   50 MB
# Cemi: 500 MB
#
# Filtr (sert, LLM standarti - Gopher/FineWeb uslubu):
#   - Deqiq dublikat silme (hash)
#   - Uzunluq: 200 - 20000 simvol
#   - Keyfiyyet: herf nisbeti, tekrar, boilerplate
#   - Dil: Azerbaycan dili yoxlamasi
#   - XUSUSI: mezmun sozu max 500 defe (butun datada)
#             sekilci/komekci sozler bu limitden azaddir
#             limit kecen soz varsa BUTUN metn atilir
#   - Qisa/Uzun balansi: 70% qisa, 30% uzun
#
# Kaggle-da:
#   1. Create New Notebook
#   2. Settings: Internet = ON, GPU T4
#   3. Bu fayli yukle (Upload) ve Run All et
# ============================================================

# ------------------------------------------------------------
# HUCEYRE 1: Quraşdırma ve parametrler
# ------------------------------------------------------------
# !pip install -q datasets

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

# ------------------------------------------------------------
# HUCEYRE 2: Sekilci / komekci sozler (limitden AZAD)
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# HUCEYRE 3: Filtr funksiyalari (Gopher/FineWeb uslubu)
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# HUCEYRE 4: Menbeler (hazir, temiz datasetler)
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# HUCEYRE 5: Esas dovr - yig, filtrle, yaz
# ------------------------------------------------------------
seen_hashes = set()
word_counts = Counter()
stats = Counter()

def vocab_ok(tokens):
    # Limitden kecen soz varmi? (sekilciler azaddir)
    for t in set(tokens):
        if len(t) < EXEMPT_MIN_LEN:
            continue
        if t in EXEMPT_WORDS:
            continue
        if word_counts.get(t, 0) >= MAX_WORD_COUNT:
            return False
    return True

def vocab_add(tokens):
    for t in tokens:
        if len(t) < EXEMPT_MIN_LEN:
            continue
        if t in EXEMPT_WORDS:
            continue
        word_counts[t] += 1

def collect_category(cat_name, target_mb):
    target_bytes = int(target_mb * 1024 * 1024)
    short_target = int(target_bytes * SHORT_RATIO)
    long_target = int(target_bytes * LONG_RATIO)
    out_path = os.path.join(OUT_DIR, f"{cat_name}.txt")
    short_bytes = 0
    long_bytes = 0
    kept = 0
    print(f"\n=== {cat_name}: hedef {target_mb} MB (qisa {short_target/1048576:.0f} MB, uzun {long_target/1048576:.0f} MB) ===")
    with open(out_path, "w", encoding="utf-8") as f:
        for src in SOURCES[cat_name]:
            if short_bytes >= short_target and long_bytes >= long_target:
                break
            print(f" Menbe: {src['id']} {src.get('config','')}")
            ds = try_load(src)
            if ds is None:
                continue
            # Ilk numunenin acarlarin goster (debug)
            try:
                first = next(iter(ds))
                print(f"  Numune acarlar: {list(first.keys())}")
            except Exception as e:
                print(f"  [X] Numune oxunmadi: {e}")
                continue
            n_seen = 0
            for ex in ds:
                if short_bytes >= short_target and long_bytes >= long_target:
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
                # Qisa / Uzun balansi
                b = len(text.encode("utf-8"))
                if is_short(text):
                    if short_bytes >= short_target:
                        stats["qisa_dolu"] += 1
                        continue
                    short_bytes += b
                elif is_long(text):
                    if long_bytes >= long_target:
                        stats["uzun_dolu"] += 1
                        continue
                    long_bytes += b
                else:
                    stats["olcu_arasi"] += 1
                    continue
                # Qebul et
                seen_hashes.add(h)
                vocab_add(tokens)
                f.write(text + "\n\n")
                kept += 1
                if kept % 1000 == 0:
                    print(f"  ... {kept} qebul, qisa {short_bytes/1048576:.1f} MB, uzun {long_bytes/1048576:.1f} MB, gorulen {n_seen}")
            print(f"  Bitdi: {src['id']} - gorulen {n_seen}")
    total_mb = (short_bytes + long_bytes) / 1048576
    print(f"=== {cat_name} BITDI: {total_mb:.1f} MB / {target_mb} MB, {kept} metn ===")
    return total_mb, kept

print("\nBaslayiriq... (uzun cekebilir, 1-3 saat)")
results = {}
for cat, mb in TARGETS_MB.items():
    results[cat] = collect_category(cat, mb)

print("\n========== UMUMI NETICE ==========")
total = 0
for cat, (mb, n) in results.items():
    print(f"{cat}: {mb:.1f} MB, {n} metn")
    total += mb
print(f"CEMI: {total:.1f} MB / 500 MB")
print(f"Unikal mezmun soz: {len(word_counts)}")
print(f"En cox tekrarlanan 10 soz: {word_counts.most_common(10)}")
print("\nFiltr statistikasi (ne qeder atildi):")
for k, v in stats.most_common():
    print(f"  {k}: {v}")

# Birlesdirilmis fayl
print("\nBirlesdirilmis fayl yazilir...")
with open(os.path.join(OUT_DIR, "az_all.txt"), "w", encoding="utf-8") as out:
    for cat in TARGETS_MB:
        p = os.path.join(OUT_DIR, f"{cat}.txt")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                out.write(f.read())
print("Hazirdir! Cixis qovlugu:", OUT_DIR)
print("Fayllar:", os.listdir(OUT_DIR))
