# Phase 8 Acceptance

## Uygulanan Katmanlar
- `ProjectManager` artik proje listeleme, secme, arsivleme, history ve summary API'lerini sagliyor.
- `FairScheduler` proje bazli round-robin fairness, starvation onleme, concurrency limiti ve basit throttle policy tasiyor.
- `GraphManager` project-thread eslemesini acik tutuyor; scheduler ile coklu proje thread'lerini izole sekilde kaydedebiliyor.
- CLI ve Telegram tarafina `/projects` ve `/history` gorunumleri eklendi; CLI icin `/project use <id>` secimi de destekleniyor.

## Gecen Testler
- multi-project create/list/select
- CLI ve Telegram `/projects` / `/history` ciktilari
- project summary metrikleri
- parallel thread/project isolation
- scheduler fairness
- concurrency limit enforcement
- archived project dispatch disi kalmasi
- rate-limit throttle policy

## Tek Projeden Cok Projeye Gecis Garantileri
- approval ve state mutasyonlari proje/thread bazinda ayrisiyor
- scheduler tek projenin worker havuzunu tamamen kapatmasini engelliyor
- arsivli projeler gorunebilir kaliyor ama aktif dispatch'e girmiyor
- proje ozeti ve history verileri repository uzerinden deterministik uretiliyor
