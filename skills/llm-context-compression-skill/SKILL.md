---
name: llm-context-compression
description: Coder AI için — LLM'e gönderilen bağlamı token limitini aşmadan sıkıştırmak; kritik bilgiyi koruyarak özetlemek.
---

## Purpose

Büyük dosyalar veya uzun geçmişler token limitini aşar.
Bağlam sıkıştırma: önemsiz detayları atar, kritik yapıyı korur.
LLM daha az tokenle daha fazla bağlam alır.

---

## When to Apply

- Dosya içeriği 2000 satırı geçtiğinde
- Birden fazla dosya aynı anda bağlama eklendiğinde
- Konuşma geçmişi 8000 tokeni aştığında

---

## Rules

- Dosya sıkıştırma: sadece fonksiyon imzaları + docstring (gövde yok).
- Geçmiş sıkıştırma: son 5 mesaj tam, öncekiler özet.
- Kritik: hata mesajları, görev tanımları asla atılmaz.
- Sıkıştırma sonrası token sayısı tahmin edilir ve loglanır.

---

## Guidelines

```python
import ast

def compress_file_to_signatures(source: str) -> str:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source[:500] + "\n# ... (kısaltıldı)"

    lines = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            lines.append(f"class {node.name}:")
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    prefix = "  async def " if isinstance(item, ast.AsyncFunctionDef) else "  def "
                    sig    = ast.unparse(item.args)
                    ret    = f" -> {ast.unparse(item.returns)}" if item.returns else ""
                    doc    = ast.get_docstring(item) or ""
                    lines.append(f"{prefix}{item.name}({sig}){ret}: ...")
                    if doc:
                        lines.append(f'    """{doc[:80]}"""')
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not any(isinstance(p, ast.ClassDef) for p in ast.walk(tree)):
                sig = ast.unparse(node.args)
                ret = f" -> {ast.unparse(node.returns)}" if node.returns else ""
                lines.append(f"def {node.name}({sig}){ret}: ...")
    return "\n".join(lines) or source[:500]

def estimate_tokens(text: str, chars_per_token: float = 4.0) -> int:
    return int(len(text) / chars_per_token)

def compress_context_files(
    files: dict[str, str],
    max_tokens: int = 4000,
) -> dict[str, str]:
    compressed = {}
    used = 0
    for path, content in files.items():
        if used >= max_tokens:
            break
        sig_only = compress_file_to_signatures(content)
        tokens   = estimate_tokens(sig_only)
        if used + tokens <= max_tokens:
            compressed[path] = sig_only
            used += tokens
        else:
            snippet = sig_only[:int((max_tokens - used) * 4)]
            compressed[path] = snippet + "\n# ... (kısaltıldı)"
            break
    return compressed
```

---

## References

- `context-injection-strategy-skill/SKILL.md` — bağlam enjeksiyonu
- `token-budget-management-skill/SKILL.md` — token bütçesi
- `sprint-context-window-management-skill/SKILL.md` — bağlam penceresi
