# Hüceyrə 4B — Mənbə yoxlaması (YENİ)

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
