---
name: executor-output-handler
description: Coder AI için — executor node'un LLM çıktısını alıp dosyaya yazmak, state'i güncellemek ve başarı/hata durumunu raporlamak.
---

## Purpose

Executor node LLM'den kod alır ama bunu nereye yazar, nasıl state günceller?
Output handler: ham LLM çıktısını ayrıştırır, dosyaya yazar, state'i günceller.
Atomik operasyon: ya her şey başarılı ya da state kirletilmez.

---

## When to Apply

- Executor node LLM yanıtını işlerken
- Üretilen kodu dosyaya yazıp state'e kaydederken
- Kısmi başarı durumu yönetilirken (bazı dosyalar yazıldı, bazıları yazılamadı)

---

## Rules

- Çıktı ayrıştırma: markdown code block veya ham Python.
- Yazma: atomik — geçici dosya → rename.
- State güncelleme: dosya yolu → `done` durumuna.
- Hata: dosya yazılamadıysa `failed`, state kir değil.

---

## Guidelines

```python
import re
from pathlib import Path

def extract_code_from_llm_output(raw: str) -> str | None:
    # ```python ... ``` bloğu
    match = re.search(r"```python\s*\n(.*?)```", raw, re.DOTALL)
    if match:
        return match.group(1).strip()
    # ``` ... ``` (dil belirtilmemiş)
    match = re.search(r"```\s*\n(.*?)```", raw, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Ham kod (satırın çoğu py kodu gibi görünüyorsa)
    if raw.strip().startswith(("import ", "from ", "def ", "class ", "async ")):
        return raw.strip()
    return None

def write_code_atomically(file_path: str, content: str) -> bool:
    path = Path(file_path)
    tmp  = path.with_suffix(".tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(content, encoding="utf-8")
        tmp.rename(path)
        return True
    except OSError:
        tmp.unlink(missing_ok=True)
        return False

def handle_executor_output(
    llm_output: str,
    task: dict,
    state: dict,
) -> dict:
    file_path = task.get("file_path", "")
    code = extract_code_from_llm_output(llm_output)
    
    if not code:
        return {
            "file_registry": {
                **state.get("file_registry", {}),
                file_path: "failed",
            },
            "last_error": f"LLM kod bloğu bulunamadı: {file_path}",
        }
    
    success = write_code_atomically(file_path, code)
    registry = dict(state.get("file_registry", {}))
    registry[file_path] = "done" if success else "failed"
    
    update = {"file_registry": registry}
    if success:
        generated = dict(state.get("generated_files", {}))
        generated[file_path] = code
        update["generated_files"] = generated
    else:
        update["last_error"] = f"Dosya yazılamadı: {file_path}"
    
    return update
```

---

## References

- `executor-node-implementation-skill/SKILL.md` — executor node
- `file-write-atomicity-skill/SKILL.md` — atomik dosya yazma
- `llm-output-parsing-skill/SKILL.md` — LLM çıktı ayrıştırma
