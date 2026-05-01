---
name: file-dependency-graph-design
description: Planner AI için — sprint içindeki dosyalar arasındaki bağımlılıkları tespit etmek ve hangi dosyanın hangisinden önce yazılması gerektiğini belirlemek.
---

## Purpose

Dosya bağımlılıklarını görsel veya yapısal olarak ortaya koyar.
Worker'ların birbirinin çıktısını beklemesi gereken sırayı belirler.
Bağımlılık döngülerini (circular dependency) engeller.

---

## When to Apply

- Sprint'e 3'ten fazla dosya girdiğinde
- Worker atamalarından önce
- "Dispatcher hangi görevi önce atayacak?" sorusu sorulduğunda
- Paralel vs. sıralı çalışma kararı verilirken

---

## Rules

- Her bağımlılık ilişkisi açıkça belirtilir: `A → B` (B, A'ya bağımlı).
- Bağımlılıksız dosyalar paralel çalışabilir.
- Döngüsel bağımlılık tespit edilirse sprint durdurulur ve ayrıştırılır.
- `src/graph/state.py` her zaman en başta yer alır — her şey ona bağımlı.
- Interface/contract dosyaları implementasyondan önce yazılır.

---

## Guidelines

Bağımlılık türleri:
```
Import bağımlılığı: B dosyası A'yı import ediyor → A önce
Veri bağımlılığı: B, A'nın ürettiği veriyi kullanıyor → A önce
State bağımlılığı: B, A'nın eklediği state alanını okuyor → A önce
Test bağımlılığı: test_B, B'nin var olmasını gerektiriyor → B önce
```

Grafik yazım formatı:
```
BAĞIMLILIK GRAFIĞI:
state.py (bağımlılık yok — ilk yazılır)
  └── models.py (state.py'yi kullanır)
      └── repository.py (models.py'yi kullanır)
          └── planner.py (repository + state kullanır)
              └── test_planner.py (planner.py test eder)

Paralel çalışabilecekler (aynı seviye):
- dispatcher.py ve worker.py (ikisi de state.py'ye bağımlı ama birbirine değil)
```

Dispatcher için bağımlılık bilgisi:
```python
# worker_queue entry'deki dependencies alanı
{
    "target_file": "src/graph/nodes/planner.py",
    "dependencies": ["src/graph/state.py", "src/core/contracts.py"]
}
```

---

## Examples

```
Sprint dosyaları:
A: src/graph/state.py
B: src/core/manager_planning.py  
C: src/graph/nodes/planner.py
D: tests/test_planner.py

Bağımlılık grafiği:
A (bağımsız)
└── B (A'yı import eder)
    └── C (A + B'yi import eder)
        └── D (C'yi test eder)

Sıra: A → B → C → D
Paralel fırsat: yok (hepsi sıralı)
```

---

## References

- `worker-load-balancing-strategy-skill/SKILL.md` — worker atama
- `parallel-task-identification-skill/SKILL.md` — paralel görevler
- `sequential-constraint-enforcement-skill/SKILL.md` — sıralı kısıtlar
