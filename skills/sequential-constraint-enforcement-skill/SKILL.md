---
name: sequential-constraint-enforcement
description: Planner AI için — mutlaka sıralı çalışması gereken görevlerin bağımlılık kısıtlarını belirlemek ve dispatcher'ın bu sıralamaya uymasını sağlamak.
---

## Purpose

Yanlış sırayla çalışırsa bozulan görevlerin sırasını garanti altına alır.
`worker_queue`'daki `dependencies` alanını doğru doldurmayı sağlar.
"Önce interface, sonra implementasyon" gibi zorunlu sıraların kaybolmamasını önler.

---

## When to Apply

- Herhangi bir görev başka bir görevin çıktısını gerektiriyorsa
- Contract sprint → feature sprint sıralamasında
- Import bağımlılığı olan dosyalarda
- Test dosyaları yazılırken

---

## Rules

- Zorunlu sıralama her zaman `dependencies` listesiyle belirtilir.
- Bağımlılık döngüsü oluşturan sıralama plana giremez.
- "Sonra düzeltiriz" yaklaşımıyla sıralamayı atlatmak yasak.
- State.py her zaman en başta — başka hiçbir şeye bağımlı değil.
- Interface/Protocol tanımları implementasyondan önce.

---

## Guidelines

Zorunlu sıralama kalıpları:

```
State → Contract → Implementation → Test

src/graph/state.py
  ↓
src/core/contracts.py
  ↓
src/graph/nodes/planner.py
  ↓
tests/test_planner.py
```

QueueEntry dependencies formatı:
```python
QueueEntry(
    assignment={
        "worker_id": "worker_b",
        "target_file": "src/graph/nodes/planner.py",
        "task_type": "implement_node"
    },
    dependencies=["src/graph/state.py", "src/core/contracts.py"],
    status="planned"
)
```

Dispatcher bu listeyi kontrol eder: dependencies içindeki dosyaların status'u `done` olmadan bu görevi başlatmaz.

Döngü tespiti:
```
A → B bağımlı
B → A bağımlı  ← DÖNGÜ! Plan geçersiz, ayrıştır.
```

---

## Examples

```
YANLIŞ plan (sırasız):
worker_a: planner.py başlar (state.py henüz yazılmadı)
worker_b: state.py başlar

Sonuç: planner.py import hatasıyla başarısız

DOĞRU plan:
worker_a: state.py (bağımlılık yok)
↓ bitti
worker_b: planner.py (dependencies: ["state.py"])
```

---

## References

- `file-dependency-graph-design-skill/SKILL.md` — bağımlılık grafiği
- `parallel-task-identification-skill/SKILL.md` — paralel fırsatlar
- `worker-load-balancing-strategy-skill/SKILL.md` — worker atama
