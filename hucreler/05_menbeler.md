# Hüceyrə 5 — Mənbələr

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
