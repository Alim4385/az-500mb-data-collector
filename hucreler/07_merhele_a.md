# Hüceyrə 7 — MƏRHƏLƏ A — paralel yığım

**MÜTLƏQ** · Vaxt: 8–15 dəq

**4 CPU nüvə paralel** (datatrove). Namizədləri `/tmp/pool/` qovluğuna **düz `.jsonl`** kimi yazır — **gz yoxdur**.

**Görməlisən:** `MƏRHƏLƏ A bitdi` + hovuz cədvəli

```python
# ------------------------------------------------------------
# MƏRHƏLƏ A — PARALEL YIĞIM (datatrove, 4 nüvə)
# Namizədləri /tmp/pool qovluğuna DÜZ .jsonl kimi yazır (GZ YOXDUR).
# Vaxt: ~8-15 dəqiqə
# ------------------------------------------------------------
import os
import sys
import re
import subprocess

try:
    import datatrove
except ImportError:
    print("datatrove qurasdirilir (30-60 saniye)...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "datatrove", "pyarrow"], check=False)

import importlib
importlib.invalidate_caches()
import time

from datatrove.executor import LocalPipelineExecutor
from datatrove.pipeline.readers import ParquetReader
from datatrove.pipeline.filters.base_filter import BaseFilter
from datatrove.pipeline.writers import JsonlWriter

# /tmp - Kaggle Save Version-a DAXIL DEYIL (cox yer tutmur, suretli saxlanir)
POOL_DIR = "/tmp/pool"
os.makedirs(POOL_DIR, exist_ok=True)

POOL_COMPRESSION = None      # None = duz .jsonl  |  "gzip" = .jsonl.gz
WORKERS = 4                  # Kaggle-da 4 CPU nuve
TASKS = 8
PER_SOURCE_LIMIT = 250_000   # her menbeden max sened (bir gedişde)
START_METHOD = "fork"        # notebook-da multiprocessing ucun MUTLEQ

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
        text = " ".join(raw.split())      # re.sub-dan 3x suretli
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

# ---------- menbe siyahisi (Merhele A ucun) ----------
# 05_fiction burada YOXDUR - kitablar setir-setirlidir, Merhele B-de yigilir.
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
PHASE_A_STATE = {}      # her menbeden ne qeder oxundu (top-up ucun)

def run_phase_a(cats=None, limit=None, tag="", quiet=False):
    """Kateqoriyalari (ve ya hamisini) paralel yigir. Merhele B-den de cagirila biler."""
    lim = limit or PER_SOURCE_LIMIT
    per_task = max(1, lim // TASKS)
    targets = cats if cats else list(PHASE_A.keys())
    t_start = time.time()
    for cat in targets:
        for si, spec in enumerate(PHASE_A.get(cat, [])):
            name = spec["folder"].split("/")[-2] + "_" + spec["folder"].split("/")[-1]
            name = re.sub(r"[^A-Za-z0-9_.-]", "_", name)[:60]
            key = (cat, si)
            skip = PHASE_A_STATE.get(key, 0)

            out_dir = os.path.join(POOL_DIR, cat)
            os.makedirs(out_dir, exist_ok=True)
            log_dir = os.path.join(POOL_DIR, "_logs", cat, f"{si}_{name}_{tag or 'main'}")

            reader_kw = {"limit": per_task, "skip": skip, "batch_size": 1000}
            if "adapter" in spec:
                reader_kw["adapter"] = ADAPTERS[spec["adapter"]]
            if "text_key" in spec:
                reader_kw["text_key"] = spec["text_key"]

            if not quiet:
                print(f"\n>>> {cat} | {spec['folder']}  (oxunacaq: {per_task}, atlanacaq: {skip})")
            t0 = time.time()
            try:
                LocalPipelineExecutor(
                    pipeline=[
                        ParquetReader(spec["folder"], **reader_kw),
                        AzKeep(check_lang=spec.get("check_lang", True)),
                        JsonlWriter(out_dir, output_filename="${rank}.jsonl",
                                    compression=POOL_COMPRESSION),
                    ],
                    tasks=TASKS,
                    workers=WORKERS,
                    logging_dir=log_dir,
                    start_method=START_METHOD,
                    skip_completed=False,
                ).run()
                PHASE_A_STATE[key] = skip + per_task
                if not quiet:
                    print(f"<<< {cat} | {name} bitdi: {time.time()-t0:.0f} saniye")
            except Exception as e:
                print(f"<<< XETA {cat} | {name}: {type(e).__name__}: {str(e)[:200]}")
                print("    (bu menbe atlanir, qalanlar davam edir)")
    if not quiet:
        print(f"\nVaxt: {(time.time()-t_start)/60:.1f} deqiqe")

def pool_stats():
    """Hovuzda ne var - cap edir."""
    print("\nHovuzdaki namizedler:")
    total = 0
    for cat in TARGETS_MB:
        d = os.path.join(POOL_DIR, cat)
        if not os.path.isdir(d):
            print(f"  {cat:28} 0 fayl, 0.0 MB")
            continue
        files = [f for f in os.listdir(d) if f.endswith((".jsonl", ".jsonl.gz"))]
        size = sum(os.path.getsize(os.path.join(d, f)) for f in files) / 1048576
        total += size
        print(f"  {cat:28} {len(files)} fayl, {size:.1f} MB")
    print(f"  {'CEMI':28} {total:.1f} MB")

print("MƏRHƏLƏ A baslayir...")
print(f"Novbe: {WORKERS} nüvə | tapsiriq: {TASKS} | her menbeden max {PER_SOURCE_LIMIT} sened")
print(f"Hovuz: {POOL_DIR} | format: {'duz .jsonl' if POOL_COMPRESSION is None else 'jsonl.gz'}")

run_phase_a()
pool_stats()
print("\nNovbeti hucreye kec: MERHELE B")
```
