# Hüceyrə 2 — HF token (istəyə bağlı)

**İSTƏYƏ BAĞLI** · Vaxt: 2 san

Gated datasetlər üçün. Token olmasa da hər şey işləyir.

**Görməlisən:** `[!] HF token yoxdur...` — bu **xəta deyil**

```python
# ------------------------------------------------------------
# HUCEYRE 1B (YENI): HF TOKEN
# Gated datasetler ucun lazimdir (CulturaX, OpenSubtitles2024,
# eqanun, aze-books). Token olmasa da qalan menbeler isleyir.
# ------------------------------------------------------------
import os
HF_TOKEN = None
try:
    from kaggle_secrets import UserSecretsClient
    HF_TOKEN = UserSecretsClient().get_secret("HF_TOKEN")
except Exception:
    pass
if not HF_TOKEN:
    HF_TOKEN = os.environ.get("HF_TOKEN")

if HF_TOKEN:
    from huggingface_hub import login
    login(token=HF_TOKEN, add_to_git_credential=False)
    print("[OK] HF token qebul edildi - gated datasetler de isleyecek")
else:
    print("[!] HF token yoxdur - gated datasetler atlanacaq, qalanlari isleyecek")
    print("    Kaggle -> Add-ons -> Secrets -> New secret, ad: HF_TOKEN")
```
