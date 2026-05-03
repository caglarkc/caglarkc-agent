---
name: file-reservation-pattern
description: Coder AI için — dispatcher'ın dosyayı worker'a atamadan önce rezerve etmesi ve worker'ın sadece rezerve ettiği dosyaya yazması pattern'ı.
---

## Purpose

Birden fazla worker'ın aynı dosyaya yazmasını önler.
Atomik check-and-reserve operasyonu race condition olmadan sağlanır.
Reservation sonrası dosya durumu `planned → reserved → in_progress → done` sırasını korur.

---

## When to Apply

- `src/graph/nodes/dispatcher.py` worker atama kodu yazılırken
- `src/graph/nodes/worker.py` dosya yazma kodu yazılırken
- File registry güncelleme mantığı implementasyonu yapılırken

---

## Rules

- Dispatcher: atamadan önce `file_registry[path] == "planned"` kontrol eder.
- Kontrol ve atama atomik olmalı (lock içinde).
- Worker: sadece kendine atanan `reservation_owner` dosyasını yazar.
- Worker başka dosyaya yazamaz.
- Yazma tamamlanınca: `file_registry[path] = "done"`.
- Worker başarısız: `file_registry[path] = "failed"`, retry için `"planned"` olabilir.

---

## Guidelines

Dispatcher reservasyon:
```python
# dispatcher.py
async def _try_reserve_file(
    state: OrchestratorState,
    target_file: str,
    worker_id: str
) -> bool:
    file_registry = state.get("file_registry", {})
    
    if file_registry.get(target_file) != "planned":
        return False  # Zaten rezerve veya tamamlandı
    
    # Bu state güncelleme atomik sayılır (LangGraph reducer mantığı)
    return True  # Dispatcher state update döndürürken "reserved" set eder


# Dispatcher node return değeri
return {
    "file_registry": {
        **state.get("file_registry", {}),
        target_file: "reserved"  # Atomik güncelleme
    },
    "worker_status": {
        **state.get("worker_status", {}),
        worker_id: "reserved"
    },
    "worker_queue": updated_queue  # görevin status'u "assigned" olarak güncellendi
}
```

Worker dosya yazma:
```python
# worker.py
async def _write_file(
    project_id: str,
    target_file: str,
    worker_id: str,
    content: str
) -> None:
    # Sadece rezerve edilmiş dosyaya yaz
    project_manager = get_project_manager()
    await project_manager.write_project_file(
        project_id=project_id,
        file_path=target_file,
        content=content,
        worker_id=worker_id  # kim yazdı
    )
```

---

## References

- `asyncio-lock-usage-skill/SKILL.md` — atomik operasyon
- `state-update-return-pattern-skill/SKILL.md` — state güncelleme
- `file-status-state-machine-skill/SKILL.md` — dosya durumları
