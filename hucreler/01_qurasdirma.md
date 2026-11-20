# Hüceyrə 1 — Quraşdırma və parametrlər

**MÜTLƏQ** · Vaxt: 2–5 san

Kitabxanaları yoxlayır, çıxış qovluğunu və MB hədəflərini təyin edir.

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
