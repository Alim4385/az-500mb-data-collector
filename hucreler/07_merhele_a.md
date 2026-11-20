# Hüceyrə 7 — MƏRHƏLƏ A — paralel yığım (datatrove)

**MÜTLƏQ** · Vaxt: 8–15 dəq

**4 CPU nüvə ilə paralel.** Parquet oxuyur, filtrləyir, namizədləri `/kaggle/working/pool/` qovluğuna yazır.

```python
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

t_all = time.time() if "time" in dir() else None
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
```
