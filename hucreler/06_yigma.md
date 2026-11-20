# Hüceyrə 6 — Yığım (əsas iş)

5 kateqoriyanı yığır və filtrləyir. **Ən vacib hissə:** hər kateqoriya öz MB hədəfinə çatır, əgər hansısa kateqoriya dolmasa (məsələn altyazı azdır), çatışmayan hissəni **avtomatik başqa mənbədən doldurur**. Sonda `az_all.txt` **tam 500 MB** (524 288 000 bayt) olur — sözün ortasında kəsilmir, abzas sərhədində bitir.

**Vaxt:** 1–3 saat. Logda "FAZA 1 / FAZA 2 / FAZA 3" görəcəksən.

```python
# ------------------------------------------------------------
# HUCEYRE 6: Esas dovr - yig, filtrle, yaz
#   - her kateqoriya oz MB hedefine
#   - az_all.txt = TAM 500 MB (524 288 000 bayt)
# ------------------------------------------------------------
TOTAL_TARGET_BYTES = 500 * 1024 * 1024

seen_hashes = set()
word_counts = Counter()
stats = Counter()
cat_bytes = {c: 0 for c in TARGETS_MB}
cat_short = {c: 0 for c in TARGETS_MB}
cat_long = {c: 0 for c in TARGETS_MB}
cat_docs = {c: 0 for c in TARGETS_MB}

def vocab_ok(tokens):
    # Limitden kecen soz varmi? (sekilciler azaddir)
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

def pass_sources(cat_name, budget_bytes, mode):
    """Kateqoriyanin menbelerini sirayla oxuyur, budget_bytes qeder yazir.
    mode='w' - fayli sifirdan yazir, mode='a' - sonuna elave edir.
    Yazilan bayt sayini qaytarir."""
    if budget_bytes <= 0:
        return 0
    out_path = os.path.join(OUT_DIR, f"{cat_name}.txt")
    pass_short_target = int(budget_bytes * SHORT_RATIO)
    pass_long_target = int(budget_bytes * LONG_RATIO)
    p_short = p_long = p_docs = 0
    print(f"\n=== {cat_name}: bu gedişde {budget_bytes/1048576:.1f} MB ===")
    f = open(out_path, mode, encoding="utf-8")
    try:
        for src in SOURCES[cat_name]:
            if p_short >= pass_short_target and p_long >= pass_long_target:
                break
            print(f" Menbe: {src['id']} {src.get('config','')}")
            ds = try_load(src)
            if ds is None:
                continue
            try:
                first = next(iter(ds))
                print(f"  Numune acarlar: {list(first.keys())}")
            except Exception as e:
                print(f"  [X] Numune oxunmadi: {e}")
                continue
            n_seen = 0
            for ex in ds:
                if p_short >= pass_short_target and p_long >= pass_long_target:
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
                b = len((text + "\n\n").encode("utf-8"))
                if is_short(text):
                    if p_short >= pass_short_target:
                        stats["qisa_dolu"] += 1
                        continue
                    p_short += b
                    cat_short[cat_name] += b
                elif is_long(text):
                    if p_long >= pass_long_target:
                        stats["uzun_dolu"] += 1
                        continue
                    p_long += b
                    cat_long[cat_name] += b
                else:
                    stats["olcu_arasi"] += 1
                    continue
                seen_hashes.add(h)
                vocab_add(tokens)
                f.write(text + "\n\n")
                p_docs += 1
                cat_bytes[cat_name] += b
                cat_docs[cat_name] += 1
                if p_docs % 1000 == 0:
                    print(f"  ... bu gedişde {p_docs} metn, qisa {p_short/1048576:.1f} MB, uzun {p_long/1048576:.1f} MB, gorulen {n_seen}")
            print(f"  Bitdi: {src['id']} - gorulen {n_seen}")
    finally:
        f.close()
    written = p_short + p_long
    print(f"=== {cat_name}: bu gedişde {written/1048576:.1f} MB, {p_docs} metn (cemi {cat_bytes[cat_name]/1048576:.1f} MB) ===")
    return written


# ---------- FAZA 1: her kateqoriya oz hedefine ----------
print("\n########## FAZA 1: KATEQORIYALAR ##########")
for cat, mb in TARGETS_MB.items():
    pass_sources(cat, mb * 1024 * 1024, "w")

total = sum(cat_bytes.values())
print(f"\nFaza 1 neticesi: {total/1048576:.1f} MB")


# ---------- FAZA 2: catismayan hisseni doldur ----------
deficit = TOTAL_TARGET_BYTES - total
if deficit > 1024:
    print(f"\n########## FAZA 2: {deficit/1048576:.1f} MB catismir, doldurulur ##########")
    # Ustunluk siyahisi: en genis menbe evvelde
    FILL_ORDER = ["01_web_news", "03_encyclopedic_technical", "05_fiction",
                  "02_conversation_subtitle", "04_official_legal"]
    for rnd in range(3):
        if deficit <= 1024:
            break
        before = deficit
        for cat in FILL_ORDER:
            if deficit <= 1024:
                break
            got = pass_sources(cat, deficit, "a")
            deficit -= got
            if got == 0:
                print(f"  {cat}: elave hec ne tapilmadi")
            if got > 0:
                print(f"  {cat}: +{got/1048576:.1f} MB elave edildi, qalan catismayan {deficit/1048576:.1f} MB")
        if deficit >= before:
            break   # hec ne elave olunmadi, dayan
    total = sum(cat_bytes.values())
    print(f"Faza 2 neticesi: {total/1048576:.1f} MB")
else:
    print("\nFaza 2 lazim deyil - kateqoriyalar hedefi doldurub.")


# ---------- FAZA 3: az_all.txt = TAM 500 MB ----------
print("\n########## FAZA 3: az_all.txt yazilir (tam 500 MB) ##########")
ALL_PATH = os.path.join(OUT_DIR, "az_all.txt")

def cut_utf8(b, n):
    """Bayt sayini n-e endirir, simvolu yarmlamadan."""
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
                    # Son fayl: tam 500 MB-a catdiririq, soz ortasinda kesmirik
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
        written = TOTAL_TARGET_BYTES
        print(f"  (sona {gap} bayt bos setir elave edildi)")

print(f"az_all.txt = {os.path.getsize(ALL_PATH)} bayt = {os.path.getsize(ALL_PATH)/1048576:.2f} MB")


# ---------- NETICE ----------
print("\n================== UMUMI NETICE ==================")
print(f"{'Fayl':32} {'MB':>10} {'Metn':>10}")
print("-" * 56)
cat_total = 0
for cat in TARGETS_MB:
    mp = cat_bytes[cat] / 1048576
    print(f"{cat:32} {mp:10.1f} {cat_docs[cat]:10}")
    cat_total += mp
print("-" * 56)
all_mb = os.path.getsize(ALL_PATH) / 1048576
print(f"{'KATEQORIYA CEMI':32} {cat_total:10.1f}")
print(f"{'az_all.txt':32} {all_mb:10.2f}")
print(f"\nHedef: 500.00 MB | Faktiki: {all_mb:.2f} MB")
print(f"Bayt: {os.path.getsize(ALL_PATH)} / {TOTAL_TARGET_BYTES}")
print(f"Unikal mezmun soz: {len(word_counts)}")
print(f"En cox tekrarlanan 10 soz: {word_counts.most_common(10)}")
print("\nFiltr statistikasi (ne qeder atildi):")
for k, v in stats.most_common():
    print(f"  {k}: {v}")
print("\nCixis qovlugu:", OUT_DIR)
for fn in sorted(os.listdir(OUT_DIR)):
    fp = os.path.join(OUT_DIR, fn)
    print(f"  {fn:34} {os.path.getsize(fp)/1048576:8.2f} MB")
print("\nHazirdir! Kaggle -> Save Version -> Output Dataset")
```
