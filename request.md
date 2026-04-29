# User Request Memory (Canonical)

Bu dosya, projenin ana hedefini ileride birebir hatırlamak ve kapsam kaymasını engellemek icin olusturuldu.

## Ana Hedef

Kullanicinin lokal PC'sinde, Docker icinde surekli calisan bir AI Orchestrator bulunacak. Bu orchestrator, kullanici ister CLI ister Telegram uzerinden mesaj gondersin, ayni merkezi sisteme dusen istegi yonetecek ve Gemini tabanli yonetici akil ile karar verecek.

## Beklenen Davranis

1. Sistem always-on calisir (daemon/service mantigi).
2. Iki giris kanali vardir:
   - CLI (kullanici PC basindayken)
   - Telegram (kullanici PC basinda degilken)
3. Her iki kanaldan gelen mesajlar tek orkestrasyon akisinda birlesir.
4. Varsayilan calisma modu "yonetici/planlayici" modudur:
   - Proje planlama
   - Gereksinim netlestirme
   - Gorev dagitimi
   - Durum takibi
5. Varsayilan durumda kod yazimi yapilmaz.
6. Kod yazdirma sadece acik komut/izinle aktif edilir.

## Kod Uretim Modu (Explicit Enable)

Kullanici acikca kod uretim istediginde orchestrator:

1. Sistemde tanimli API key'leri ve lokal modelleri tarar.
2. Kullanilabilir AI modellerini/calisanlari listeler.
3. Uygun role gore gorev dagitimi yapar (sub-agent mantigi).
4. Promptlari ilgili AI'lara dagitir.
5. Kod ciktisini toplar, review akisina sokar, sonucu raporlar.

## Ornek Istek (Kullanicinin hedefledigi kullanim)

"Agent, tum API key ve lokal modelleri tara, aktif kullanilabilir tum AI'lari belirle, gorevlerini dagit ve sub-agent olarak hazirla."

## Tasarim Ilkeleri

- Tek merkezli orkestrasyon
- Kanal bagimsiz komut isleme (CLI ve Telegram tutarliligi)
- Guvenli onay mekanizmasi (approval id, stale koruma, idempotency)
- Crash recovery ve kaldigi yerden devam
- Olculebilir operasyonel metrikler

## Non-Goals (Su Asamada)

- Tam otonom kod yazimi varsayilan davranis degildir.
- Kullanici onayi olmadan kritik mode switch yapilmaz.

## Not

Bu dokuman urun niyetini sabit tutmak icin "hafiza kaydi"dir. Faz bazli teknik detaylar `main-plan.md` ve `plan-phase.md` dosyalarinda yasar.
