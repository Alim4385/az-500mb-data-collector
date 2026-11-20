# Hüceyrə 4 — Mənbələr (YENİLƏNDİ)

Hamısı açıq (gated olmayan) datasetlər.

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
