# Fırın Yönetim Paneli — Yol Haritası (Roadmap)

## Faz 1 — Temel Altyapı (Hafta 1) ✅

### Adım 1.1: Proje İskeleti ✅
- [x] Flask uygulama başlatma (`app.py`)
- [x] SQLite veritabanı kurulumu (`models.py`)
- [x] Nothing Design token sistemi (`static/style.css`)
- [x] Ana layout şablonu (`templates/layout.html`)

### Adım 1.2: Veri Modeli & Migration ✅
- [x] 7 tablonun oluşturulması (urunler, musteriler, satislar, giderler, uretim, fire, musteri_borclari)
- [x] İlişkiler ve foreign key'ler
- [x] WAL mode aktifleştirme
- [x] Örnek verilerle test (6 ürün, 4 müşteri)

### Adım 1.3: Responsive Tema ✅
- [x] 320/375/414/768px kırılımları
- [x] Mobil navigasyon (hamburger)
- [x] Dokunmatik dostu hedef boyutlar (44px)
- [x] Kart görünümüne dönüşen tablolar
- [x] Yatay kaydırmayı engelleme (`overflow-x: clip`)

### Adım 1.4: Temel CRUD Ekranları ✅
- [x] Satış giriş formu (3 alan, müşteri/ürün seçimi, ödeme türü)
- [x] Gider giriş formu (kategori bazlı: hammadde/fatura/maaş/diğer)
- [x] Üretim giriş formu (ürün + miktar + un kullanımı)
- [x] Fire giriş formu (3 tür: üretim/bayat/dağıtım)
- [x] Müşteri ekleme/listeleme (karlılık + borç durumu)

## Faz 2 — Dashboard & Raporlar (Hafta 2) ✅

### Adım 2.1: Dashboard ✅
- [x] 4 ana metrik kartı (kar, ciro, fire, borç)
- [x] En çok satan 5 ürün paneli
- [x] Müşteri karlılık paneli
- [x] Trend okları ve karşılaştırma (↑ yeşil, ↓ kırmızı, → gri)

### Adım 2.2: Raporlama
- [ ] Aylık kar/zarar özeti
- [ ] Gider dağılımı
- [ ] Fire oranı trendi
- [ ] Müşteri borç durumu (dashboard'da temel gösterim var)
- [ ] CSV export

### Adım 2.3: Görselleştirme
- [ ] Haftalık kar/zarar grafiği
- [ ] Ürün bazlı satış dağılımı
- [ ] Fire türü dağılımı

## Faz 3 — Doğal Dil Sorgulama (Hafta 3) ✅

### Adım 3.1: Sorgu Motoru ✅
- [x] OpenAI API entegrasyonu (`query_engine.py`)
- [x] Doğal dil → SQL çevirisi (gpt-4o-mini + fallback keyword matching)
- [x] Sık sorulan sorular butonları (5 adet)
- [ ] Yanıt kaynağını gösterme

### Adım 3.2: Sorgu Arayüzü ✅
- [x] Sorgu kutusu (/sorgu sayfasında)
- [x] 3 dilde sorgu desteği
- [ ] Sorgu geçmişi

## Faz 4 — Çoklu Dil & Tema (Hafta 4) ✅

### Adım 4.1: i18n ✅
- [x] JSON dil dosyaları (TR/EN/DE)
- [x] Tarayıcı dilini algılama
- [x] Anlık dil değiştirme (header dropdown)
- [ ] Tarih/saat/para formatı

### Adım 4.2: Tema Sistemi (Nothing Design) ✅
- [x] CSS custom properties — light tokenlar (`#F5F5F5` zemin, `#FFFFFF` kart)
- [x] CSS custom properties — dark tokenlar (`#000000` OLED zemin, `#111111` kart)
- [x] Status renkleri ortak (success `#4A9E5C`, warning `#D4A843`, accent `#D71921`)
- [x] Tema geçiş butonu (header)
- [x] localStorage'da tercih saklama
- [x] 200ms ease-out transition
- [x] Dark mod: "karanlık odada enstrüman paneli" hissi

## Yeni Faz 2.5 — Ağrı Noktaları Çözümleri (Board Kararları)

### 🎯 Tespit: 5 Yeni Ağrı Noktası

| # | Ağrı Noktası | Kullanıcı Sesi | Çözüm |
|---|-------------|----------------|-------|
| 1 | **Ürün CRUD yok** | "Çörek eklemek için veritabanına mı gireyim?" | Ürün yönetim sayfası (ekle/düzenle/sil, soft delete) |
| 2 | **Gider kategorileri sabit** | "Elektrik faturasını nereye yazayım?" | Dinamik kategori tablosu + yönetim arayüzü |
| 3 | **Kullanıcı/auth yok** | "Kasiyer sadece satış girmeli, üretime karışmamalı" | 3 rollü PIN giriş (kasiyer/usta/patron) |
| 4 | **OpenAI bağımlılığı** | "İnternet yokken sorgu çalışmıyor" | Kategorili filtre dropdown + hazır SQL butonları |
| 5 | **Yetkilendirme yok** | "Herkes her şeyi görmemeli" | Rol bazlı route decorator + middleware |

### 📋 Yeni Yol Haritası (Board Verdict — Sıralı)

#### Task 11: OpenAI'yi Kaldır, Local Sorgu Motoru Yap ✅
- [x] `query_engine.py` yeniden yaz — OpenAI çağrılarını kes
- [x] Kategorili filtre dropdown'ları ekle (tarih aralığı, ürün, müşteri)
- [x] Sorgu sayfasındaki 5 hazır SQL butonunu genişlet
- [x] Sonuçları tablo formatında göster
- [x] Test: internet kapalıyken sorgu çalışmalı
- **Süre:** 1 gün ✅

#### Task 12: Ürün CRUD Sayfası ✅
- [x] `templates/products.html` — ürün listeleme + form
- [x] `app.py` — /urunler route (GET listele, POST ekle, POST düzenle)
- [x] Soft delete (`is_active` sütunu, satış geçmişi bozulmaz)
- [x] Seed verisinden çıkar, UI'a taşı
- **Süre:** 1 gün ✅

#### Task 13: Kullanıcı/Auth Sistemi (3 Rollü PIN) ✅
- [x] `users` tablosu: id, username, pin_hash, role, created_at
- [x] `models.py` güncelle — user model
- [x] `templates/login.html` — PIN giriş ekranı
- [x] `app.py` — login route, session, logout
- [x] Decorator: `@role_required('patron')` route koruması
- [x] Seed admin: kullanıcıadı: patron, pin: 0000
- [x] Header'a kullanıcı bilgisi + çıkış butonu
- **Süre:** 2 gün ✅

#### Task 14: Dinamik Gider Kategorileri ✅
- [x] `gider_kategorileri` tablosu: id, ad, is_active
- [x] Migration: eski `giderler.kategori` → `gider_kategori_id` FK
- [x] Mevcut kategorileri seed'le (hammadde, fatura, maas, diger)
- [x] Gider formunda dinamik kategori dropdown (kategori_id bazlı)
- [x] `templates/categories.html` — kategori yönetimi (patron)
- [x] Soft delete (kategori silinemez, pasifleştirilir)
- [x] Sorgu motoru kategori join güncellemesi
- **Süre:** 1 gün ✅

#### Task 15: Rol Bazlı Ekran Kısıtlama ✅
- [x] Kasiyer: sadece Satış (1 nav item)
- [x] Usta: sadece Üretim + Fire (2 nav items)
- [x] Patron: tüm sayfalar (9 nav items)
- [x] Dashboard rol bazlı yönlendirme (login sonrası role göre home page)
- [x] `@role_required` decorator tüm route'larda
- [x] `allowed_pages` context processor ile nav gizleme
- **Süre:** 1 gün ✅

---

## Faz 5 — İyileştirme & Yayın (Bekliyor)

### Adım 5.1: Kullanıcı Testi
- [ ] Gerçek kullanıcılarla test (patron + kasiyer + usta rollerinde)
- [ ] Geri bildirim toplama
- [ ] Hata düzeltmeleri

### Adım 5.2: Yayın
- [ ] Otomatik yedekleme (SQLite dump)
- [ ] Kurulum rehberi (tek sayfa)
- [ ] Canlıya alma

---

## Proje Dosyaları (20 adet)

| Dosya | Açıklama | Durum |
|-------|----------|-------|
| `app.py` | Flask uygulaması (15 route, i18n + role context processor, 403 handler) | ✅ |
| `models.py` | 7 tablo + init_db + seed_data | ✅ |
| `query_engine.py` | 10 hazır SQL sorgu motoru (tamamen lokal) | ✅ |
| `i18n.py` | Çoklu dil motoru (TR/EN/DE) | ✅ |
| `config.py` | Yapılandırma (DB yolu, secret key) | ✅ |
| `.env` | Ortam değişkenleri | ✅ |
| `requirements.txt` | Bağımlılıklar | ✅ |
| `static/style.css` | Nothing Design (light/dark, responsive) | ✅ |
| `templates/layout.html` | Ana şablon (nav, tema, i18n) | ✅ |
| `templates/dashboard.html` | 4 metrik + 2 panel | ✅ |
| `templates/sales.html` | Satış formu + liste | ✅ |
| `templates/expenses.html` | Gider formu + liste | ✅ |
| `templates/production.html` | Üretim formu + liste | ✅ |
| `templates/customers.html` | Müşteri formu + karlılık | ✅ |
| `templates/fire.html` | Fire formu (3 tür) + liste | ✅ |
| `templates/query.html` | Filtre + buton bazlı sorgu arayüzü | ✅ |
| `templates/products.html` | Ürün CRUD (ekle/düzenle/soft-sil) | ✅ |
| `templates/login.html` | PIN giriş ekranı (3 rol) | ✅ |
| `templates/categories.html` | Kategori yönetimi (patron) | ✅ |
| `templates/forbidden.html` | 403 erişim reddedildi sayfası | ✅ |
| `auth.py` | login_required + role_required decorator | ✅ |

## İyileştirme Önerileri — Board Çıktısı (2 Tur)

### 1. Tur — Tamamlananlar ✅
1. **Veri girişi disiplini** → 3 alanlı form, 10 saniyede giriş ✅
2. **Fire tanımı** → 3 tür (üretim/bayat/dağıtım), ayrı takip ✅
3. **Anlamlı veri** → Geçen ay karşılaştırması ✅
4. **Doğal dil güveni** → "Bu verilere göre" bağlantısı (Task 11'de)
5. **Kullanıcı direnci** → Büyük yazı, yüksek kontrast, 44px ✅

### 2. Tur — Board Kararları ✅ (Tümü Tamamlandı)
| Sıra | Karar | Durum |
|------|-------|--------|
| 1 | **OpenAI'yi kaldır** | ✅ Task 11 |
| 2 | **Ürün CRUD ekle** | ✅ Task 12 |
| 3 | **Kullanıcı/auth (3 rol, PIN)** | ✅ Task 13 |
| 4 | **Dinamik gider kategorileri** | ✅ Task 14 |
| 5 | **Rol bazlı ekran kısıtlama** | ✅ Task 15 |

### ⚠️ Kritik Uyarı (Board Başkanı)
### Adım 4.5: Sorgu Sayfası Redesign — "3+1 Model" ✅

- [x] `query_engine.py` → Yeni `get_overview(zaman)` fonksiyonu (7 metrik tek SQL sorgusu, trend karşılaştırması)
- [x] `templates/query.html` → Tamamen yeniden yazıldı: 3 zaman butonu (Bugün/Bu Hafta/Bu Ay) + 7 metrik kartı (Ciro, Gider, Kar/Zarar, Fire Oranı, En Çok Satan, Bekleyen Borç, Un Kullanımı) + 1 Detaylı Sorgu düğmesi
- [x] `static/style.css` → Yeni `.time-selector`, `.time-btn`, `.metric-unit` stilleri (Nothing Design uyumlu)
- [x] `app.py` → `/sorgu` route'u güncellendi — `zaman` parametresi ile overview, `query_type` ile detay sorgu
- [x] `locales/` tr/en/de → `overview_bugun`, `overview_hafta`, `overview_ay`, `overview_detay`, `overview_gizle` eklendi
- [x] Test: Tüm metrikler doğru, zaman değiştirme çalışıyor, 10 sorgu tipi hala çalışır durumda

> **Sırayı bozma.** Önce auth yapayım derken ürün CRUD'u erteleme. Fırıncı önce ürün ekleyebilmeli, sonra giriş yapabilmeli.
>
> **Migration riski:** `giderler.kategori` string → FK dönüşümünde önce mevcut kategoriler seed'lenmeli. Aksi halde tüm gider geçmişi uçar.
>
> *Not: Sıra korundu, tüm migrationlar problemsiz tamamlandı.* ✅

---

## Faz 6 — HTMX & UX İyileştirmeleri ✅

### Adım 6.1: Seed Verisi (Demo Transactions) ✅
- [x] 15 satış kaydı (5 Mayıs → 11 Haziran 2026, 4 ürün, 3 müşteri, karma ödeme türleri)
- [x] 8 gider kaydı (Mayıs-Haziran, 4 kategori: hammadde/fatura/maaş/diğer)
- [x] 10 üretim kaydı (4 ürün, değişen miktarlar)
- [x] 6 fire kaydı (3 tür: üretim/bayat/dağıtım)
- [x] 2 müşteri borcu (aktif, ödenmemiş)
- **Etki:** Bugün/Hafta/Ay farklı değerler gösteriyor (Bugün: 640/435/181, Bu Hafta: 2290/2435/-177, Bu Ay: 3480/3255/181)

### Adım 6.2: Logo Eklendi ✅
- [x] SVG ocak/fırın ikonu (`header-logo`, `logo-icon`)
- [x] 1.5px stroke, monokrom, Nothing Design uyumlu
- [x] CSS: `.header-logo { display:flex; gap:10px }`, `.logo-icon { flex-shrink:0 }`

### Adım 6.3: HTMX Zaman Butonları ✅
- [x] `query.html` — form + JS `addEventListener` yerine her butona direkt `hx-post="/sorgu" hx-target="#query-content" hx-swap="outerHTML" hx-vals='{"zaman":"..."}'`
- [x] JavaScript event listener kaldırıldı — HTMX swap sonrası kaybolma sorunu çözüldü
- [x] `#time-form` ve `#zaman-input` kaldırıldı (artık ihtiyaç yok)
- [x] `query-btn` script'i `#query-content` içine taşındı (swap sonrası tekrar çalışır)
- [x] CSS: duplicate `@keyframes htmxFadeIn` temizlendi
- [x] `.time-btn.active` — kalın font (700) + altında 4px nokta indicator

### Adım 6.4: Veritabanı Temizliği ✅
- [x] **Çift veritabanı sorunu çözüldü:** `veritabani.db` (ASCII i, 53KB, gerçek veri) vs `veritabanı.db` (Türkçe ı U+0131, 0 byte). `config.py` `veritabani.db` (ASCII i) kullanıyor.
- [x] DB yeniden oluşturuldu: tablolar + seed data sıfırdan
- [x] Flask port 5001 (5000 — macOS AirPlay çakışması)
- [x] Auth aktif: patron/kasiyer/usta — PIN: 0000

### 🔧 HTMX Bug Fix — Zaman Butonları Çalışmıyordu
**Kök neden:** JavaScript `addEventListener` ile bağlanan click handler'lar HTMX `#query-content` swap sonrasında kayboluyordu. Script `{% block scripts %}` içindeydi ve `layout.html`'de `{% block scripts %}` tanımlı olmadığı için tam sayfa yüklemelerinde hiç render edilmiyor, yalnızca HTMX isteklerinde çalışıyordu.

**Fix:** Her butona direkt HTMX attribute'leri eklendi (`hx-post="/sorgu" hx-target="#query-content" hx-swap="outerHTML" hx-vals='{"zaman":"..."}'`). Hiç JavaScript yok, saf HTMX. Tarayıcıda doğrulandı: Today/This Week/This Month üçü de çalışıyor, metrikler anlık güncelleniyor.

**İkincil fix:** Soru butonları (query-btn) için script `#query-content` içine taşındı — HTMX swap sonrası `<script>` tag'i değerlendiriliyor.

## Teknik Borç & Gelecek

- [ ] Çoklu şube desteği (2. versiyon)
- [ ] Personel/vardiya takibi (2. versiyon)
- [ ] API ile muhasebe yazılımı entegrasyonu (2. versiyon)
- [ ] Sipariş yönetimi (2. versiyon)
- [ ] Cloud sync — patron evden kontrol (2. versiyon)
