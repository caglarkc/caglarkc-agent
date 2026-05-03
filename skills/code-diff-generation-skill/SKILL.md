---
name: code-diff-generation
description: Coder AI için — mevcut bir dosyada değişiklik yapılırken tam dosya yazmak yerine sadece değişen kısımları LLM'e ürettirmek.
---

## Purpose

Büyük dosya tamamen yeniden yazılırsa var olan çalışan kod kaybolabilir.
Diff tabanlı üretim: sadece değişen fonksiyon veya bloklar güncellenir.
Token tasarrufu ve güvenli değişiklik için.

---

## When to Apply

- Mevcut dosyaya yeni fonksiyon veya metod eklenirken
- Var olan fonksiyon güncellenmesi gerektiğinde
- Büyük dosya (300+ satır) değiştirilirken

---

## Rules

- Dosya 100 satırdan kısaysa: tam yeniden yaz kabul edilir.
- Büyük dosya: patch formatında değişiklik üret.
- Üretilen patch `ast` ile doğrulanır — syntax kontrol.
- Uygulama: `difflib` veya doğrudan string replace.

---

## Guidelines

```python
import difflib
import ast

def apply_function_replacement(
    original_code: str,
    function_name: str,
    new_function_code: str,
) -> str:
    """Belirtilen fonksiyonu dosyada yenisiyle değiştirir."""
    tree = ast.parse(original_code)
    
    # Fonksiyon satır aralığını bul
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == function_name:
                lines = original_code.splitlines(keepends=True)
                start = node.lineno - 1
                end = node.end_lineno
                
                new_lines = (
                    lines[:start]
                    + [new_function_code + "\n"]
                    + lines[end:]
                )
                return "".join(new_lines)
    
    raise ValueError(f"Fonksiyon bulunamadı: {function_name}")

# LLM prompt'u: tam dosya yerine sadece değişecek fonksiyon
def build_patch_prompt(
    file_path: str,
    current_function: str,
    change_description: str,
) -> list:
    return [
        SystemMessage(content=(
            "Sadece değişen fonksiyonu yaz. "
            "Tüm dosyayı yazmana gerek yok. "
            "Fonksiyon imzasını koru."
        )),
        HumanMessage(content=(
            f"Mevcut fonksiyon:\n```python\n{current_function}\n```\n\n"
            f"Değişiklik: {change_description}\n\n"
            f"Güncellenmiş fonksiyonu yaz."
        )),
    ]
```

---

## References

- `worker-node-implementation-skill/SKILL.md` — worker
- `file-write-atomicity-skill/SKILL.md` — dosya yazma
- `llm-output-parsing-skill/SKILL.md` — LLM çıktı
