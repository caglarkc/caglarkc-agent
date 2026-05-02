---
name: code-ast-manipulation
description: Coder AI için — Python AST ile mevcut koda programatik değişiklik yapmak; import ekleme, fonksiyon ekleme, decorator uygulama.
---

## Purpose

Metin tabanlı düzenleme kırılgan — AST manipülasyon doğru ve güvenli.
Mevcut dosyaya fonksiyon eklemek, import inject etmek veya decorator uygulamak.
LLM tam dosyayı yeniden üretmek yerine sadece delta üretir.

---

## When to Apply

- Var olan dosyaya yeni fonksiyon eklenmesi gerektiğinde
- Tüm fonksiyonlara belirli decorator eklenmesi istendiğinde
- Import'lar programatik olarak yönetilirken

---

## Rules

- AST parse başarısız olursa: metin düzenlemeye fallback.
- Ekleme: mevcut kodu silmez — sadece ekler.
- Yeniden üretim: ast.unparse() sonrası ruff format ile düzeltilir.
- Test: AST değişikliği sonrası syntax kontrolü yapılır.

---

## Guidelines

```python
import ast
import astor  # pip install astor

def add_import_if_missing(source: str, module: str, names: list[str]) -> str:
    tree = ast.parse(source)
    
    # Zaten import var mı?
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == module:
            existing = {alias.name for alias in node.names}
            new_names = [n for n in names if n not in existing]
            if not new_names:
                return source
    
    # Yeni import ekle
    new_import = ast.ImportFrom(
        module=module,
        names=[ast.alias(name=n) for n in names],
        level=0,
    )
    tree.body.insert(0, new_import)
    return ast.unparse(tree)

def add_decorator_to_functions(
    source: str,
    decorator_name: str,
    predicate = None,
) -> str:
    tree = ast.parse(source)
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if predicate is None or predicate(node):
                dec = ast.Name(id=decorator_name, ctx=ast.Load())
                node.decorator_list.insert(0, dec)
    
    return ast.unparse(tree)

def append_function(source: str, new_func_source: str) -> str:
    tree     = ast.parse(source)
    new_tree = ast.parse(new_func_source)
    
    for node in new_tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            tree.body.append(node)
    
    return ast.unparse(tree)

def validate_syntax(source: str) -> bool:
    try:
        ast.parse(source)
        return True
    except SyntaxError:
        return False
```

---

## References

- `file-write-atomicity-skill/SKILL.md` — atomik dosya yazma
- `code-import-resolver-skill/SKILL.md` — import çözücü
- `linter-integration-skill/SKILL.md` — linter entegrasyonu
