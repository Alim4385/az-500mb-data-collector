# AZ 500 MB DATA YIGICI - SIFIRDAN VERSIYA
# KODLAR.md ile tam eyni (8 hucre)

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
MAX_WORD_COUNT = 3000   # 500 ile 500 MB mumkun deyil (README-ye bax)

print(f"Cixis qovlugu: {OUT_DIR}")
print(f"Hedefler: {TARGETS_MB}")
print(f"Soz limiti: max {MAX_WORD_COUNT} defe")
print("Qeyd: 500 limiti ile 500 MB yigmaq mumkun deyil - ona gore 3000")
print("HUCeyre 1 HAZIRDIR - novbeti hucreye kec")

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

# ------------------------------------------------------------
# MƏRHƏLƏ A — PARALEL YIĞIM (datatrove, 4 nüvə)
# Bu hüceyrə ağır işi görür: parquet oxumaq + filtrləmək.
# Nəticə: /kaggle/working/pool/<kateqoriya>/*.jsonl.gz (namizədlər)
# Vaxt: ~10-20 dəqiqə
# ------------------------------------------------------------
import os
import sys
import re
import subprocess

try:
    import datatrove
except ImportError:
    print("datatrove qurasdirilir...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "datatrove", "pyarrow"], check=False)

from datatrove.executor import LocalPipelineExecutor
from datatrove.pipeline.readers import ParquetReader
from datatrove.pipeline.filters.base_filter import BaseFilter
from datatrove.pipeline.writers import JsonlWriter

POOL_DIR = "/kaggle/working/pool"
os.makedirs(POOL_DIR, exist_ok=True)

WORKERS = 4              # Kaggle-da 4 CPU nuve
TASKS = 8                # bolgü sayi (cox olsa pis deyil)
PER_SOURCE_LIMIT = 250_000   # her menbeden max sened sayi
START_METHOD = "fork"    # notebook-da multiprocessing ucun lazimdir

# ---------- adapterler (mueyyen sutunlari olan datasetler ucun) ----------
def adapter_smoltalk(self, data, path, id_in_file):
    """messages_az: [{'role':..,'content':..}, ...] -> metn"""
    parts = []
    for m in (data.get("messages_az") or []):
        if isinstance(m, dict):
            c = m.get("content") or ""
            r = m.get("role") or ""
            if c:
                parts.append(f"{r}: {c}" if r else c)
    return {"text": "\n".join(parts), "id": str(id_in_file)}

def adapter_opus(self, data, path, id_in_file):
    """translation: {'az': '...', 'en': '...'} -> azerbaycan metni"""
    t = data.get("translation") or {}
    if isinstance(t, dict):
        return {"text": t.get("az") or "", "id": str(id_in_file)}
    return {"text": "", "id": str(id_in_file)}

# ---------- filtr ----------
class AzKeep(BaseFilter):
    """Bizim filtrler - datatrove icinde, her nuvede ayrica isleyir."""
    name = "AzKeep"

    def __init__(self, check_lang=True, **kwargs):
        super().__init__(**kwargs)
        self.check_lang = check_lang

    def filter(self, doc) -> bool:
        raw = doc.text
        if not raw or len(raw) < SHORT_MIN:
            return False
        if len(raw) > LONG_MAX * 3:
            return False
        text = " ".join(raw.split())   # re.sub-dan 3x suretli
        if len(text) < SHORT_MIN:
            return False
        tokens = tokenize(text)
        if self.check_lang and not is_azerbaijani(text, tokens):
            return False
        ok, _ = quality_ok(text, tokens)
        if not ok:
            return False
        doc.text = text
        return True

# ---------- menbe siyahisi (Mərhələ A ucun) ----------
# qeyd: 05_fiction burada YOXDUR - kitablar setir-setirlidir,
# onlari Merhele B-de ayrica yigiriq.
PHASE_A = {
    "01_web_news": [
        {"folder": "hf://datasets/HuggingFaceFW/fineweb-2/data/azj_Latn/train", "check_lang": False},
        {"folder": "hf://datasets/LocalDoc/community_oscar_azerbaijani/data", "text_key": "content", "check_lang": False},
        {"folder": "hf://datasets/LocalDoc/news_azerbaijan_2/data", "check_lang": False},
        {"folder": "hf://datasets/LocalDoc/news_azerbaijan/data", "check_lang": False},
    ],
    "02_conversation_subtitle": [
        {"folder": "hf://datasets/LocalDoc/smoltalk_az/data", "adapter": "smoltalk"},
        {"folder": "hf://datasets/Helsinki-NLP/opus-100/az-en", "adapter": "opus"},
    ],
    "03_encyclopedic_technical": [
        {"folder": "hf://datasets/wikimedia/wikipedia/20231101.az", "check_lang": False},
        {"folder": "hf://datasets/LocalDoc/azerbaijani-pretrain-corpus/data", "check_lang": False},
    ],
    "04_official_legal": [
        {"folder": "hf://datasets/LocalDoc/azerbaijan_legislation/data", "check_lang": False},
    ],
}

ADAPTERS = {"smoltalk": adapter_smoltalk, "opus": adapter_opus}

print("MƏRHƏLƏ A baslayir...")
print(f"Novbe sayi: {WORKERS}, tapsiriq: {TASKS}, her menbeden max {PER_SOURCE_LIMIT} sened\n")

import importlib
importlib.invalidate_caches()
import time as _time
T0 = _time.time()

for cat, specs in PHASE_A.items():
    for si, spec in enumerate(specs):
        out_dir = os.path.join(POOL_DIR, cat)
        os.makedirs(out_dir, exist_ok=True)
        name = spec["folder"].split("/")[-2] + "_" + spec["folder"].split("/")[-1]
        name = re.sub(r"[^A-Za-z0-9_.-]", "_", name)[:60]
        log_dir = os.path.join(POOL_DIR, "_logs", cat, f"{si}_{name}")

        reader_kw = {"limit": PER_SOURCE_LIMIT // TASKS, "batch_size": 1000}
        if "adapter" in spec:
            reader_kw["adapter"] = ADAPTERS[spec["adapter"]]
        if "text_key" in spec:
            reader_kw["text_key"] = spec["text_key"]

        t0 = _time.time()
        print(f"\n>>> {cat} | {spec['folder']}")
        try:
            executor = LocalPipelineExecutor(
                pipeline=[
                    ParquetReader(spec["folder"], **reader_kw),
                    AzKeep(check_lang=spec.get("check_lang", True)),
                    JsonlWriter(out_dir, output_filename="${rank}.jsonl"),
                ],
                tasks=TASKS,
                workers=WORKERS,
                logging_dir=log_dir,
                start_method=START_METHOD,
                skip_completed=False,
            )
            executor.run()
            print(f"<<< {cat} | {name} bitdi: {_time.time()-t0:.0f} saniye")
        except Exception as e:
            print(f"<<< XETA {cat} | {name}: {type(e).__name__}: {str(e)[:200]}")
            print("    (bu menbe atlanir, qalanlar davam edir)")

print(f"\nMƏRHƏLƏ A bitdi: {(_time.time()-T0)/60:.1f} deqiqe")
print("\nHovuzdaki namizedler:")
for cat in list(PHASE_A.keys()) + ["05_fiction"]:
    d = os.path.join(POOL_DIR, cat)
    if not os.path.isdir(d):
        continue
    files = [f for f in os.listdir(d) if f.endswith((".jsonl", ".jsonl.gz"))]
    size = sum(os.path.getsize(os.path.join(d, f)) for f in files) / 1048576
    print(f"  {cat:28} {len(files)} fayl, {size:.1f} MB (sıxılmış)")
print("\nNovbeti hucreye kec: MERHELE B")

# ------------------------------------------------------------
# MƏRHƏLƏ B — SOZ LIMITI + BALANS + YAZMA
# Hovuzdaki namizedleri oxuyur (yerli fayllar, suretlidir),
# global 3000 soz limitini tetbiq edir, 70/30 balans qurur,
# tam 500 MB az_all.txt yazir.
# Vaxt: 5-10 deqiqe
# ------------------------------------------------------------
import glob
import gzip
import json
import time

TOTAL_TARGET_BYTES = 500 * 1024 * 1024
MAX_WORD_COUNT = 3000
POOL_DIR = "/kaggle/working/pool"

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

def iter_pool(cat):
    """Hovuzdaki jsonl.gz fayllarindan metn axini."""
    d = os.path.join(POOL_DIR, cat)
    if not os.path.isdir(d):
        return
    for f in sorted(glob.glob(os.path.join(d, "*.jsonl*"))):
        opener = gzip.open if f.endswith(".gz") else open
        try:
            with opener(f, "rt", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    t = obj.get("text") or ""
                    if t:
                        yield t
        except Exception as e:
            print(f"  [X] {f}: {type(e).__name__}")

# ---------- kitablar (05_fiction) - setir-setir gelir, birlestiririk ----------
CHUNK_CYCLE = [950] * 7 + [6000] * 3

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

def iter_books():
    """LocalDoc/books_dataset - ID uzre birlesdirib abzaslara bolur."""
    ds = try_load({"id": "LocalDoc/books_dataset"})
    if ds is None:
        return
    buf, cur, n_docs = [], None, 0
    for ex in ds:
        k = ex.get("ID")
        sent = (ex.get(" Sentence") or ex.get("Sentence") or "").strip()
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
    print(f"  [kitablar] {n_docs} abzas hazirlandi")

# ---------- esas dovr ----------
def collect(cat_name, budget_bytes, stream, mode="w"):
    if budget_bytes <= 0:
        return 0
    out_path = os.path.join(OUT_DIR, f"{cat_name}.txt")
    short_target = int(budget_bytes * SHORT_RATIO)
    long_target = int(budget_bytes * LONG_RATIO)
    p_short = p_long = p_docs = 0
    t0 = time.time()
    print(f"\n=== {cat_name}: hedef {budget_bytes/1048576:.1f} MB ===")
    with open(out_path, mode, encoding="utf-8") as f:
        n_seen = 0
        for raw in stream():
            if p_short >= short_target and p_long >= long_target:
                break
            n_seen += 1
            if len(raw) < SHORT_MIN:
                stats["cox_qisa"] += 1
                continue
            if len(raw) > LONG_MAX * 3:
                stats["cox_uzun"] += 1
                continue
            text = " ".join(raw.split()) if "  " in raw or "\n" in raw else raw.strip()
            tokens = tokenize(text)
            ok, reason = quality_ok(text, tokens)
            if not ok:
                stats[reason] += 1
                continue
            h = doc_hash(text)
            if h in seen_hashes:
                stats["dublikat"] += 1
                continue
            if not vocab_ok(tokens):
                stats["soz_limiti"] += 1
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
            if p_docs % 5000 == 0:
                el = time.time() - t0
                print(f"  ... {p_docs} metn | {(p_short+p_long)/1048576:.1f} MB | "
                      f"baxilan {n_seen} | {n_seen/max(el,1):.0f} sen/san")
    written = p_short + p_long
    print(f"=== {cat_name}: {written/1048576:.1f} MB, {p_docs} metn, {time.time()-t0:.0f} saniye ===")
    return written

print("\n########## MƏRHƏLƏ B ##########")
for cat, mb in TARGETS_MB.items():
    budget = mb * 1024 * 1024
    if cat == "05_fiction":
        # evvel hovuz (varsa), sonra kitablar
        got = collect(cat, budget, lambda: iter_pool(cat), "w")
        if got < budget * 0.95:
            print("  Kitab menbeyinden elave edilir...")
            collect(cat, budget - got, iter_books, "a")
    else:
        collect(cat, budget, lambda: iter_pool(cat), "w")

total = sum(cat_bytes.values())
print(f"\nMerhele B neticesi: {total/1048576:.1f} MB")

# ---------- catismayan hisseni doldur ----------
deficit = TOTAL_TARGET_BYTES - total
FILL_ORDER = ["01_web_news", "03_encyclopedic_technical", "02_conversation_subtitle",
              "05_fiction", "04_official_legal"]
if deficit > 1024:
    print(f"\n{deficit/1048576:.1f} MB catismir - doldurulur...")
    for rnd in range(3):
        if deficit <= 1024:
            break
        before = deficit
        for cat in FILL_ORDER:
            if deficit <= 1024:
                break
            if cat == "05_fiction":
                got = collect(cat, deficit, iter_books, "a")
            else:
                got = collect(cat, deficit, lambda c=cat: iter_pool(c), "a")
            deficit -= got
            if got > 0:
                print(f"  {cat}: +{got/1048576:.1f} MB, qalan {deficit/1048576:.1f} MB")
        if deficit >= before:
            print("  Elave data tapilmadi.")
            break

# ---------- az_all.txt = tam 500 MB ----------
print("\n########## az_all.txt (tam 500 MB) ##########")
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
        print(f"  (sona {gap} bayt bos setir)")

# ---------- netice ----------
print("\n================== UMUMI NETICE ==================")
print(f"{'Fayl':32} {'MB':>9} {'Metn':>9}")
print("-" * 54)
cat_total = 0
for cat in TARGETS_MB:
    mbv = cat_bytes[cat] / 1048576
    print(f"{cat:32} {mbv:9.1f} {cat_docs[cat]:9}")
    cat_total += mbv
print("-" * 54)
all_size = os.path.getsize(ALL_PATH)
print(f"{'KATEQORIYA CEMI':32} {cat_total:9.1f}")
print(f"{'az_all.txt':32} {all_size/1048576:9.2f}")
print(f"\nHedef: 500.00 MB | Faktiki: {all_size/1048576:.2f} MB")
print(f"Bayt: {all_size} / {TOTAL_TARGET_BYTES}")
print(f"Soz limiti: {MAX_WORD_COUNT} | Unikal mezmun soz: {len(word_counts)}")
print(f"En cox tekrarlanan 10 soz: {word_counts.most_common(10)}")
print("\nFiltr statistikasi:")
for k, v in stats.most_common():
    print(f"  {k}: {v}")
print("\nCixis qovlugu:", OUT_DIR)
for fn in sorted(os.listdir(OUT_DIR)):
    fp = os.path.join(OUT_DIR, fn)
    print(f"  {fn:34} {os.path.getsize(fp)/1048576:8.2f} MB")
print("\nHazirdir! Kaggle -> Save Version -> Output Dataset")