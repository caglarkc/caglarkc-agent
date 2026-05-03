---
name: code-string-formatting
description: Coder AI için — Python string formatlama yöntemlerini doğru seçmek; f-string, Template, format() kullanım rehberi.
---

## Purpose

Yanlış string formatlama: okunaksız kod, güvenlik açığı (SQL injection), performans kaybı.
Doğru yöntem: bağlama göre f-string, Template veya format() seçilir.
Kullanıcı girdisi içeren string'lerde template tercih edilir.

---

## When to Apply

- Prompt string'leri oluşturulurken
- SQL sorgusu veya komut satırı string'leri hazırlanırken
- Büyük çok satırlı metin şablonları yazılırken

---

## Rules

- Sabit bağlam: f-string (hızlı, okunabilir).
- Kullanıcı girdisi: Template.safe_substitute() — injection önler.
- SQL: parametre binding — f-string asla.
- Çok satırlı şablon: textwrap.dedent + Template.

---

## Guidelines

```python
from string import Template
import textwrap

# 1. f-string: sabit bağlam
name = "Ahmet"
greeting = f"Merhaba, {name}!"

# 2. Template: kullanıcı girdisi içeren string
user_input = "${DROP TABLE users}"  # Kötü niyetli
tmpl = Template("Hedef: $goal")
safe = tmpl.safe_substitute(goal=user_input)
# Sonuç: "Hedef: ${DROP TABLE users}" — tehlikeli karakter korunur

# 3. SQL: parametre binding
import sqlite3
conn = sqlite3.connect(":memory:")
# DOĞRU
conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
# YANLIŞ (asla yapma)
# conn.execute(f"SELECT * FROM tasks WHERE id = {task_id}")

# 4. Çok satırlı şablon
PROMPT_TEMPLATE = textwrap.dedent("""
    Sprint hedefi: $goal
    Mevcut dosyalar: $files
    Tamamlanan görevler: $done_count
""").strip()

def render_prompt(goal: str, files: list[str], done_count: int) -> str:
    return Template(PROMPT_TEMPLATE).substitute(
        goal=goal,
        files=", ".join(files[:5]),
        done_count=done_count,
    )

# 5. Büyük metin birleştirme: join (+ ile döngü değil)
lines = ["satır1", "satır2", "satır3"]
text  = "\n".join(lines)  # O(n), doğru
# text = ""  + lines[0] + "\n" + ...  # O(n²), yanlış
```

---

## References

- `prompt-template-construction-skill/SKILL.md` — prompt şablonu
- `input-validation-patterns-skill/SKILL.md` — giriş doğrulama
- `code-security-scan-skill/SKILL.md` — güvenlik tarama
