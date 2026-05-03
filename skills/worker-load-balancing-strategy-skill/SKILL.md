---
name: worker-load-balancing-strategy
description: Planner AI için — görevleri worker_a, worker_b, worker_c arasında dengeli ve çakışmasız şekilde dağıtmak.
---

## Purpose

Worker'lar arasında iş yükünü dengeler.
Bir worker'ın aşırı yüklenmesini, diğerlerinin boşta beklemesini önler.
Dosya çakışması olmadan paralel çalışmayı sağlar.

---

## When to Apply

- Sprint'e birden fazla görev girecekse
- Dispatcher'a geçmeden önce worker atamaları yapılırken
- Worker başarısızlık geçmişi değerlendirilirken

---

## Rules

- Her worker aynı anda sadece 1 dosyayı rezerve eder.
- Aynı dosyaya iki worker atanamaz (file_registry çakışması).
- Worker başarısızlık sayısı yüksekse o worker'a kritik görev atanmaz.
- Bağımlılığı olmayan görevler farklı worker'lara paralel atanır.
- `worker_a` → karmaşık görevler (planner, core servisler).
- `worker_b` → orta karmaşıklık (dispatcher, validator).
- `worker_c` → basit görevler (config, interface, test).

---

## Guidelines

Atama matrisi (görev karmaşıklığına göre):
```
worker_a → Yüksek karmaşıklık
  - LLM entegrasyonu
  - LangGraph node implementasyonu
  - Core servis mantığı

worker_b → Orta karmaşıklık
  - Storage/repository işlemleri
  - Event bus subscriber
  - Validation mantığı

worker_c → Düşük karmaşıklık
  - Config/settings değişikliği
  - Interface/format düzenlemesi
  - Test dosyası
  - Log mesajı güncelleme
```

Çakışma kontrolü:
```python
# Planlama sırasında kontrol edilmesi gereken
görev_A → hedef: src/graph/nodes/planner.py → worker_a
görev_B → hedef: src/storage/repository.py → worker_b
görev_C → hedef: src/interfaces/telegram/notifier.py → worker_c
# Tüm dosyalar farklı → paralel çalışabilir ✓
```

---

## Examples

```
4 görev, 3 worker:

Görev 1: planner.py (yüksek) → worker_a
Görev 2: repository.py (orta) → worker_b  
Görev 3: settings.py (düşük) → worker_c
Görev 4: test_planner.py (düşük, Görev 1'e bağımlı) → worker_a (Görev 1 bittikten sonra)

worker_a Görev 1 → worker_a Görev 4 (sıralı)
worker_b Görev 2 (paralel)
worker_c Görev 3 (paralel)
```

---

## References

- `file-dependency-graph-design-skill/SKILL.md` — dosya çakışması
- `parallel-task-identification-skill/SKILL.md` — paralel fırsatlar
- `sequential-constraint-enforcement-skill/SKILL.md` — sıralı kısıtlar
