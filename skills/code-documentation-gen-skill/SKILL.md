---
name: code-documentation-gen
description: Coder AI için — üretilen Python koduna otomatik dokümantasyon eklemek; README ve API referansı oluşturmak.
---

## Purpose

Üretilen kod çalışır ama nasıl kullanılır, başka geliştirici bilemez.
Auto-doc: fonksiyon imzalarından docstring, modülden README taslağı üretir.
LLM tabanlı açıklama + AST tabanlı imza çıkarımı birleştirilir.

---

## When to Apply

- Yeni modül veya public API yazıldığında
- Reviewer "dokümantasyon eksik" dediğinde
- Sprint sonunda teslim dökümanı hazırlanırken

---

## Rules

- Docstring: tek satır özet + parametre açıklaması (Google style).
- README: modül amacı, kurulum, kullanım örneği.
- Özel metodlar (`_` ile başlayan) için docstring yazılmaz.
- Üretilen doc: ayrı branch veya PR notu olarak sunulur.

---

## Guidelines

```python
import ast

DOCSTRING_PROMPT = """
Şu Python fonksiyonu için tek satır docstring yaz (Google style).
Parametre açıklaması ekle.
Sadece docstring metnini döndür, tırnak işareti olmadan.

Fonksiyon imzası: {signature}
Fonksiyon gövdesi (ilk 10 satır): {body_snippet}
"""

def extract_public_functions(code: str) -> list[dict]:
    tree = ast.parse(code)
    funcs = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                funcs.append({
                    "name":      node.name,
                    "signature": ast.unparse(node.args),
                    "lineno":    node.lineno,
                    "body_snippet": ast.unparse(node.body[:3]) if node.body else "",
                })
    return funcs

async def generate_docstrings(llm, code: str) -> dict[str, str]:
    funcs = extract_public_functions(code)
    docstrings = {}
    for func in funcs:
        prompt = DOCSTRING_PROMPT.format(
            signature=f"def {func['name']}({func['signature']})",
            body_snippet=func["body_snippet"],
        )
        response = await llm.ainvoke([{"role": "user", "content": prompt}])
        docstrings[func["name"]] = response.content.strip()
    return docstrings

def inject_docstrings(code: str, docstrings: dict[str, str]) -> str:
    tree = ast.parse(code)
    lines = code.splitlines()
    offset = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in docstrings:
                insert_at = node.lineno + offset
                doc_line  = f'    """{docstrings[node.name]}"""'
                lines.insert(insert_at, doc_line)
                offset += 1
    return "\n".join(lines)
```

---

## References

- `docstring-generation-skill/SKILL.md` — docstring üretimi
- `code-review-checklist-skill/SKILL.md` — kod inceleme
- `sprint-diff-report-skill/SKILL.md` — sprint diff raporu
