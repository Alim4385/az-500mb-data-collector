# Hüceyrə 8 — MƏRHƏLƏ B — tam 500 MB

**MÜTLƏQ** · Vaxt: 5–15 dəq

Hovuzdan oxuyur, qlobal 3000 limitini tətbiq edir, 70/30 balans qurur.

**Yenilik:** data çatmırsa hovuzu **avtomatik genişləndirir** (Mərhələ A-nı yenidən çağırır, 3 cəhdə qədər). Sonda **tam 500 MB** olur. Çıxış faylları **düz `.txt`** — gz yoxdur.

**Görməlisən:** `TAM 500 MB - HAZIRDIR!`

```python
# ------------------------------------------------------------
# MƏRHƏLƏ B — SOZ LIMITI + BALANS + TAM 500 MB
# Hovuzdan oxuyur, qlobal 3000 limitini tetbiq edir, 70/30 balans
# qurur, tam 500 MB az_all.txt yazir. Catismayan olsa, hovuzu
# AVTOMATIK genislendirir (Merhele A-ni yeniden cagirir).
# Vaxt: 5-10 deqiqe
# ------------------------------------------------------------
import glob
import json
import time

TOTAL_TARGET_BYTES = 500 * 1024 * 1024
MAX_WORD_COUNT = 3000
POOL_DIR = "/tmp/pool"

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

def iter_pool(cat):
    """Hovuzdan metn axini (.jsonl ve ya .jsonl.gz)."""
    d = os.path.join(POOL_DIR, cat)
    if not os.path.isdir(d):
        return
    files = sorted(glob.glob(os.path.join(d, "*.jsonl*")))
    for f in files:
        try:
            fh = gzip.open(f, "rt", encoding="utf-8") if f.endswith(".gz") else open(f, encoding="utf-8")
            with fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    t = obj.get("text") or ""
                    if t:
                        yield t
        except Exception as e:
            print(f"  [X] {f}: {type(e).__name__}")

import gzip

# ---------- kitablar (05_fiction) ----------
CHUNK_CYCLE = [950] * 7 + [6000] * 3
BOOKS_SKIP = 0

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

def iter_books():
    """LocalDoc/books_dataset - ID uzre birlesdirib abzaslara bolur."""
    global BOOKS_SKIP
    ds = try_load({"id": "LocalDoc/books_dataset"})
    if ds is None:
        return
    if BOOKS_SKIP:
        ds = ds.skip(BOOKS_SKIP)
    buf, cur, n_read, n_docs = [], None, 0, 0
    for ex in ds:
        n_read += 1
        k = ex.get("ID")
        sent = (ex.get(" Sentence") or ex.get("Sentence") or "").strip()
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
    BOOKS_SKIP += n_read
    print(f"  [kitablar] {n_read} setir oxundu -> {n_docs} abzas")

# ---------- esas dovr ----------
def collect(cat_name, budget_bytes, stream, mode="w"):
    if budget_bytes <= 0:
        return 0
    out_path = os.path.join(OUT_DIR, f"{cat_name}.txt")
    short_target = int(budget_bytes * SHORT_RATIO)
    long_target = int(budget_bytes * LONG_RATIO)
    p_short = p_long = p_docs = 0
    t0 = time.time()
    print(f"\n=== {cat_name}: hedef {budget_bytes/1048576:.1f} MB ===")
    with open(out_path, mode, encoding="utf-8") as f:
        n_seen = 0
        for raw in stream():
            if p_short >= short_target and p_long >= long_target:
                break
            n_seen += 1
            if len(raw) < SHORT_MIN:
                stats["cox_qisa"] += 1
                continue
            if len(raw) > LONG_MAX * 3:
                stats["cox_uzun"] += 1
                continue
            text = " ".join(raw.split())
            tokens = tokenize(text)
            ok, reason = quality_ok(text, tokens)
            if not ok:
                stats[reason] += 1
                continue
            h = doc_hash(text)
            if h in seen_hashes:
                stats["dublikat"] += 1
                continue
            if not vocab_ok(tokens):
                stats["soz_limiti"] += 1
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
            if p_docs % 5000 == 0:
                el = time.time() - t0
                print(f"  ... {p_docs} metn | {(p_short+p_long)/1048576:.1f} MB | "
                      f"baxilan {n_seen} | {n_seen/max(el,1):.0f} sen/san")
    written = p_short + p_long
    print(f"=== {cat_name}: {written/1048576:.1f} MB, {p_docs} metn, {time.time()-t0:.0f} saniye ===")
    return written

def fill_all():
    for cat, mb in TARGETS_MB.items():
        budget = mb * 1024 * 1024
        if cat == "05_fiction":
            got = collect(cat, budget, lambda: iter_pool(cat), "w")
            if got < budget * 0.98:
                print("  Kitablardan elave edilir...")
                collect(cat, budget - got, iter_books, "a")
        else:
            collect(cat, budget, lambda: iter_pool(cat), "w")

print("\n########## MƏRHƏLƏ B ##########")
fill_all()

# ---------- catismayan olsa: hovuzu avtomatik genislendir ----------
for attempt in range(1, 4):
    total = sum(cat_bytes.values())
    deficit = TOTAL_TARGET_BYTES - total
    if deficit <= 4096:
        break
    need = [c for c in TARGETS_MB if cat_bytes[c] < TARGETS_MB[c] * 1024 * 1024 - 1024]
    print(f"\n### CATISMAYAN: {deficit/1048576:.1f} MB | genislendirilecek: {need} ###")
    if not need:
        break
    before_bytes = sum(cat_bytes.values())
    try:
        run_phase_a(cats=need, limit=PER_SOURCE_LIMIT, tag=f"topup{attempt}")
    except Exception as e:
        print(f"  Hovuz genislendirile bilmedi: {type(e).__name__}: {e}")
        break
    for cat in need:
        if cat == "05_fiction":
            collect(cat, TARGETS_MB[cat] * 1024 * 1024 - cat_bytes[cat], iter_books, "a")
        else:
            collect(cat, TARGETS_MB[cat] * 1024 * 1024 - cat_bytes[cat],
                    lambda c=cat: iter_pool(c), "a")
    gained = sum(cat_bytes.values()) - before_bytes
    print(f"  Bu turda elave: +{gained/1048576:.2f} MB")
    if gained < 1024:
        print("  Elave data tapilmadi - daha cehd etmirik.")
        break

total = sum(cat_bytes.values())
print(f"\nMerhele B neticesi: {total/1048576:.1f} MB")

# ---------- az_all.txt = TAM 500 MB ----------
print("\n########## az_all.txt (tam 500 MB) ##########")
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
    # YALNIZ cuzi bosluq (4 KB-dan az) doldurulur - saxta 500 MB yazmiriq
    if written < TOTAL_TARGET_BYTES:
        gap = TOTAL_TARGET_BYTES - written
        if gap < 4096:
            out.write(b"\n" * gap)
            print(f"  (sona {gap} bayt bos setir elave edildi)")
        else:
            print(f"  !!! {gap/1048576:.1f} MB catismir - fayl saxta doldurulmadi")
            print(f"  !!! Real olcu: {written/1048576:.2f} MB")

# ---------- netice ----------
print("\n================== UMUMI NETICE ==================")
print(f"{'Fayl':32} {'MB':>9} {'Metn':>9}")
print("-" * 54)
cat_total = 0
for cat in TARGETS_MB:
    mbv = cat_bytes[cat] / 1048576
    print(f"{cat:32} {mbv:9.1f} {cat_docs[cat]:9}")
    cat_total += mbv
print("-" * 54)
all_size = os.path.getsize(ALL_PATH)
print(f"{'KATEQORIYA CEMI':32} {cat_total:9.1f}")
print(f"{'az_all.txt':32} {all_size/1048576:9.2f}")
print(f"\nHedef: 500.00 MB | Faktiki: {all_size/1048576:.2f} MB")
print(f"Bayt: {all_size} / {TOTAL_TARGET_BYTES}")
if all_size == TOTAL_TARGET_BYTES:
    print("TAM 500 MB - HAZIRDIR!")
print(f"Soz limiti: {MAX_WORD_COUNT} | Unikal mezmun soz: {len(word_counts)}")
print(f"En cox tekrarlanan 10 soz: {word_counts.most_common(10)}")
print("\nFiltr statistikasi:")
for k, v in stats.most_common():
    print(f"  {k}: {v}")
print("\nCixis qovlugu:", OUT_DIR)
for fn in sorted(os.listdir(OUT_DIR)):
    fp = os.path.join(OUT_DIR, fn)
    print(f"  {fn:34} {os.path.getsize(fp)/1048576:8.2f} MB")
print("\nButun fayllar duz .txt formatindadir (gz yoxdur).")
print("Kaggle -> Save Version -> Output Dataset")
```
