# Hüceyrə 4 — Filtr funksiyaları

**MÜTLƏQ**

Təmizləmə, dil yoxlaması, keyfiyyət filtri (Gopher/FineWeb), dublikat hash, qısa/uzun təyini.

**Vaxt:** dərhal. Sonda `Filtr funksiyalari hazirdir` yazır.

```python
AZ_CHARS = set("eqciOSU EQCIOSU".replace(" ", ""))  # placeholder, real check below
AZ_CHARS = set(["\u0259", "\u011f", "\u00e7", "\u0131", "\u00f6", "\u015f", "\u00fc",
                "\u018f", "\u011e", "\u00c7", "\u0130", "\u00d6", "\u015e", "\u00dc"])
AZ_STOPWORDS = {
    "ve", "ile", "ucun", "bir", "bu", "o", "da", "de", "ki",
    "men", "sen", "biz", "siz", "onlar", "he", "yox", "cox",
    "kimi", "sonra", "evvel", "amma", "lakin", "cunki", "eger",
    "oldu", "olacaq", "deyil", "hemise", "indi", "yene", "artiq",
}
BOILERPLATE = ["lorem ipsum", "cookie", "privacy policy", "terms of service",
               "subscribe", "abune ol", "reklam", "copyright"]
WORD_RE = re.compile(r"[A-Za-z\u018f\u0259\u011f\u00e7\u0131\u00f6\u015f\u00fc]+(?:['\-\u2019][A-Za-z\u018f\u0259\u011f\u00e7\u0131\u00f6\u015f\u00fc]+)*")

def normalize_text(text):
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", text)
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"\S+@\S+\.\S+", " ", text)
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"\s+", " ", line)
        lines.append(line)
    # Tekrarlanan setirleri sil (3-den cox tekrar = boilerplate)
    seen = {}
    out = []
    for line in lines:
        seen[line] = seen.get(line, 0) + 1
        if seen[line] <= 3:
            out.append(line)
    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def tokenize(text):
    return WORD_RE.findall(text.lower())

def is_azerbaijani(text, tokens):
    if not tokens:
        return False
    low = text.lower()
    az_char_count = sum(1 for ch in low if ch in AZ_CHARS)
    az_ratio = az_char_count / max(len(low), 1)
    stop_hits = sum(1 for t in tokens if t in AZ_STOPWORDS)
    stop_ratio = stop_hits / max(len(tokens), 1)
    # Azerbaycan herfleri var ve ya stopword nisbeti yuksekdirse AZ say
    if az_char_count >= 5 and az_ratio >= 0.005:
        return True
    if stop_ratio >= 0.08 and len(tokens) >= 20:
        return True
    # Kiril Azerbaycanca da ola biler - kiril nisbeti yuksekse qebul et
    cyr = sum(1 for ch in low if "\u0400" <= ch <= "\u04ff")
    if cyr / max(len(low), 1) >= 0.5 and stop_ratio >= 0.03:
        return True
    return False

def quality_ok(text, tokens):
    if not text or not tokens:
        return False, "bos"
    n = len(text)
    if n < SHORT_MIN:
        return False, "cox_qisa"
    if n > LONG_MAX:
        return False, "cox_uzun"
    if len(tokens) < 30 or len(tokens) > 3000:
        return False, "soz_sayi"
    # Herf nisbeti
    letters = sum(1 for ch in text if ch.isalpha())
    if letters / max(n, 1) < 0.70:
        return False, "herf_nisbeti"
    # Reqem nisbeti
    digits = sum(1 for ch in text if ch.isdigit())
    if digits / max(n, 1) > 0.20:
        return False, "reqem_cox"
    # Boilerplate
    low = text.lower()
    for pat in BOILERPLATE:
        if pat in low:
            return False, "boilerplate"
    # Tekrar: en cox tekrarlanan soz 30%-den cox olmasin
    cnt = Counter(tokens)
    most = cnt.most_common(1)[0][1]
    if most / len(tokens) > 0.30:
        return False, "soz_tekrari"
    # Punktuasiya coxlugu
    punct = sum(1 for ch in text if ch in "!?.,;:()[]{}\"'")
    if punct / max(n, 1) > 0.15:
        return False, "punktuasiya"
    return True, "ok"

def doc_hash(text):
    h = hashlib.blake2b(text.encode("utf-8", errors="ignore"), digest_size=8).hexdigest()
    return h

def is_short(text):
    return SHORT_MIN <= len(text) < SHORT_MAX

def is_long(text):
    return LONG_MIN <= len(text) <= LONG_MAX

print("Filtr funksiyalari hazirdir")
```
