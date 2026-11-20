# Hüceyrə 7 — Yığım — əsas iş

**MÜTLƏQ**

5 kateqoriyanı yığır, filtrdən keçirir, tam 500 MB `az_all.txt` yazır.

**Vaxt:** 1–3 saat. Logda FAZA 1, FAZA 2, FAZA 3 görəcəksən.

```python
# ------------------------------------------------------------
# HUCEYRE 6: Esas dovr - yig, filtrle, yaz
#   FAZA 1: her kateqoriya oz MB hedefine
#   FAZA 2: catismayan hisseni basqa menbeden doldur
#   FAZA 3: az_all.txt = TAM 500 MB
# ------------------------------------------------------------
TOTAL_TARGET_BYTES = 500 * 1024 * 1024   # tam 500 MB

seen_hashes = set()
word_counts = Counter()
stats = Counter()
cat_bytes = {c: 0 for c in TARGETS_MB}
cat_docs = {c: 0 for c in TARGETS_MB}

def vocab_ok(tokens):
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

# ---------- saheden metn cixarma ----------
def to_text(value):
    """str / dict / list-of-dicts -> metn"""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for k in ("az", "aze", "src", "content", "text"):
            if isinstance(value.get(k), str):
                return value[k]
        strs = [v for v in value.values() if isinstance(v, str)]
        return max(strs, key=len) if strs else ""
    if isinstance(value, list):
        parts = []
        for m in value:
            if isinstance(m, dict):
                c = m.get("content") or m.get("text") or m.get("value") or ""
                role = m.get("role", "")
                if c:
                    parts.append(f"{role}: {c}" if role else c)
            elif isinstance(m, str):
                parts.append(m)
        return "\n".join(parts)
    return ""

def extract_text(ex, field):
    if field is None:
        strs = [v for v in ex.values() if isinstance(v, str)]
        return max(strs, key=len) if strs else ""
    fields = field if isinstance(field, list) else [field]
    for f in fields:
        if f in ex:
            t = to_text(ex[f])
            if t and len(t.strip()) > 20:
                return t
    return ""

# ---------- kitablari abzaslara bolme ----------
CHUNK_CYCLE = [950] * 7 + [6000] * 3   # 70% qisa, 30% uzun

def split_pieces(text, sizes=CHUNK_CYCLE):
    out, pos, i, n = [], 0, 0, len(text)
    while pos < n:
        size = sizes[i % len(sizes)]
        end = min(pos + size, n)
        if end < n:
            cut = text.rfind(". ", pos, end)
            if cut > pos + size // 2:
                end = cut + 2
        piece = text[pos:end].strip()
        if len(piece) >= 80:
            out.append(piece)
        pos = end
        i += 1
    return out

def iter_join(src):
    """Setir-setir gelen kitabi ID uzre birlesdirib abzaslara bolur."""
    ds = try_load(src)
    if ds is None:
        return
    key, fld = src["join_by"], src["join_field"]
    buf, cur, n_docs = [], None, 0
    for ex in ds:
        k = ex.get(key)
        sent = (ex.get(fld) or "").strip()
        if cur is None:
            cur = k
        if k != cur:
            for piece in split_pieces(" ".join(buf)):
                yield piece
                n_docs += 1
            buf, cur = [], k
        if sent:
            buf.append(sent)
    if buf:
        for piece in split_pieces(" ".join(buf)):
            yield piece
            n_docs += 1
    print(f"  [kitab rejimi] {n_docs} abzas hazirlandi")

def iter_docs(src):
    if src.get("join_by"):
        yield from iter_join(src)
        return
    ds = try_load(src)
    if ds is None:
        return
    for ex in ds:
        t = extract_text(ex, src.get("field"))
        if t:
            yield t

# ---------- bir gediş ----------
def pass_sources(cat_name, budget_bytes, mode):
    """Kateqoriyanin menbelerini sirayla oxuyur, budget_bytes qeder yazir."""
    if budget_bytes <= 0:
        return 0
    out_path = os.path.join(OUT_DIR, f"{cat_name}.txt")
    short_target = int(budget_bytes * SHORT_RATIO)
    long_target = int(budget_bytes * LONG_RATIO)
    p_short = p_long = p_docs = 0
    print(f"\n=== {cat_name}: bu gedişde {budget_bytes/1048576:.1f} MB ===")
    with open(out_path, mode, encoding="utf-8") as f:
        for src in SOURCES[cat_name]:
            if p_short >= short_target and p_long >= long_target:
                break
            name = src["id"] + (f" [{src['config']}]" if src.get("config") else "")
            print(f" Menbe: {name}")
            n_seen = 0
            try:
                for raw in iter_docs(src):
                    if p_short >= short_target and p_long >= long_target:
                        break
                    n_seen += 1
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
                    if len(text) < SHORT_MAX:
                        if p_short >= short_target:
                            stats["qisa_dolu"] += 1
                            continue
                        p_short += b
                    else:
                        if p_long >= long_target:
                            stats["uzun_dolu"] += 1
                            continue
                        p_long += b
                    seen_hashes.add(h)
                    vocab_add(tokens)
                    f.write(text + "\n\n")
                    p_docs += 1
                    cat_bytes[cat_name] += b
                    cat_docs[cat_name] += 1
                    if p_docs % 2000 == 0:
                        print(f"  ... {p_docs} metn | qisa {p_short/1048576:.1f} MB | uzun {p_long/1048576:.1f} MB | baxilan {n_seen}")
            except Exception as e:
                print(f"  [X] {name}: {type(e).__name__}: {str(e)[:120]} - novbeti menbeye kecirik")
                continue
            print(f"  Bitdi: {name} - baxilan {n_seen}, qebul {p_docs}")
    written = p_short + p_long
    print(f"=== {cat_name}: +{written/1048576:.1f} MB, {p_docs} metn (cemi {cat_bytes[cat_name]/1048576:.1f} MB) ===")
    return written

# =========== FAZA 1 ===========
print("\n########## FAZA 1: KATEQORIYALAR ##########")
for cat, mb in TARGETS_MB.items():
    pass_sources(cat, mb * 1024 * 1024, "w")

total = sum(cat_bytes.values())
print(f"\nFaza 1 neticesi: {total/1048576:.1f} MB")

# =========== FAZA 2 ===========
# Qeyd: 500 soz limiti cok sertdir. Real datada kateqoriyalar dolmaya biler.
# AUTO_RAISE_LIMIT = True etsen, kod limiti avtomatik artiracaq (1000, 2000, ...)
AUTO_RAISE_LIMIT = False
FILL_ORDER = ["01_web_news", "03_encyclopedic_technical", "02_conversation_subtitle",
              "05_fiction", "04_official_legal"]

deficit = TOTAL_TARGET_BYTES - total
if deficit > 1024:
    print(f"\n########## FAZA 2: {deficit/1048576:.1f} MB catismir ##########")
    for rnd in range(3):
        if deficit <= 1024:
            break
        before = deficit
        for cat in FILL_ORDER:
            if deficit <= 1024:
                break
            got = pass_sources(cat, deficit, "a")
            deficit -= got
            if got > 0:
                print(f"  {cat}: +{got/1048576:.1f} MB, qalan catismayan {deficit/1048576:.1f} MB")
        if deficit >= before:
            print("  Hec bir menbeden elave data tapilmadi.")
            if not AUTO_RAISE_LIMIT:
                print("  FAZA 2 dayandirilir. (AUTO_RAISE_LIMIT = True etsen, soz limiti artirilacaq)")
            break
else:
    print("\nFaza 2 lazim deyil.")

# ---------- FAZA 2B: soz limitini artirmaq (istege bagli) ----------
if AUTO_RAISE_LIMIT:
    for new_limit in (1000, 2000, 5000, 10000, 25000, 50000):
        deficit = TOTAL_TARGET_BYTES - sum(cat_bytes.values())
        if deficit <= 1024:
            break
        MAX_WORD_COUNT = new_limit
        print(f"\n#### FAZA 2B: soz limiti {new_limit}-e qaldirildi, catismayan {deficit/1048576:.1f} MB ####")
        for cat in FILL_ORDER:
            deficit = TOTAL_TARGET_BYTES - sum(cat_bytes.values())
            if deficit <= 1024:
                break
            got = pass_sources(cat, deficit, "a")
            if got > 0:
                print(f"  {cat}: +{got/1048576:.1f} MB")
    print(f"Son soz limiti: {MAX_WORD_COUNT}")

# =========== FAZA 3 ===========
print("\n########## FAZA 3: az_all.txt (tam 500 MB) ##########")
ALL_PATH = os.path.join(OUT_DIR, "az_all.txt")

def cut_utf8(b, n):
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
        print(f"  (sona {gap} bayt bos setir elave edildi)")

# =========== NETICE ===========
print("\n================== UMUMI NETICE ==================")
print(f"{'Fayl':32} {'MB':>9} {'Metn':>9}")
print("-" * 54)
cat_total = 0
for cat in TARGETS_MB:
    mb = cat_bytes[cat] / 1048576
    print(f"{cat:32} {mb:9.1f} {cat_docs[cat]:9}")
    cat_total += mb
print("-" * 54)
all_size = os.path.getsize(ALL_PATH)
print(f"{'KATEQORIYA CEMI':32} {cat_total:9.1f}")
print(f"{'az_all.txt':32} {all_size/1048576:9.2f}")
print(f"\nHedef: 500.00 MB | Faktiki: {all_size/1048576:.2f} MB")
print(f"Bayt: {all_size} / {TOTAL_TARGET_BYTES}")
print(f"Unikal mezmun soz: {len(word_counts)}")
print(f"En cox tekrarlanan 10 soz: {word_counts.most_common(10)}")
print("\nFiltr statistikasi:")
for k, v in stats.most_common():
    print(f"  {k}: {v}")
print("\nCixis qovlugu:", OUT_DIR)
for fn in sorted(os.listdir(OUT_DIR)):
    fp = os.path.join(OUT_DIR, fn)
    print(f"  {fn:34} {os.path.getsize(fp)/1048576:8.2f} MB")
print("\nHazirdir! Kaggle -> Save Version -> Output Dataset")
```
