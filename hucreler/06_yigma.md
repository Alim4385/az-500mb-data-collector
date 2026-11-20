# Hüceyrə 6 — Yığım (əsas iş)

5 kateqoriyanı sıra ilə yığır, filtrdən keçirir, `/kaggle/working/az_data/` qovluğuna `.txt` yazır. Ən uzun hüceyrə — 1–3 saat çəkə bilər.

```python
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
```
