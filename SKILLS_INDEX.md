# Skills Index — caglarkc-agent

Bu dosya, Planner AI ve Coder AI için yazılmış **360 skill**'in tam listesini içerir.
Her skill `skills/<name>-skill/SKILL.md` dosyasında detaylıca açıklanmıştır.

## Nasıl Kullanılır?

Her skill bir AI ajanına belirli bir davranışı öğretir.
- **Planner AI** becerileri: sprint planlama, kullanıcı iletişimi, karar alma, raporlama.
- **Coder AI** becerileri: Python kod üretimi, LangGraph, async, test, güvenlik.

Skill dosyaları sistem prompt'una veya context'e eklenerek ilgili AI'ın davranışını yönlendirir.

---

## Skill Listesi (360 Skill)

| Skill Adı | Açıklama |
|-----------|----------|
| `abstract-base-class` | Coder AI için — Python ABC (Abstract Base Class) ile interface sözleşmesi tanımlamak; implementasyonu olmayan abstract metod bildirmek. |
| `acceptance-criteria-definition` | Planner AI için — her sprint ve görev için "bitti" ne demektir sorusunu net kriterlerle yanıtlamak; onay öncesi kontrol listesi oluşturmak. |
| `aiosqlite-patterns` | Coder AI için — aiosqlite ile async SQLite operasyonlarının bu projedeki standart pattern'ları; connection, query, transaction ve row factory. |
| `api-key-masking` | Coder AI için — API key, token ve şifre gibi hassas verilerin log'a, hata mesajına veya user output'a düşmemesini sağlamak. |
| `api-rate-limit-handling` | Coder AI için — LLM veya harici API'lerin hız limitlerini (rate limit) yönetmek; 429 hatasında akıllı bekleme uygulamak. |
| `approval-flow-orchestration` | Planner AI için — HITL onay akışının tüm adımlarını koordine etmek; plan sunumu, bekleme, onay/ret işleme ve devam etme. |
| `approval-request-drafting` | Planner AI için — kullanıcıya sunulacak onay isteğini net, özlü ve aksiyon alınabilir şekilde hazırlamak; teknik detayları kullanıcı diline çevirmek. |
| `approval-timeout-handling` | Planner AI için — HITL onay bekleme süresi aşıldığında ne yapılacağını belirlemek; timeout sonrası kullanıcıyı hatırlatmak veya planı iptal etmek. |
| `architecture-decision-record` | Planner AI için — önemli mimari kararları ADR (Architecture Decision Record) formatında kaydetmek; neden bu yaklaşım seçildi, alternatifleri nelerdi. |
| `async-architecture-validation` | Planner AI için — sistemin async mimarisinin tutarlı olduğunu doğrulamak; blocking call, yanlış await, event loop bloklaması gibi sorunları review sırasında tespit etmek. |
| `async-await-correctness-review` | Planner AI için — await eksikliği, gereksiz async, yanlış event loop kullanımı gibi async/await hatalarını review sırasında tespit etmek. |
| `async-context-manager` | Coder AI için — async with bloğu gerektiren kaynakların (DB bağlantısı, HTTP session, kilit) doğru açılıp kapatılması için async context manager yazmak. |
| `async-event-driven` | Coder AI için — asyncio event loop üzerinde olay güdümlü mimari kurmak; callback yerine async event handler kullanmak. |
| `async-function-template` | Coder AI için — bu projede her async fonksiyonun uyması gereken standart yapı; tip hint, hata handling, logging ve return formatı dahil. |
| `async-generator-pattern` | Coder AI için — async generator (async def + yield) kullanarak büyük veri setlerini bellek verimli şekilde akış halinde işlemek. |
| `async-lock-usage` | Coder AI için — asyncio.Lock ile paylaşılan kaynakları korumak; eşzamanlı erişimde yarış koşullarını önlemek. |
| `async-pubsub-pattern` | Coder AI için — asyncio tabanlı pub/sub mesajlaşma deseni uygulamak; yayıncı ve abone bileşenleri gevşek bağlamak. |
| `async-queue-usage` | Coder AI için — asyncio.Queue ile dispatcher ve worker arasında iş kuyruğu oluşturmak; producer/consumer pattern uygulamak. |
| `async-semaphore-throttling` | Coder AI için — asyncio.Semaphore ile eşzamanlı işlem sayısını sınırlamak; kaynakları aşırı yüklemeden paralel iş yapmak. |
| `async-timeout-pattern` | Coder AI için — asyncio.wait_for ile async operasyonlara zaman aşımı eklemek; takılı kalan işlemleri belirli süre sonra iptal etmek. |
| `async-transaction-management` | Coder AI için — aiosqlite ile çoklu yazma operasyonunu tek atomik transaction içinde yönetme; commit ve rollback pattern'ları. |
| `asyncio-gather-usage` | Coder AI için — birden fazla coroutine'i eş zamanlı çalıştırmak için asyncio.gather() kullanımının doğru yolu; exception handling ve return_exceptions. |
| `asyncio-lock-usage` | Coder AI için — shared state'i korumak için asyncio.Lock() kullanımının doğru yolu; StateManager, file_registry ve diğer paylaşılan kaynaklarda race condition önleme. |
| `asyncio-task-creation` | Coder AI için — asyncio.create_task() ile background task oluşturmanın doğru yolu; task referansı yönetimi, iptal ve temizleme. |
| `batch-processing` | Coder AI için — büyük listeyi küçük batch'lere bölerek işlemek; bellek kullanımını kontrol altında tutmak ve rate limit aşımını önlemek. |
| `blocking-call-detection` | Coder AI için — async context'te event loop'u bloklayan sync çağrıları tespit etmek ve async alternatifleriyle değiştirmek. |
| `caching-patterns` | Coder AI için — sık erişilen verileri (proje bilgisi, şema) bellekte önbelleğe almak; gereksiz DB çağrısını azaltmak. |
| `cascading-failure-prevention` | Planner AI için — bir worker veya dosyanın başarısız olmasının zincirleme olarak bağımlı görevleri de çökertmesini önlemek; izole hata yönetimi. |
| `chat-model-invocation` | Coder AI için — LangChain ChatModel (Gemini, OpenRouter) ile doğru async çağrı yapma; mesaj listesi oluşturma, structured output ve hata yönetimi. |
| `checkpoint-inspection` | Coder AI için — LangGraph checkpoint'te saklanan state'i okuyarak mevcut sprint durumunu analiz etmek; hata ayıklama ve recovery için. |
| `checkpoint-strategy-review` | Planner AI için — LangGraph checkpoint konfigürasyonunun doğru yapılandırıldığını, state'in düzenli kaydedildiğini ve crash sonrası recovery'nin çalıştığını review sırasında doğrulamak. |
| `cli-argument-parsing` | Coder AI için — argparse veya Click ile CLI komutları ve argümanları tanımlamak; kullanıcı dostu hata mesajları vermek. |
| `code-ast-manipulation` | Coder AI için — Python AST ile mevcut koda programatik değişiklik yapmak; import ekleme, fonksiyon ekleme, decorator uygulama. |
| `code-class-design` | Coder AI için — Python sınıfı tasarlarken sorumlulukları netleştirmek; SRP, composition over inheritance prensiplerini uygulamak. |
| `code-complexity-metric` | Coder AI için — üretilen kodun siklomatik karmaşıklığını ve satır sayısını ölçmek; çok karmaşık fonksiyonları işaretlemek. |
| `code-context-manager-advanced` | Coder AI için — contextlib ile özel context manager yazmak; kaynakları otomatik serbest bırakmak ve cleanup garantilemek. |
| `code-dataclass-field-validators` | Coder AI için — Python dataclass alanlarında __post_init__ ile doğrulama yapmak; geçersiz veri nesnesi oluşmasını önlemek. |
| `code-dead-code-detection` | Coder AI için — üretilen kodda kullanılmayan fonksiyonlar, değişkenler ve import'ları tespit etmek. |
| `code-decorator-factory` | Coder AI için — parametreli decorator (decorator factory) yazmak; retry, timeout, cache gibi davranışları fonksiyonlara dinamik eklemek. |
| `code-diff-generation` | Coder AI için — mevcut bir dosyada değişiklik yapılırken tam dosya yazmak yerine sadece değişen kısımları LLM'e ürettirmek. |
| `code-documentation-gen` | Coder AI için — üretilen Python koduna otomatik dokümantasyon eklemek; README ve API referansı oluşturmak. |
| `code-enum-patterns` | Coder AI için — Python Enum sınıflarını doğru kullanmak; string literal yerine tip güvenli sabitler tanımlamak. |
| `code-environment-guard` | Coder AI için — üretilen kodun yanlış ortamda (production vs dev) çalışmasını engelleyen guard'lar eklemek. |
| `code-exception-hierarchy` | Coder AI için — proje özel istisna hiyerarşisi tasarlamak; hataları kategorize etmek ve tutarlı yakalamayı sağlamak. |
| `code-explanation` | Planner AI için — üretilen kodu kullanıcıya anlaşılır şekilde açıklamak; ne yaptığını, neden bu yaklaşımın seçildiğini özetlemek. |
| `code-functional-patterns` | Coder AI için — Python'da fonksiyonel programlama kalıplarını uygulamak; map, filter, reduce, partial ve compose kullanımı. |
| `code-generation-quality-check` | Coder AI için — LLM'den gelen kod çıktısını üretim öncesinde hızlıca kalite kontrolünden geçirmek; sık yapılan LLM hatalarını otomatik tespit etmek. |
| `code-generation-templates` | Coder AI için — tekrar eden kod kalıplarını (repository, service, node) şablon olarak tanımlamak; LLM'in ürettiği kodu standart yapıda tutmak. |
| `code-generator-function` | Coder AI için — Python generator fonksiyonları ile büyük veri setlerini bellek dostu şekilde işlemek. |
| `code-import-resolver` | Coder AI için — üretilen koddaki import hatalarını tespit edip çözmek; eksik veya yanlış import'ları düzeltmek. |
| `code-mode` | AI Development Team Orchestrator projesinde Codex'in kod yazma kuralları. Claude'dan gelen görev prompt'larını alır, analiz eder, projenin mimarisine uygun kod yazar ve standart formatta teslim eder. Her kodlama görevinde bu skill kullanılır. |
| `code-module-boundary` | Coder AI için — modüller arası sınırları net çizmek; hangi fonksiyonların public, hangilerinin internal olduğunu tanımlamak. |
| `code-naming-convention` | Coder AI için — üretilen koddaki isimlendirme hatalarını tespit edip düzeltmek; tutarlı Python isimlendirme sağlamak. |
| `code-performance-hint` | Coder AI için — üretilen kodda belirgin performans sorunlarını tespit edip iyileştirme önerileri sunmak. |
| `code-property-pattern` | Coder AI için — Python @property decorator ile hesaplanan özellik, doğrulama ve lazy loading uygulamak. |
| `code-protocol-implementation` | Coder AI için — Python Protocol sınıfları ile structural subtyping uygulamak; interface sözleşmesi olmadan duck typing güvenliğini sağlamak. |
| `code-refactor-suggestion` | Coder AI için — üretilen veya mevcut kodda refactor fırsatlarını tespit edip önermek. |
| `code-review-checklist` | Planner AI için — reviewer node'unun üretilen kodu değerlendirirken kullandığı kontrol listesini uygulamak; geçme/kalma kararı vermek. |
| `code-security-scan` | Coder AI için — üretilen kodda güvenlik açıklarını tespit etmek; SQL injection, hardcoded secret, path traversal gibi yaygın sorunları bulmak. |
| `code-singleton-pattern` | Coder AI için — Python Singleton desenini doğru uygulamak; EventBus, config, DB pool gibi paylaşılan kaynaklar için tek örnek garantisi. |
| `code-skeleton-generation` | Coder AI için — görev açıklamasından önce kod iskeleti (stub) oluşturmak; sonra detayları doldurmak. |
| `code-string-formatting` | Coder AI için — Python string formatlama yöntemlerini doğru seçmek; f-string, Template, format() kullanım rehberi. |
| `code-style-guide` | Coder AI için — proje kod stilini tanımlamak ve uygulamak; tutarlı Python kodu üretmek. |
| `code-test-coverage-check` | Coder AI için — üretilen Python kodunun test kapsamını ölçmek ve minimum eşiği karşılamayan modülleri raporlamak. |
| `code-test-fixture-cleanup` | Coder AI için — test fixture'larının testlerden sonra temizlenmesini sağlamak; geçici dosya, DB kaydı ve mock'ların silinmesi. |
| `code-type-stub-generation` | Coder AI için — üretilen modüller için .pyi tip stub dosyaları oluşturmak; dış kullanıcılara tip bilgisi sağlamak. |
| `concurrency-safety-review` | Planner AI için — eş zamanlı async operasyonlarda race condition, shared state mutasyonu ve lock eksikliği gibi concurrency güvenlik sorunlarını review sırasında tespit etmek. |
| `concurrent-task-limiting` | Coder AI için — asyncio.Semaphore ve asyncio.BoundedSemaphore ile eşzamanlı görev sayısını sınırlamak; kaynak tüketimini kontrol altında tutmak. |
| `conditional-edge-function` | Coder AI için — LangGraph conditional edge fonksiyonlarını src/graph/edges.py'e doğru yazma; tüm case'leri kapsayan, pure function, string döndüren routing fonksiyonları. |
| `conditional-sprint-flow` | Planner AI için — sprint içinde koşullu akış oluşturmak; belirli koşullar sağlanırsa farklı görev setleri yürütmek. |
| `config-hot-reload` | Coder AI için — daemon çalışırken .env dosyasındaki değişiklikleri yeniden başlatmadan yüklemek; dinamik konfigürasyon güncelleme. |
| `config-schema-versioning` | Coder AI için — konfigürasyon şemasının versiyonunu yönetmek; eski config dosyalarını yeni versiyona taşımak. |
| `constant-and-config-extraction` | Coder AI için — sihirli sayı ve string'leri koddan çıkarıp sabit veya config olarak tanımlamak; bakımı kolaylaştırmak. |
| `context-injection-strategy` | Coder AI için — LLM prompt'una hangi bağlam bilgisinin, hangi sırada ve ne kadar ekleneceğine sistematik karar vermek. |
| `context-manager-implementation` | Coder AI için — async context manager (async with) ve sync context manager (__enter__/__exit__) implementasyonunun bu projede doğru kullanımı. |
| `context-window-management` | Coder AI için — LLM'e gönderilen prompt'un token limitini aşmaması için context içeriğini akıllıca kırpma ve önceliklendirme. |
| `conversation-history-trimming` | Planner AI için — konuşma geçmişi büyüdüğünde context window'u taşmadan önce eski mesajları budamak; önemli bağlamı korumak. |
| `conversation-mode-routing` | Planner AI için — gelen kullanıcı mesajını analiz ederek doğru PM moduna yönlendirmek; sohbet mu planlama mı onay mı olduğuna karar vermek. |
| `custom-exception-hierarchy` | Coder AI için — bu projeye özgü exception sınıf hiyerarşisini tasarlamak ve uygulamak; hatanın kaynağına göre spesifik exception tipleri kullanmak. |
| `daemon-ops` | AI Development Team Orchestrator projesinin 7/24 daemon olarak çalıştırılması. systemd service kurulumu, otomatik başlatma, crash recovery, log yönetimi, deployment adımları. Daemon kurulumu veya deployment kodu yazarken referans alınır. |
| `database-schema-review` | Planner AI için — SQLite tablo tasarımını, Pydantic storage modellerini ve repository metodlarının doğruluğunu review sırasında doğrulamak. |
| `dataclass-vs-pydantic` | Coder AI için — ne zaman Python dataclass ne zaman Pydantic model kullanılacağını belirlemek; her ikisinin güçlü yönlerini doğru senaryoda uygulamak. |
| `db-connection-pool` | Coder AI için — SQLite veya PostgreSQL için async bağlantı havuzu oluşturmak; her sorgu için yeni bağlantı açmamak. |
| `dead-code-detection` | Planner AI için — kullanılmayan import, fonksiyon, değişken, yorum satırı ve erişilemeyen kod bloklarını review sırasında tespit etmek ve temizletmek. |
| `dead-letter-queue` | Coder AI için — maksimum retry sayısını aşan ve işlenemeyen görevleri dead-letter queue'ya alarak raporlamak; sonsuz retry döngüsünü önlemek. |
| `decision-log-maintenance` | Planner AI için — sprint boyunca alınan mimari ve teknik kararları Decision kaydı olarak DB'ye yazmak; ileride "neden böyle yaptık?" sorusunu yanıtlamak. |
| `dependency-graph-visualization` | Planner AI için — proje modülleri arasındaki import bağımlılıklarını görsel grafik olarak göstermek; mimari kararları desteklemek. |
| `dependency-injection-patterns` | Coder AI için — repository, LLM client ve event bus gibi bağımlılıkları node ve servislere doğru şekilde enjekte etmek; test edilebilirliği artırmak. |
| `dispatcher-node-implementation` | Coder AI için — LangGraph dispatcher node'unu implemente etmek; planned dosyaları reserved yapıp worker kuyruğuna atmak. |
| `docstring-generation` | Coder AI için — fonksiyon ve sınıflara kısa, bilgilendirici docstring eklemek; parametre ve dönüş tiplerini açıklamak. |
| `dry-principle-enforcement` | Coder AI için — tekrar eden kod bloklarını tespit etmek ve ortak fonksiyon/yardımcı modüle taşımak; "Don't Repeat Yourself" prensibini uygulamak. |
| `dynamic-task-injection` | Planner AI için — sprint çalışırken öngörülemeyen bağımlılık keşfedildiğinde yeni görev enjekte etmek; planı dondurulmamış tutmak. |
| `enum-definition` | Coder AI için — bu projede string enum'ların doğru tanımlanma yolu; FileStatus, WorkerStatus gibi mevcut enum'larla tutarlı yapı. |
| `env-file-setup` | Coder AI için — .env dosyasını ve .env.example şablonunu oluşturmak; ortam değişkenlerini güvenli şekilde yönetmek. |
| `env-var-validation` | Coder AI için — daemon başlarken tüm zorunlu environment variable'ların varlığını ve geçerliliğini kontrol etmek; eksik config ile sessizce çalışmayı önlemek. |
| `environment-detection` | Coder AI için — uygulamanın hangi ortamda çalıştığını (development/test/production) tespit etmek; ortama göre farklı davranış sergilemek. |
| `error-categorization` | Coder AI için — oluşan hataları sistematik kategorilere ayırmak; her kategori için farklı tepki stratejisi uygulamak. |
| `event-driven-pattern-validation` | Planner AI için — event emit ve subscribe pattern'larının doğru uygulandığını, event isimlerinin tutarlı olduğunu ve event'lerin doğru payload ile gönderildiğini review sırasında kontrol etmek. |
| `event-emission-pattern` | Coder AI için — EventBus üzerinden event emit etmenin standart yolu; EventEnvelope oluşturma, event isimlendirme ve payload yapısı. |
| `event-replay` | Coder AI için — kaydedilen event'leri sırayla yeniden oynatarak sistemi belirli bir duruma getirmek; test ve debug için event sourcing benzeri pattern. |
| `event-sourcing-pattern` | Coder AI için — sistem durumunu olaylar dizisi olarak saklamak; state'i olaylardan yeniden oluşturmak. |
| `event-subscription-pattern` | Coder AI için — EventBus'a abone olmanın standart yolu; callback kayıt, async callback, ve subscription lifecycle yönetimi. |
| `exception-handling-review` | Planner AI için — hata yakalama mantığının doğru exception tiplerini kullandığını, bare except olmadığını, hataların log'landığını ve uygun şekilde propagate edildiğini review sırasında kontrol etmek. |
| `execution-intent-detection` | Planner AI için — kullanıcının sadece tartışmak mı yoksa gerçekten kodu çalıştırmak mı istediğini tespit etmek; yanlış execution intent tespiti gereksiz sprint başlatır. |
| `executor-node-implementation` | Coder AI için — LangGraph executor node'unu implemente etmek; dispatch_queue'daki girişleri paralel worker task'larına dönüştürmek. |
| `executor-output-handler` | Coder AI için — executor node'un LLM çıktısını alıp dosyaya yazmak, state'i güncellemek ve başarı/hata durumunu raporlamak. |
| `exponential-backoff-calculation` | Coder AI için — retry beklemelerini 2^n * base_delay formülüyle hesaplama, jitter ekleme ve maksimum gecikme sınırlama. |
| `feature-breakdown` | Planner AI için — büyük bir özellik isteğini birden fazla sprint'e bölmek; her sprint'in bağımsız, teslim edilebilir bir değer içermesini sağlamak. |
| `file-backup-strategy` | Coder AI için — worker kod yazmadan önce mevcut dosyayı yedeklemek; yazma başarısız olduğunda orijinal dosyayı geri yüklemek. |
| `file-context-loader` | Coder AI için — worker node'da kod üretmeden önce bağımlı dosyaların içeriğini okuyarak LLM prompt'una eklemek. |
| `file-dependency-detection` | Coder AI için — Python import analizi ile hangi dosyanın hangi dosyaya bağımlı olduğunu tespit etmek; doğru context_files listesi oluşturmak. |
| `file-dependency-graph-design` | Planner AI için — sprint içindeki dosyalar arasındaki bağımlılıkları tespit etmek ve hangi dosyanın hangisinden önce yazılması gerektiğini belirlemek. |
| `file-generation-pipeline` | Coder AI için — tek dosya üretimini aşamalı pipeline'a dönüştürmek; oluştur → doğrula → düzelt → kaydet. |
| `file-reservation-pattern` | Coder AI için — dispatcher'ın dosyayı worker'a atamadan önce rezerve etmesi ve worker'ın sadece rezerve ettiği dosyaya yazması pattern'ı. |
| `file-status-state-machine` | Coder AI için — file_registry içindeki dosya durumlarının geçerli geçişlerini (planned → reserved → in_progress → done/failed) zorlamak. |
| `file-template-registry` | Coder AI için — sık kullanılan dosya şablonlarını kayıt altında tutmak; yeni dosyaları şablondan oluşturmak. |
| `file-watcher` | Coder AI için — proje dosyalarındaki değişiklikleri watchdog veya asyncio ile izlemek; değişen dosyaları otomatik yeniden işlemek. |
| `file-write-atomicity` | Coder AI için — üretilen kod dosyasını diske yazarken kısmi yazma ve yarım dosya sorunlarını önlemek için atomik write pattern uygulamak. |
| `fixture-factory-pattern` | Coder AI için — pytest fixture'larında test verisi üreten factory fonksiyonları yazmak; tekrar eden test setup kodunu merkezileştirmek. |
| `function-length-review` | Planner AI için — çok uzun fonksiyonları tespit etmek; tek sorumluluktan sapan ve yeniden kullanılabilir parçalara bölünmesi gereken fonksiyonları işaretlemek. |
| `graceful-degradation` | Coder AI için — bir bileşen başarısız olduğunda sistemin azaltılmış işlevsellikle çalışmaya devam etmesini sağlamak; tam çöküşü önlemek. |
| `graceful-shutdown-implementation` | Coder AI için — daemon'ın SIGTERM/SIGINT sinyallerini yakalayarak tüm aktif işlemleri temizce durdurmak, state'i flushe etmek ve bağlantıları kapatmak. |
| `graph-assembly` | Coder AI için — LangGraph StateGraph'ını tüm node'lar ve edge'lerle birleştirerek derlenmiş graph oluşturmak. |
| `graph-builder-usage` | Coder AI için — LangGraph StateGraph'ı doğru oluşturma, node ekleme, edge bağlama ve AsyncSqliteSaver ile compile etme. |
| `graph-hot-reload` | Coder AI için — LangGraph iş akışını yeniden başlatmadan güncellemek; node değişikliklerini canlı uygulamak. |
| `graph-invocation-async` | Coder AI için — compile edilmiş LangGraph'ı ainvoke() ve astream() ile doğru çalıştırma; thread config, input state ve sonuç işleme. |
| `graph-node-isolation-test` | Coder AI için — LangGraph node fonksiyonlarını tüm graph çalıştırmadan izole birim testlerle doğrulama. |
| `graph-state-inspection` | Coder AI için — çalışan veya durdurulmuş bir LangGraph thread'inin mevcut state'ini okumak, sıradaki node'u öğrenmek ve state'i manuel güncellemek. |
| `graph-state-reset` | Coder AI için — LangGraph state'ini belirli alanları koruyarak kısmen sıfırlamak; yeni sprint başlangıcında önceki sprint'in çöp alanlarını temizlemek. |
| `healthcheck-endpoint` | Coder AI için — daemon'ın sağlık durumunu raporlayan basit health check mekanizması; DB bağlantısı, LLM erişimi ve aktif sprint durumu. |
| `heartbeat-emission` | Coder AI için — stall detection için dispatcher ve worker node'larından düzenli heartbeat event'i emit etmek. |
| `http-client-patterns` | Coder AI için — async HTTP istekleri yapmak; httpx.AsyncClient veya aiohttp ile doğru session yönetimi ve timeout ayarı. |
| `idempotency-enforcement` | Coder AI için — aynı operasyonun birden fazla kez çalıştırılmasının güvenli olduğunu garanti etmek; tekrarlanan daemon restart ve LangGraph resume senaryolarında veri tutarlılığını korumak. |
| `implicit-assumption-surfacing` | Planner AI için — kullanıcının söylemediği ama varsaydığı şeyleri ortaya çıkarmak; gizli beklentileri ve kabul edilen varsayımları netleştirmek. |
| `import-structure-review` | Planner AI için — import listesinin doğru sıralanıp sıralanmadığını, kullanılmayan import'ların bulunup bulunmadığını ve circular import riski taşıyıp taşımadığını review sırasında kontrol etmek. |
| `incremental-delivery-planning` | Planner AI için — her sprint sonunda kullanıcıya somut değer teslim etmek; "hep ya da hiç" yerine kademeli ilerleme planlamak. |
| `input-validation-patterns` | Coder AI için — kullanıcıdan veya dış sistemden gelen verinin Pydantic ile doğrulanması; hatalı input'u erken yakalamak. |
| `integration-requirement-analysis` | Planner AI için — sistemin dış servisler, API'lar ve diğer bileşenlerle nasıl entegre olacağını analiz etmek; entegrasyon noktalarını ve bağımlılıkları belirlemek. |
| `integration-test-setup` | Coder AI için — LangGraph graph'ının gerçek (veya near-real) bileşenlerle end-to-end çalıştığını doğrulayan integration test altyapısını kurmak. |
| `intent-disambiguation` | Planner AI için — kullanıcı isteği belirsizse anlamlandırmak; farklı yorumları listeleyip doğruyu sormak. |
| `interface-contract-review` | Planner AI için — fonksiyon imzaları, Pydantic modeller ve event kontratlarının doğru ve tutarlı olduğunu review sırasında doğrulamak. |
| `interrupt-before-node` | Coder AI için — LangGraph HITL (Human-in-the-Loop) interrupt pattern'ını uygulamak; belirli bir node'dan önce graph'ı durdurmak ve onay sonrası resume etmek. |
| `langgraph-edge-routing-review` | Planner AI için — LangGraph conditional edge fonksiyonlarının doğru state'e göre routing yaptığını, tüm olası sonuçların ele alındığını ve sonsuz döngü oluşturmadığını review sırasında doğrulamak. |
| `langgraph-node-design-review` | Planner AI için — LangGraph node implementasyonlarının doğru sorumluluk ayrımına sahip olduğunu, state güncelleme pattern'larına uyduğunu ve graph akışıyla uyumlu çalıştığını review sırasında doğrulamak. |
| `langgraph-patterns` | AI Development Team Orchestrator projesinde LangGraph kullanım kuralları ve pattern'ları. OrchestratorState tanımı, node yapısı, koşullu edge'ler, DAG bağımlılık yönetimi, human-in-the-loop (interrupt), SqliteSaver persistence, context inject. LangGraph kodu yazarken veya review ederken referans alınır. |
| `langgraph-subgraph` | Coder AI için — LangGraph içinde alt graf (subgraph) oluşturmak; karmaşık iş akışlarını izole modüller hâline getirmek. |
| `lazy-loading` | Coder AI için — ağır bağımlılıkları (LLM client, DB bağlantısı) sadece ilk kullanıldığında yüklemek; startup süresini kısaltmak. |
| `linter-integration` | Coder AI için — ruff ve mypy gibi araçları koda entegre etmek; lint hatalarını otomatik düzeltmek veya CI'ya eklemek. |
| `llm-context-compression` | Coder AI için — LLM'e gönderilen bağlamı token limitini aşmadan sıkıştırmak; kritik bilgiyi koruyarak özetlemek. |
| `llm-few-shot-examples` | Coder AI için — LLM prompt'una few-shot örnek eklemek; model davranışını örneklerle yönlendirmek. |
| `llm-output-parsing` | Coder AI için — LLM'den dönen ham metin veya JSON'ı güvenli şekilde parse etmek; bozuk çıktıyı tolere etmek. |
| `llm-prompt-chaining` | Coder AI için — birden fazla LLM çağrısını zincirlemek; bir çağrının çıktısını sonrakinin girdisi olarak kullanmak. |
| `llm-provider-selection` | Planner AI için — Gemini, Ollama veya OpenRouter arasında hangi provider'ın hangi görev için kullanılacağına karar vermek. |
| `llm-response-streaming` | Coder AI için — LLM yanıtını astream() ile token token okumak; uzun çıktıları kullanıcıya anlık göstermek. |
| `llm-system-prompt-management` | Coder AI için — farklı node'lar için farklı system prompt'ları yönetmek; prompt versiyonlama ve A/B testi. |
| `llm-temperature-tuning` | Coder AI için — LLM temperature ayarını görev tipine göre doğru değere ayarlamak; kod üretimi için düşük, yaratıcı metin için yüksek temperature. |
| `llm-tool-use-pattern` | Coder AI için — LangChain/Anthropic tool use ile LLM'e araç tanımlamak; fonksiyon çağrısını yapılandırılmış olarak almak. |
| `logging-patterns` | Coder AI için — structlog veya standart logging ile tutarlı log mesajları yazmak; debug, info, warning, error seviyelerini doğru kullanmak. |
| `logging-usage-review` | Planner AI için — log seviyelerinin doğru kullanıldığını, API key gibi hassas verinin log'a düşmediğini ve log mesajlarının yeterince bilgi içerdiğini review sırasında kontrol etmek. |
| `magic-number-review` | Planner AI için — kodun içindeki anlamsız sayısal ve string sabitlerini tespit etmek; bunları isimlendirilmiş sabit veya config değerine dönüştürmek. |
| `message-bus-design` | Coder AI için — EventBus'un pub/sub mesaj iletimini tasarlamak ve implemente etmek; topic tabanlı mesajlaşma, handler kayıt ve async dispatch. |
| `migration-strategy` | Planner AI için — mevcut DB şemasına yeni sütun veya tablo eklenirken migration stratejisini planlamak; veri kaybını önlemek. |
| `mock-event-bus` | Coder AI için — test sırasında gerçek EventBus yerine mock kullanmak; event emit'lerin doğrulandığı izole testler yazmak. |
| `mock-llm-response` | Coder AI için — test sırasında gerçek LLM API çağrısı yapmadan sahte yanıt döndürmek; AsyncMock ile provider mock'lama. |
| `mock-repository-pattern` | Coder AI için — testlerde gerçek DB yerine AsyncMock tabanlı repository mock'u kullanmak; DB olmadan unit test yazmak. |
| `mode-transition-detection` | Planner AI için — pm-mode'un 5 modu arasında (SOHBET, PLANLAMA, GÖREV, REVIEW, ONAY-BEKLE) doğru geçiş zamanını tespit etmek. |
| `model-fallback-chain` | Coder AI için — birincil LLM model başarısız olduğunda yedek modellere sırayla geçiş yapmak. |
| `module-boundary-validation` | Planner AI için — kod review sırasında her modülün kendi sorumluluğu dışına çıkıp çıkmadığını kontrol etmek; katman ihlallerini tespit etmek. |
| `multi-model-routing` | Coder AI için — görev tipine ve karmaşıklığa göre farklı LLM modellerine otomatik yönlendirme yapmak; maliyet-kalite dengesini optimize etmek. |
| `multi-project-support` | Planner AI için — aynı agent instance'ının birden fazla projeyi eş zamanlı yönetmesini sağlamak; project_id ile izolasyon. |
| `multi-sprint-backlog` | Planner AI için — birden fazla sprint için backlog tutmak; önceliklendirme ve sıradaki sprint seçimi. |
| `multi-sprint-roadmap-design` | Planner AI için — büyük bir projeyi veya özellik setini birden fazla sprint'e bölmek; hangi sprint'in hangisinden önce gelmesi gerektiğini belirlemek ve uzun vadeli yol haritası çıkarmak. |
| `multi-turn-context-preservation` | Planner AI için — çok turlu konuşmalarda bağlamı korumak; kullanıcının önceki mesajlarını, alınan kararları ve mevcut plan durumunu doğru takip etmek. |
| `mvp-identification` | Planner AI için — bir özellik veya proje için minimum çalışan ve değer üreten seti belirlemek; fazla mühendislik yapmadan işlevselliği teslim etmek. |
| `node-error-boundary` | Coder AI için — LangGraph node'larını hata sınırıyla sarmak; node hatası grafı çökermesin. |
| `node-function-signature` | Coder AI için — LangGraph node fonksiyonlarının doğru imzası, state okuma/yazma pattern'ı ve event emit entegrasyonu. |
| `node-output-validation` | Coder AI için — LangGraph node'unun döndürdüğü state update'ini doğrulamak; zorunlu alanların mevcut ve doğru tipte olduğunu kontrol etmek. |
| `non-functional-requirement-extraction` | Planner AI için — kullanıcının söylemediği ama sistemin karşılaması gereken performans, güvenlik, güvenilirlik ve ölçeklenebilirlik gereksinimlerini ortaya çıkarmak. |
| `notification-abstraction` | Coder AI için — Telegram ve CLI gibi farklı bildirim kanallarını soyutlayan ortak interface yazmak; kanal değişimini kolaylaştırmak. |
| `output-formatting` | Planner AI için — kullanıcıya sunulan mesajları tutarlı, okunabilir formatta yazmak; PM mod etiketleri ve yapısal düzeni korumak. |
| `output-schema-validation` | Coder AI için — LLM çıktısının beklenen JSON şemasına uygunluğunu doğrulamak; hatalı yapıyı erken yakalamak. |
| `parallel-task-identification` | Planner AI için — bağımsız görevleri tespit ederek aynı anda birden fazla worker'a atanabilecek işleri belirlemek ve sprint süresini kısaltmak. |
| `parametrize-test-cases` | Coder AI için — pytest.mark.parametrize ile aynı test mantığını farklı input/output kombinasyonlarıyla çalıştırmak. |
| `partial-sprint-recovery` | Coder AI için — daemon restart sonrasında yarım kalan sprint'i checkpoint'ten okuyarak kaldığı yerden devam ettirme mantığını implemente etmek. |
| `planner-memory` | Planner AI için — kullanıcı tercihlerini, geçmiş kararları ve proje özelliklerini kısa vadeli bellekte tutmak. |
| `planner-node-implementation` | Coder AI için — LangGraph planner node'unu implemente etmek; kullanıcı isteğini sprint görevlerine ve dosya listesine dönüştürmek. |
| `plugin-architecture` | Coder AI için — yeni LLM provider, bildirim kanalı veya storage backend'i plugin olarak ekleyebilmek; genişletilebilir mimari tasarlamak. |
| `pm-mode` | AI Development Team Orchestrator projesinde Claude'un proje yöneticisi olarak davranma kuralı. Projeyi planlar, Codex'e görev prompt'ları üretir, çıktıları review eder, kullanıcıya onay sunar. [SOHBET], [PLANLAMA], [GÖREV], [REVIEW], [ONAY-BEKLE] modlarıyla çalışır. Bu projeyi geliştirirken her mimari karar, görev dağılımı ve review sürecinde bu skill kullanılır. |
| `priority-ordering` | Planner AI için — görevleri ve sprint'leri değer, bağımlılık ve risk faktörlerine göre sıralamak; önce en kritik işi yapmak. |
| `progress-report-generation` | Planner AI için — sprint boyunca tamamlanan ve bekleyen görevlerin özetini çıkarmak; kullanıcıya net ilerleme raporu sunmak. |
| `project-architecture` | AI Development Team Orchestrator projesinin klasör yapısı, mimari kuralları, dosya sınırları, naming convention ve state şeması. Her kodlama görevinde ve review sürecinde referans alınır. Mimari kararlar bu skill'e göre verilir. |
| `project-file-structure` | Coder AI için — Python projesinin standart dosya ve dizin yapısını bilmek; yeni dosyaları doğru konuma yerleştirmek. |
| `project-initialization-workflow` | Planner AI için — yeni proje oluşturma isteğinde proje kaydını DB'ye eklemek, ilk sprint hazırlığını yapmak ve kullanıcıyı karşılamak. |
| `prompt-construction-pattern` | Coder AI için — LLM provider'a gönderilecek system + user + context prompt'unu bu projeye özgü standart biçimde oluşturma. |
| `prompt-template-construction` | Coder AI için — LLM'e gönderilecek prompt'u system/human mesajı ayrımıyla doğru yapıda oluşturmak; context injection yapmak. |
| `prompt-versioning` | Planner AI için — LLM prompt'larını versiyonlamak; hangi prompt değişikliğinin hangi sonucu ürettiğini takip etmek. |
| `proto-typing` | Coder AI için — tam implementasyon öncesinde hızlı çalışan prototip yazmak; doğrulama sonrası production kalitesine yükseltmek. |
| `provider-cost-tracking` | Coder AI için — LLM provider kullanım maliyetini token başına hesaplamak ve sprint toplam maliyetini raporlamak. |
| `provider-fallback-chain` | Coder AI için — LLM provider fallback zincirini (Ollama → OpenRouter Primary → Secondary → Stub) doğru implemente etmek; her provider'ın bağımsız denemesi ve hata yönetimi. |
| `pydantic-model-review` | Planner AI için — Pydantic v2 model tanımlarının doğru alanlar, tipler ve validator'lar içerdiğini; proje veri modelleriyle tutarlı olduğunu review sırasında doğrulamak. |
| `pydantic-settings-definition` | Coder AI için — BaseSettings ile .env tabanlı konfigürasyon tanımlamanın bu projedeki doğru yolu; yeni alan ekleme, computed property ve validation. |
| `pydantic-v2-model-definition` | Coder AI için — bu projede Pydantic v2 ile model tanımlamanın doğru yolu; field tanımları, validator'lar, enum entegrasyonu ve JSON serialization. |
| `pytest-async-test` | Coder AI için — pytest ile async fonksiyon ve LangGraph node'larını test etme; asyncio mark, fixture ve mock kullanımı. |
| `python-async-patterns` | AI Development Team Orchestrator projesinde kullanılan Python async pattern'ları. EventBus tasarımı, asyncio kuralları, daemon yapısı, concurrent task yönetimi, crash recovery. Async kod yazarken veya review ederken referans alınır. |
| `python-packaging` | Coder AI için — pyproject.toml ile Python paketini doğru yapılandırmak; bağımlılıkları, entry point'leri ve geliştirme araçlarını tanımlamak. |
| `queue-entry-construction` | Coder AI için — dispatcher'ın worker'a gönderdiği iş kuyruğu girişini (QueueEntry) doğru alanlarla oluşturmak. |
| `rate-limit-handling` | Coder AI için — LLM provider'lardan gelen 429 rate limit hatalarını tespit etmek, exponential backoff ile yeniden denemek ve farklı provider'a geçmek. |
| `rejection-handling` | Planner AI için — kullanıcının planı reddetmesi durumunda gerekçeyi analiz etmek, planı revize etmek ve yeni onay döngüsünü başlatmak. |
| `requirement-conflict-detection` | Planner AI için — birbiriyle çelişen gereksinimleri tespit etmek, önceliklendirmek ve kullanıcıyla çözüme kavuşturmak. |
| `resource-cleanup-review` | Planner AI için — DB connection, HTTP client, dosya handle, asyncio task gibi kaynakların düzgün kapatıldığını ve sızdırılmadığını review sırasında kontrol etmek. |
| `response-caching` | Coder AI için — tekrarlayan LLM sorgularının yanıtlarını önbelleğe almak; aynı prompt için ikinci kez LLM çağrısı yapmamak. |
| `retry-decision-logic` | Coder AI için — bir görev başarısız olduğunda yeniden deneme yapılıp yapılmayacağına ve nasıl yapılacağına karar veren mantığı implemente etmek. |
| `retry-decorator-implementation` | Coder AI için — async fonksiyon için yapılandırılabilir retry decorator yazma; exponential backoff, retryable exception filtresi ve max attempt. |
| `retry-with-jitter` | Coder AI için — exponential backoff'a rastgele jitter (gürültü) ekleyerek thundering herd sorununu önlemek; birden fazla worker'ın aynı anda retry yapmasını engellemek. |
| `review-cycle-limit-enforcement` | Planner AI için — reviewer → dispatcher döngüsünün sonsuz tekrarlamasını engellemek; maksimum review cycle sayısını aşınca sprint'i başarısız olarak işaretlemek. |
| `reviewer-node-implementation` | Coder AI için — LangGraph reviewer node'unu implemente etmek; üretilen kodu LLM ile değerlendirerek geç/kalma kararı vermek. |
| `rollback-strategy` | Planner AI için — başarısız sprint sonrası yazılan dosyaların geri alınmasını planlamak; sistemin önceki çalışan durumuna dönmesini sağlamak. |
| `schema-first-design` | Coder AI için — implementasyona başlamadan önce Pydantic modelleri ve DB şemasını tasarlamak; kontrat önce, implementasyon sonra. |
| `scope-boundary-detection` | Planner AI için — bir isteğin neyi kapsadığını ve neyi kapsamadığını net olarak tanımlamak; scope creep ve belirsiz genişlemeyi engellemek. |
| `scope-creep-detection` | Planner AI için — konuşma sırasında veya sprint ilerlerken kapsamın fark edilmeden genişlemesini tespit etmek ve durdurmak. |
| `sentinel-value-pattern` | Coder AI için — None ile ayırt edilemeyen "değer yok" durumları için sentinel nesneleri tanımlamak; Optional'ın yetersiz kaldığı durumlarda kullanmak. |
| `sequential-constraint-enforcement` | Planner AI için — mutlaka sıralı çalışması gereken görevlerin bağımlılık kısıtlarını belirlemek ve dispatcher'ın bu sıralamaya uymasını sağlamak. |
| `settings-validation` | Coder AI için — uygulama başlarken zorunlu environment variable'ların mevcut ve geçerli olduğunu doğrulamak; eksik config'i erken bildirmek. |
| `signal-handler-setup` | Coder AI için — SIGTERM ve SIGINT sinyallerini yakalayarak daemon'ı temiz kapatan signal handler'ları kurmak. |
| `single-responsibility-enforcement` | Coder AI için — her modül, sınıf ve fonksiyonun tek bir sorumluluğa sahip olmasını sağlamak; birden fazla işi yapan bileşenleri tespit ve ayırmak. |
| `sprint-abort-on-critical-failure` | Planner AI için — kritik hata oluştuğunda devam etmek yerine sprinti temiz şekilde durdurmak. |
| `sprint-acceptance-testing` | Planner AI için — sprint sonu kabul testlerini tanımlamak ve çalıştırmak; kullanıcı hikayelerinin gerçeklendiğini doğrulamak. |
| `sprint-adaptive-planning` | Planner AI için — sprint sırasında gelen yeni bilgiye göre planı dinamik olarak güncellemek; sabit plan yerine uyarlanabilir yaklaşım. |
| `sprint-approval-gate` | Planner AI için — sprint başlamadan veya kritik bir adımda kullanıcı onayı beklemek; onay gelmezse harekete geçmemek. |
| `sprint-approval-history` | Planner AI için — hangi sprint'lerin onaylandığını, reddedildiğini ve ne zaman onaylandığını sorgulamak; audit trail sağlamak. |
| `sprint-audit-log` | Planner AI için — sprint boyunca yapılan tüm kritik işlemleri değiştirilemez denetim kaydına yazmak. |
| `sprint-auto-continuation` | Planner AI için — tamamlanan sprintten sonra kullanıcı müdahalesi olmadan bir sonraki sprintin otomatik başlatılması. |
| `sprint-blocker-resolution` | Planner AI için — sprint'i engelleyen teknik veya organizasyonel blocker'ları tespit etmek ve çözüm önerileri sunmak. |
| `sprint-budget-estimation` | Planner AI için — bir sprint'in tahmini süresini ve karmaşıklığını değerlendirmek; kullanıcıya gerçekçi beklenti sunmak. |
| `sprint-cancellation` | Planner AI için — aktif sprint'in kullanıcı isteğiyle veya hata durumunda iptal edilmesi; kaynakların temizlenmesi ve durumun kaydedilmesi. |
| `sprint-capacity-planning` | Planner AI için — mevcut kaynakları (worker sayısı, LLM kapasitesi) göz önünde bulundurarak sprint hacmini belirlemek. |
| `sprint-checklist` | Planner AI için — sprint başlatmadan önce tüm ön koşulların karşılandığını kontrol eden başlangıç kontrol listesi. |
| `sprint-clone` | Planner AI için — başarılı bir sprint'i şablon olarak kullanarak benzer yeni sprint oluşturmak; sıfırdan planlamayı atlamak. |
| `sprint-completion-celebration` | Planner AI için — sprint başarıyla tamamlandığında kullanıcıya özet sunan ve sonraki adımı soran kapanış mesajı yazmak. |
| `sprint-completion-validation` | Planner AI için — bir sprint'in gerçekten tamamlanıp tamamlanmadığını doğrulamak; tüm dosyaların yazıldığını, validation geçtiğini ve bir sonraki sprint'e geçilebileceğini kontrol etmek. |
| `sprint-configuration-profile` | Planner AI için — farklı kullanım senaryoları için hazır sprint konfigürasyon profilleri tanımlamak (hızlı, kapsamlı, güvenli). |
| `sprint-conflict-resolution` | Planner AI için — aynı dosyayı düzenleyen iki görevi tespit edip çakışmayı çözmek; paralel yazım çakışmalarını önlemek. |
| `sprint-constraint-solver` | Planner AI için — sprint kısıtlamalarını (süre, worker, token) göz önüne alarak gerçekçi görev seçimi yapmak. |
| `sprint-context-window-management` | Planner AI için — uzun sprint boyunca LLM bağlam penceresini yönetmek; önemli bilgiyi sıkıştırarak taşımak. |
| `sprint-continuous-improvement` | Planner AI için — her sprint döngüsünden elde edilen içgörülerle sistemi sürekli iyileştirmek; retrospective bulgularını otomatik uygulamak. |
| `sprint-decision-gate` | Planner AI için — sprint belirli bir noktaya geldiğinde devam/dur kararını verilen kriterlere göre otomatik almak. |
| `sprint-dependencies-update` | Coder AI için — sprint sırasında yeni Python bağımlılıkları tespit etmek ve pyproject.toml / requirements.txt'e otomatik eklemek. |
| `sprint-dependency-graph` | Planner AI için — sprint görevleri arasındaki bağımlılıkları yönlü çizge olarak temsil etmek ve döngü tespit etmek. |
| `sprint-dependency-management` | Planner AI için — sprint'ler arası bağımlılıkları yönetmek; Sprint 2'nin Sprint 1'in sonuçlarına bağlı olduğunu kullanıcıya açıklamak. |
| `sprint-diff-report` | Planner AI için — sprint öncesi ve sonrası dosya değişikliklerini karşılaştıran rapor oluşturmak. |
| `sprint-dry-run` | Planner AI için — sprint planını gerçek kod yazmadan simüle etmek; tahmini süre, kaynak kullanımı ve olası sorunları önceden görmek. |
| `sprint-emergency-stop` | Planner AI için — kritik sorun anında tüm sistemi anında durdurmak; veri bütünlüğünü koruyarak acil kapanış yapmak. |
| `sprint-export` | Planner AI için — sprint planını ve sonuçlarını JSON veya Markdown formatında dışa aktarmak; arşivleme ve paylaşım için. |
| `sprint-feedback-loop` | Planner AI için — sprint sonuçlarından öğrenerek bir sonraki sprint planlamasını iyileştirmek. |
| `sprint-full-report` | Planner AI için — sprint sonunda hedef, metrikler, dosyalar, notlar ve öğrenilen dersleri tek kapsamlı raporda birleştirmek. |
| `sprint-gantt-view` | Planner AI için — sprint görevlerini basit ASCII Gantt şeması olarak görselleştirmek; zaman çizelgesini sohbet ekranında göstermek. |
| `sprint-goal-articulation` | Planner AI için — her sprint için tek cümlelik net bir hedef ve başarı tanımı yazmak; ekibin ne yapmaya çalıştığını herkesin anlayacağı şekilde ifade etmek. |
| `sprint-goal-clarification` | Planner AI için — belirsiz sprint hedefini netleştirmek için kullanıcıya odaklı sorular sormak ve yanıtları entegre etmek. |
| `sprint-goal-decomposition` | Planner AI için — yüksek seviyeli sprint hedefini somut, eyleme geçirilebilir görevlere parçalamak. |
| `sprint-goal-tracking` | Planner AI için — sprint boyunca hedefin hâlâ geçerli olup olmadığını izlemek; kapsam değişikliğinde hedefi güncellemek. |
| `sprint-goal-validation` | Planner AI için — sprint hedefinin somut, ölçülebilir ve tek sprint'e sığar olduğunu doğrulamak; belirsiz hedefleri reddetmek. |
| `sprint-handoff-protocol` | Planner AI için — bir sprint bittikten sonra sonraki sprinte veya başka bir sisteme kontrol devrederken gerekli bilgiyi aktarmak. |
| `sprint-history-query` | Planner AI için — tamamlanan sprint'lerin geçmişini sorgulamak; önceki kararları ve sonuçları yeni sprint planında bağlam olarak kullanmak. |
| `sprint-impact-analysis` | Planner AI için — bir görev veya değişikliğin diğer modülleri nasıl etkileyeceğini önceden analiz etmek. |
| `sprint-interruption-handling` | Planner AI için — kullanıcının sprint ortasında gönderdiği yeni isteği veya değişikliği işlemek; çalışan sprinti güvenli şekilde duraklatmak. |
| `sprint-iteration-management` | Planner AI için — sprint içinde iterasyonları yönetmek; başarısız dosyaları sonraki iterasyona taşımak. |
| `sprint-knowledge-base` | Planner AI için — sprint boyunca öğrenilen teknik bilgileri, çözülen sorunları ve en iyi pratikleri erişilebilir bir bilgi tabanında saklamak. |
| `sprint-kpi-dashboard` | Planner AI için — sprint performans göstergelerini (KPI) hesaplamak ve özet dashboard formatında sunmak. |
| `sprint-lifecycle-state-machine` | Planner AI için — bir sprint'in tüm yaşam döngüsü durumlarını (draft → active → review → done/cancelled) yönetmek; geçersiz geçişleri engellemek. |
| `sprint-metrics-collection` | Planner AI için — sprint boyunca üretilen kod kalitesi, süre ve hata oranı gibi metrikleri toplamak; iyileştirme kararlarına veri sağlamak. |
| `sprint-milestone-tracking` | Planner AI için — sprint içinde kritik dönüm noktalarını (milestone) tanımlamak ve ulaşıldığında bildirmek. |
| `sprint-multi-agent-coordination` | Planner AI için — birden fazla AI ajanın (planner + coder) koordinasyonunu yönetmek; görev dağılımı ve iletişim protokolü. |
| `sprint-multi-goal` | Planner AI için — tek sprint'te birden fazla hedefi yönetmek; her hedef için ayrı görev grubu oluşturmak. |
| `sprint-note-taking` | Planner AI için — sprint boyunca önemli gözlemleri, kararları ve öğrenilen dersleri kısa notlar olarak kaydetmek. |
| `sprint-notification-channels` | Planner AI için — sprint bildirimlerini farklı kanallara (CLI, Telegram, log) yönlendirmek; kanal seçimini yapılandırılabilir tutmak. |
| `sprint-observability` | Planner AI için — sprint sistemine gözlemlenebilirlik eklemek; metrik, log ve trace üçgenini kurarak sorunları hızlı tespit etmek. |
| `sprint-onboarding-guide` | Planner AI için — yeni kullanıcıyı sisteme tanıştırmak; ilk sprint için adım adım rehber sunmak. |
| `sprint-parallel-execution` | Planner AI için — bağımsız görevleri paralel worker'lara dağıtarak sprint süresini kısaltmak. |
| `sprint-pause-resume` | Planner AI için — aktif sprint'i geçici olarak durdurmak ve daha sonra kaldığı yerden devam ettirmek; HITL checkpoint mekanizmasını kullanmak. |
| `sprint-plan-revision` | Planner AI için — kullanıcı planı reddettiğinde geri bildirimi analiz ederek revize edilmiş plan oluşturmak; önceki hatayı tekrarlamamak. |
| `sprint-priority-matrix` | Planner AI için — birden fazla bekleyen özellik isteği varsa önceliklendirme matrisiyle hangi sprint'in önce yapılacağına karar vermek. |
| `sprint-progress-persistence` | Coder AI için — sprint ilerleme verilerini düzenli aralıklarla DB'ye yazmak; uygulama yeniden başlasa da devam edilebilsin. |
| `sprint-project-template` | Planner AI için — yaygın proje türleri için hazır sprint şablonları sunmak; FastAPI, CLI araç, LangGraph agent başlangıç konfigürasyonları. |
| `sprint-quick-win` | Planner AI için — sprint planında 5-10 dakikada tamamlanabilecek kolay görevleri önce sıralamak; hızlı momentum kazanmak. |
| `sprint-release-notes` | Planner AI için — tamamlanan sprint'ten kullanıcıya sunmak üzere sürüm notları oluşturmak. |
| `sprint-resource-limits` | Planner AI için — sprint boyunca kaynak kullanımını (token, süre, dosya sayısı) sınırlamak ve aşım durumunda uyarmak. |
| `sprint-restart` | Planner AI için — başarısız veya iptal edilmiş sprint'i yeni planla yeniden başlatmak; eski state'i temizleyip taze başlangıç yapmak. |
| `sprint-review-checklist` | Planner AI için — sprint tamamlanmadan önce gözden geçirilmesi gereken maddelerin kontrol listesi. |
| `sprint-risk-register` | Planner AI için — sprint boyunca tespit edilen riskleri kayıt altında tutmak; her riske önlem ve sahip atamak. |
| `sprint-rollup-metrics` | Planner AI için — birden fazla sprintin metriklerini toplayarak proje düzeyinde istatistik üretmek. |
| `sprint-scope-creep-detection` | Planner AI için — sprint sırasında kapsam genişlemesini (scope creep) tespit edip kullanıcıyı uyarmak. |
| `sprint-scope-negotiation` | Planner AI için — sprint kapsamı konusunda kullanıcıyla müzakere etmek; çok büyük isteği bölerek veya küçük isteği zenginleştirerek doğru boyuta getirmek. |
| `sprint-search` | Planner AI için — geçmiş sprint kayıtlarında tam metin arama yapmak; benzer görevleri veya eski kararları bulmak. |
| `sprint-size-estimation` | Planner AI için — bir sprint'in kaç dosya, kaç görev ve tahminen ne kadar süreceğini belirlemek; aşırı büyük veya anlamsız küçük sprint'leri önlemek. |
| `sprint-stakeholder-update` | Planner AI için — sprint ilerlemesini paydaşlara (kullanıcıya) anlaşılır dilde düzenli raporlamak. |
| `sprint-summary-generation` | Planner AI için — sprint tamamlandığında ne yapıldığını, hangi dosyaların değiştiğini ve kullanıcının artık neler yapabileceğini özetleyen kısa bir rapor oluşturmak. |
| `sprint-tag-system` | Planner AI için — sprint'leri etiketleyerek (feature, bugfix, refactor, test) filtreleme ve raporlama yapmak. |
| `sprint-task-splitting` | Planner AI için — tahmini süresi fazla olan büyük görevi otomatik olarak daha küçük alt görevlere bölmek. |
| `sprint-team-collaboration` | Planner AI için — birden fazla kullanıcının aynı proje üzerinde çalıştığı senaryolarda sprint koordinasyonu. |
| `sprint-template-library` | Planner AI için — sık tekrar eden sprint türleri için hazır şablonlar bulundurmak; "repository katmanı ekle" gibi istekleri şablondan hızla planlamak. |
| `sprint-time-boxing` | Planner AI için — sprint'e sabit süre sınırı koymak; süre dolduğunda tamamlanmamış görevleri gelecek sprinte ertelemek. |
| `sprint-type-selection` | Planner AI için — bir işin "contract" sprint mi yoksa "feature" sprint mi olacağını belirlemek; sprint türüne göre planlama stratejisini ayarlamak. |
| `sprint-user-story-mapping` | Planner AI için — kullanıcı hikayelerini sprint'e dönüştürmek; "kullanıcı olarak X istiyorum" formatını görevlere çevirmek. |
| `sprint-velocity-tracking` | Planner AI için — sprint hızını (velocity) ölçmek; her sprint kaç dosya/görev tamamladığını takip ederek ileriki sprints için gerçekçi tahmin yapmak. |
| `sprint-what-if-analysis` | Planner AI için — "şu olursa ne olur?" sorusunu sprint planına uygulamak; risk senaryolarını simüle etmek. |
| `sprint-work-breakdown` | Planner AI için — sprint görevlerini WBS (Work Breakdown Structure) hiyerarşisinde organize etmek; epic → story → task ağaç yapısı. |
| `stall-detection-response` | Planner AI için — sistemin takılı kaldığını (heartbeat gelmiyor, progress yok) tespit etmek ve uygun aksiyonu almak. |
| `state-builder-for-tests` | Coder AI için — LangGraph node testleri için hazır, eksiksiz OrchestratorState nesneleri oluşturma; farklı senaryolar için state builder fonksiyonları. |
| `state-initialization` | Coder AI için — LangGraph graph'ı ilk başlatırken OrchestratorState'in zorunlu alanlarını doğru başlangıç değerleriyle hazırlamak. |
| `state-machine-design-review` | Planner AI için — OrchestratorState, sprint lifecycle ve dosya status state machine'lerinin doğru tasarlandığını ve geçişlerin geçerli olduğunu review sırasında doğrulamak. |
| `state-migration` | Coder AI için — OrchestratorState TypedDict'e yeni alan eklendiğinde mevcut checkpoint'lerdeki eski state'i uyumlu hale getirmek. |
| `state-persistence-recovery` | Coder AI için — LangGraph state'ini kalıcı depolamaya yazmak ve çöküş sonrası geri yüklemek. |
| `state-snapshot-diff` | Coder AI için — iki LangGraph state snapshot arasındaki farkı göstermek; hangi alanların değiştiğini takip etmek. |
| `state-typeddict-definition` | Coder AI için — LangGraph OrchestratorState TypedDict şemasına yeni alan eklemenin ve mevcut alanları düzenlemenin doğru yolu. |
| `state-update-return-pattern` | Coder AI için — LangGraph node'larının sadece değişen state alanlarını döndürme pattern'ı; tam state kopyalama ve mutation'dan kaçınma. |
| `streaming-response-handling` | Coder AI için — LLM streaming yanıtını (astream) işlemek; token token gelen yanıtı birleştirmek ve gerçek zamanlı çıktı göstermek. |
| `structured-error-logging` | Coder AI için — hata log'larını `extra` dict ile yapılandırmak; grep edilebilir, izlenebilir ve context-rich log kayıtları oluşturmak. |
| `structured-logging-context` | Coder AI için — log kayıtlarına yapısal bağlam (sprint_id, worker_id, task_id) eklemek; filtrelenebilir log üretmek. |
| `structured-output-schema` | Coder AI için — LangChain with_structured_output ile LLM'den doğrudan Pydantic modeli almak; JSON parse adımını ortadan kaldırmak. |
| `subprocess-async` | Coder AI için — asyncio.create_subprocess_exec veya asyncio.create_subprocess_shell ile harici komutları async olarak çalıştırmak. |
| `task-context-enrichment` | Coder AI için — görev yürütmeden önce ilgili dosya içeriklerini, bağımlılıkları ve proje bağlamını görev nesnesine eklemek. |
| `task-dependency-ordering` | Planner AI için — sprint görevleri arasındaki bağımlılıkları belirleyerek doğru çalışma sırasını oluşturmak; bağımlı görevin öncekinden önce başlamasını önlemek. |
| `task-estimation-calibration` | Planner AI için — geçmiş sprint verilerine göre görev süresi tahminlerini kalibre etmek; tutarlı ve gerçekçi beklenti yönetimi yapmak. |
| `task-granularity-calibration` | Planner AI için — Coder AI'a verilen görevlerin ne çok büyük ne de çok küçük olduğunu garantilemek; doğru boyutlandırma ile tek seferde başarıyla tamamlanabilir görevler üretmek. |
| `task-retry-policy` | Planner AI için — her görev için ayrı retry politikası tanımlamak; hangi hatalar yeniden denenecek, kaç kez, ne kadar bekleyerek. |
| `task-status-update` | Coder AI için — görev durumunu (pending/in_progress/done/failed) OrchestratorState içinde güncellemek; görev bazlı ilerleme takibi yapmak. |
| `technical-debt-logging` | Planner AI için — sprint sırasında ertelenen işleri, bilinen eksiklikleri ve iyileştirme fırsatlarını kayıt altına almak; teknik borç birikimini izlemek. |
| `technical-feasibility-check` | Planner AI için — kullanıcının istediği şeyin mevcut mimari, bağımlılıklar ve kısıtlar çerçevesinde yapılabilir olup olmadığını değerlendirmek. |
| `telegram-bot-patterns` | AI Development Team Orchestrator projesinde Telegram bot ve CLI arayüzü entegrasyon kuralları. python-telegram-bot async yapısı, EventBus entegrasyonu, Flow resume pattern'ı, onay mekanizması, CLI Textual yapısı. Telegram veya CLI kodu yazarken referans alınır. |
| `telegram-command-handler` | Coder AI için — python-telegram-bot ile Telegram komutlarını (/start, /status, /approve) işleyen handler'lar yazmak. |
| `telemetry-logging` | Coder AI için — LLM çağrılarının süresini, token kullanımını ve sonucunu loglayarak maliyet ve performans takibi yapmak. |
| `test-coverage-reporting` | Coder AI için — pytest-cov ile test kapsamı raporunu çalıştırmak; düşük kapsama sahip modülleri tespit etmek. |
| `test-data-builder` | Coder AI için — test verisi üretmek için builder pattern kullanmak; her test için temiz, izole veri oluşturmak. |
| `test-isolation` | Coder AI için — testlerin birbirinden bağımsız çalışmasını sağlamak; paylaşılan state, global singleton ve DB kalıntılarının testleri etkilemesini önlemek. |
| `test-strategy-planning` | Planner AI için — bir sprint için hangi testlerin yazılacağına karar vermek; unit, integration ve smoke test ihtiyaçlarını belirlemek. |
| `thread-config-management` | Coder AI için — LangGraph thread ID'lerini proje başına yönetme, thread-config mapping ve birden fazla projenin aynı anda izolasyonu. |
| `thread-config-usage` | Coder AI için — LangGraph thread konfigürasyonunu doğru oluşturmak ve checkpointer'ın doğru thread'i bulmasını sağlamak. |
| `token-budget-management` | Planner AI için — her sprint için LLM token bütçesini takip etmek; aşırı tüketimi erkenden tespit edip optimize etmek. |
| `type-alias-definition` | Coder AI için — karmaşık tip ifadelerini okunabilir tip alias'larıyla basitleştirmek; kodun self-documenting olmasını sağlamak. |
| `type-hint-completeness-review` | Planner AI için — Coder AI çıktısında tüm fonksiyon parametrelerinin ve dönüş tiplerinin type hint ile annotate edildiğini review sırasında kontrol etmek. |
| `type-narrowing-patterns` | Coder AI için — Python type system'inde tür daraltma (type narrowing) kalıplarını uygulamak; mypy uyumlu kod yazmak. |
| `upsert-pattern` | Coder AI için — SQLite'ta "var ise güncelle, yok ise ekle" operasyonunun doğru yolu; INSERT OR REPLACE ve ON CONFLICT DO UPDATE kullanımı. |
| `user-feedback-collection` | Planner AI için — sprint tamamlandıktan sonra kullanıcıdan kalite geri bildirimi almak; gelecek sprint'leri iyileştirmek için. |
| `user-intent-clarification` | Planner AI için — kullanıcının ne istediği net olmadığında doğru soruyu sormak; tek soru ile maksimum bilgi toplamak. |
| `user-story-decomposition` | Planner AI için — büyük kullanıcı isteklerini ve epikleri, Coder AI'ın uygulayabileceği küçük, bağımsız görevlere bölmek. |
| `user-story-to-task` | Planner AI için — kullanıcı hikayesini ("Kullanıcı olarak X yapabilmek istiyorum") teknik görevlere dönüştürmek. |
| `vague-requirement-clarification` | Planner AI için — kullanıcının belirsiz veya eksik isteklerini net gereksinimlere dönüştürmek amacıyla doğru soruları sormak ve netlik kazandırmak. |
| `validator-node-implementation` | Coder AI için — LangGraph validator node'unu implemente etmek; üretilen dosyaların syntax doğruluğunu ve temel kural uyumunu otomatik kontrol etmek. |
| `worker-assignment-strategy` | Planner AI için — hangi dosyanın hangi worker'a atanacağına karar vermek; önceliklendirme ve yük dengeleme. |
| `worker-concurrency-control` | Coder AI için — paralel çalışan worker sayısını asyncio.Semaphore ile sınırlamak; sistem kaynaklarını aşırı yüklemeden korumak. |
| `worker-failure-triage` | Planner AI için — worker başarısızlığını analiz etmek; retryable mı, kalıcı mı, hangi worker'a atanacak, ne yapılacak kararını vermek. |
| `worker-graceful-shutdown` | Coder AI için — worker'ları aniden kesmek yerine mevcut görevi bitirip temiz kapanmalarını sağlamak. |
| `worker-heartbeat` | Coder AI için — aktif worker'ların canlılığını izlemek; yanıt vermeyen worker'ları tespit edip sistemi uyarmak. |
| `worker-idle-detection` | Coder AI için — atanmış görevi olmayan boşta bekleyen worker'ları tespit edip yeni görev atamak veya kapatmak. |
| `worker-load-balancing-strategy` | Planner AI için — görevleri worker_a, worker_b, worker_c arasında dengeli ve çakışmasız şekilde dağıtmak. |
| `worker-node-implementation` | Coder AI için — LangGraph worker node'unu implemente etmek; LLM ile kod üretip diske yazarak file_registry'yi güncellemek. |
| `worker-queue-overflow` | Coder AI için — worker kuyruğu dolduğunda taşmayı yönetmek; yeni görevleri reddetmek veya bekletmek. |
| `worker-result-aggregation` | Coder AI için — paralel worker'lardan gelen sonuçları toplayıp birleştirmek; eksik veya hatalı sonuçları işlemek. |
| `worker-status-tracking` | Coder AI için — aktif worker'ların durumunu (idle/busy/failed) OrchestratorState içinde takip etmek; kapasite yönetimi için worker sayısını güncel tutmak. |
| `workflow-visualization` | Planner AI için — sprint akışını ve görev bağımlılıklarını ASCII veya Mermaid diyagramıyla görselleştirerek kullanıcıya sunmak. |

---

*Bu dosya otomatik oluşturulmuştur. Son güncelleme: 2026-05-03*
