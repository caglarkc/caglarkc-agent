# Manager Planning Mode

Bu orchestrator artik varsayilan olarak planning modunda calisir. `request.md` ile uyumlu olarak kullanici istegi once Gemini tabanli manager katmanina gider; worker kuyruğu ancak acik uygulama niyeti ve plan onayi sonrasinda baslar.

## Akis

1. CLI veya Telegram `task.received` gonderir.
2. `GraphManager` mevcut planning thread varsa onu reuse eder.
3. `planner` node, `ManagerPlanningService` uzerinden Gemini ile konusur.
4. Sistem `manager.reply` ve gerekiyorsa `plan.draft_updated` event'lerini yayar.
5. Kullanici `/apply` derse veya acikca "uygula / kod yaz / sprint baslat" isterse, dogrulanmis draft plan icin `plan.approval_needed` acilir.
6. Onaydan sonra ayni thread mevcut `dispatcher -> worker -> validator -> reviewer` akisina devam eder.

## Env

- `GEMINI_API_KEY`: manager planning icin zorunlu.
- `GEMINI_MODEL`: varsayilan Gemini model tanimi.
- `MANAGER_MODEL`: bos degilse manager icin kullanilan model.
- `MANAGER_USE_GEMINI=0`: gelistirme/test amacli yerel heuristic planning fallback.
- `MANAGER_MAX_HISTORY_TURNS`: manager'a gonderilen son konusma turu sayisi.
- `USE_LEGACY_PLANNER=1`: eski deterministik planner akisini geri acar.

## CLI

- `/task <metin>`: planning turu baslatir veya mevcut planning thread'e yeni bir tur ekler.
- `/apply [not]`: mevcut draft plani uygulama onayina yollar.
- `/approve <approval_id>`: onay verildiginde worker kuyruğu baslar.

Ornek:

```text
/task bir landing page kur, ana sayfada urun tanitimi ve iletisim formu olsun
/task mobilde de duzgun gorunsun
/apply
/approve <approval_id>
```

## Telegram

- `/task <metin>`: planning turu
- `/apply [not]`: draft plan icin approval acma
- approval butonlari: mevcut stale/idempotent guard ile calisir

## Notlar

- Varsayilan mod worker patlamasi degildir; draft plan yoksa veya yapisal dogrulama gecmezse approval acilmaz.
- Worker kuyruğu sadece dogrulanmis `PlanDraft.files[]` listesinden turetilir.
- Mevcut checkpoint, recovery, `ApprovalGuard`, event bus UI senkronu ve daemon girisi korunmustur.
