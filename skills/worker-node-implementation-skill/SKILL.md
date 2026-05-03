---
name: worker-node-implementation
description: Coder AI için — LangGraph worker node'unu implemente etmek; LLM ile kod üretip diske yazarak file_registry'yi güncellemek.
---

## Purpose

Worker node, dispatcher'dan aldığı görevi gerçekleştirir: kod üretir ve yazar.
Her worker tek bir dosya sorumluluğundadır.
Başarılı olursa `done`, başarısız olursa `failed` durumuna geçer.

---

## When to Apply

- `src/graph/nodes/worker.py` yazılırken
- Paralel dosya yazma mantığı implemente edilirken
- Worker hata yönetimi eklenirken

---

## Rules

- Her worker izole çalışır — diğer worker state'ini değiştirmez.
- Kod üretimi LLM ile yapılır — doğrudan string yazılmaz.
- Dosya yazma atomik (`file-write-atomicity-skill`).
- Exception durumunda `failed` durum kaydedilir, hata loglanır.
- Context dosyaları prompt'a eklenir.

---

## Guidelines

```python
# src/graph/nodes/worker.py
async def worker_node(
    state: OrchestratorState,
    entry: QueueEntry,
) -> dict:
    file_path = entry.file_path
    
    # Context dosyalarını oku
    context = await _load_context_files(entry.context_files)
    
    # Prompt oluştur
    messages = build_coder_prompt(
        task_description=entry.task_description,
        file_path=file_path,
        context_files=context,
    )
    
    try:
        # Kod üret
        response = await llm.ainvoke(messages)
        code_content = extract_code_from_response(response.content)
        
        # Diske yaz
        await write_file_atomic(file_path, code_content)
        
        logger.info(f"Worker tamamlandı: {file_path}")
        
        updated_registry = dict(state["file_registry"])
        updated_registry[file_path] = "done"
        return {"file_registry": updated_registry}
    
    except Exception as e:
        logger.error(f"Worker başarısız: {file_path}: {e}")
        
        updated_registry = dict(state["file_registry"])
        updated_registry[file_path] = "failed"
        return {"file_registry": updated_registry}

def extract_code_from_response(content: str) -> str:
    """LLM yanıtından kod bloğunu çıkarır."""
    import re
    match = re.search(r'```(?:python)?\n(.*?)```', content, re.DOTALL)
    if match:
        return match.group(1)
    return content.strip()
```

---

## References

- `file-write-atomicity-skill/SKILL.md` — atomik yazma
- `prompt-template-construction-skill/SKILL.md` — prompt
- `file-status-state-machine-skill/SKILL.md` — durum
