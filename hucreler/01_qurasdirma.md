# Hüceyrə 1 — Quraşdırma + parametrlər

`datasets` və `huggingface_hub` yüklənir, çıxış qovluğu və 5 kateqoriyanın MB hədəfləri təyin olunur.

**Dəyişməyib** — artıq işə salmısansa, keç.

```python
# !pip install -q -U datasets huggingface_hub

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
