# Hüceyrə 2 — Parametrlər

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
