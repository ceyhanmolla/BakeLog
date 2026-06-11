import sqlite3
from config import DATABASE


def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS urunler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT NOT NULL,
            birim TEXT NOT NULL DEFAULT 'adet',
            tur TEXT NOT NULL DEFAULT 'perakende' CHECK(tur IN ('toptan','perakende')),
            birim_maliyet REAL NOT NULL DEFAULT 0,
            birim_fiyat REAL NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS musteriler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT NOT NULL,
            telefon TEXT DEFAULT '',
            tur TEXT NOT NULL DEFAULT 'perakende' CHECK(tur IN ('toptan','perakende')),
            kayit_tarihi DATE DEFAULT (date('now'))
        );

        CREATE TABLE IF NOT EXISTS satislar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarih DATETIME DEFAULT (datetime('now','localtime')),
            musteri_id INTEGER REFERENCES musteriler(id),
            urun_id INTEGER REFERENCES urunler(id),
            miktar REAL NOT NULL DEFAULT 1,
            birim_fiyat REAL NOT NULL,
            toplam REAL NOT NULL,
            odeme_turu TEXT NOT NULL DEFAULT 'nakit' CHECK(odeme_turu IN ('nakit','kart','veresiye'))
        );

        CREATE TABLE IF NOT EXISTS giderler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarih DATETIME DEFAULT (datetime('now','localtime')),
            kategori TEXT NOT NULL DEFAULT 'diger' CHECK(kategori IN ('hammadde','fatura','maas','diger')),
            tutar REAL NOT NULL,
            aciklama TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS uretim (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarih DATE DEFAULT (date('now')),
            urun_id INTEGER REFERENCES urunler(id),
            uretilen_miktar REAL NOT NULL DEFAULT 0,
            kullanilan_un_kg REAL DEFAULT 0,
            notlar TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS fire (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarih DATE DEFAULT (date('now')),
            urun_id INTEGER REFERENCES urunler(id),
            fire_turu TEXT NOT NULL CHECK(fire_turu IN ('uretim','bayat','dagitim')),
            miktar REAL NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            pin_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'kasiyer' CHECK(role IN ('kasiyer','usta','patron')),
            created_at DATETIME DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS gider_kategorileri (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT NOT NULL UNIQUE,
            is_active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS musteri_borclari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            musteri_id INTEGER REFERENCES musteriler(id),
            tarih DATE DEFAULT (date('now')),
            borc_tutari REAL NOT NULL,
            odenme_tarihi DATE,
            durum TEXT NOT NULL DEFAULT 'bekliyor' CHECK(durum IN ('bekliyor','odendi'))
        );
    """)

    for migration in [
        "ALTER TABLE urunler ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1",
        "ALTER TABLE giderler ADD COLUMN gider_kategori_id INTEGER REFERENCES gider_kategorileri(id)",
    ]:
        try:
            conn.execute(migration)
        except Exception:
            pass

    conn.commit()
    conn.close()


def seed_data():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.executemany("INSERT OR IGNORE INTO urunler (id, ad, birim, tur, birim_maliyet, birim_fiyat) VALUES (?,?,?,?,?,?)", [
        (1, 'Köy Ekmeği', 'adet', 'perakende', 8, 20),
        (2, 'Tam Buğday', 'adet', 'perakende', 10, 25),
        (3, 'Simit', 'adet', 'perakende', 3, 10),
        (4, 'Poğaça', 'adet', 'perakende', 4, 12),
        (5, 'Somon Ekmek', 'adet', 'toptan', 15, 30),
        (6, 'Un (50kg)', 'çuval', 'toptan', 350, 450),
    ])

    cursor.executemany("INSERT OR IGNORE INTO musteriler (id, ad, telefon, tur) VALUES (?,?,?,?)", [
        (1, 'Bakkal Ahmet', '05551234567', 'toptan'),
        (2, 'Mahalle Market', '05559876543', 'toptan'),
        (3, 'Otel Akdeniz', '05551112233', 'toptan'),
        (4, 'Müşteri', '', 'perakende'),
    ])

    cursor.executemany("INSERT OR IGNORE INTO gider_kategorileri (id, ad) VALUES (?,?)", [
        (1, 'hammadde'),
        (2, 'fatura'),
        (3, 'maas'),
        (4, 'diger'),
    ])
    cursor.execute("UPDATE giderler SET gider_kategori_id = (SELECT id FROM gider_kategorileri WHERE ad = giderler.kategori) WHERE gider_kategori_id IS NULL")

    import hashlib
    cursor.executemany("INSERT OR IGNORE INTO users (username, pin_hash, role) VALUES (?,?,?)", [
        ('patron', hashlib.sha256(b'0000').hexdigest(), 'patron'),
        ('kasiyer', hashlib.sha256(b'0000').hexdigest(), 'kasiyer'),
        ('usta', hashlib.sha256(b'0000').hexdigest(), 'usta'),
    ])

    cursor.executemany("INSERT OR IGNORE INTO satislar (id, tarih, musteri_id, urun_id, miktar, birim_fiyat, toplam, odeme_turu) VALUES (?,?,?,?,?,?,?,?)", [
        (1,  '2026-05-05 08:30:00', 1, 1, 50, 18, 900, 'nakit'),
        (2,  '2026-05-12 10:15:00', 2, 2, 30, 22, 660, 'veresiye'),
        (3,  '2026-05-15 09:00:00', 3, 3, 100, 8, 800, 'kart'),
        (4,  '2026-05-20 11:30:00', 1, 5, 20, 28, 560, 'nakit'),
        (5,  '2026-05-25 16:45:00', 4, 4, 5, 12, 60, 'nakit'),
        (6,  '2026-05-28 10:00:00', 2, 1, 40, 18, 720, 'veresiye'),
        (7,  '2026-06-02 08:00:00', 3, 3, 80, 8, 640, 'kart'),
        (8,  '2026-06-05 09:30:00', 1, 2, 25, 22, 550, 'nakit'),
        (9,  '2026-06-08 14:00:00', 4, 4, 10, 12, 120, 'nakit'),
        (10, '2026-06-09 10:30:00', 2, 1, 35, 18, 630, 'veresiye'),
        (11, '2026-06-10 09:00:00', 1, 5, 15, 28, 420, 'nakit'),
        (12, '2026-06-10 11:00:00', 3, 3, 60, 8, 480, 'kart'),
        (13, '2026-06-11 08:15:00', 4, 1, 3, 20, 60, 'nakit'),
        (14, '2026-06-11 09:30:00', 1, 1, 20, 18, 360, 'veresiye'),
        (15, '2026-06-11 10:00:00', 2, 2, 10, 22, 220, 'nakit'),
    ])

    cursor.executemany("INSERT OR IGNORE INTO giderler (id, tarih, kategori, gider_kategori_id, tutar, aciklama) VALUES (?,?,?,?,?,?)", [
        (1, '2026-05-03 10:00:00', 'hammadde', 1, 350, 'Un 1 çuval'),
        (2, '2026-05-15 09:00:00', 'maas', 3, 2000, 'Usta maaşı Mayıs'),
        (3, '2026-05-28 12:00:00', 'fatura', 2, 450, 'Elektrik faturası'),
        (4, '2026-06-02 10:00:00', 'hammadde', 1, 700, 'Un 2 çuval'),
        (5, '2026-06-07 11:00:00', 'fatura', 2, 120, 'Su faturası'),
        (6, '2026-06-10 09:00:00', 'maas', 3, 2000, 'Usta maaşı Haziran'),
        (7, '2026-06-11 08:00:00', 'hammadde', 1, 350, 'Un 1 çuval'),
        (8, '2026-06-11 12:30:00', 'diger', 4, 85, 'Temizlik malzemesi'),
    ])

    cursor.executemany("INSERT OR IGNORE INTO uretim (id, tarih, urun_id, uretilen_miktar, kullanilan_un_kg, notlar) VALUES (?,?,?,?,?,?)", [
        (1, '2026-05-05', 1, 100, 15, 'Sabah üretimi'),
        (2, '2026-05-12', 2, 80, 12, 'Öğle üretimi'),
        (3, '2026-05-15', 3, 200, 8, 'Simit günlük'),
        (4, '2026-05-20', 5, 60, 12, 'Toptan sipariş'),
        (5, '2026-05-25', 4, 100, 10, 'Poğaça çeşitli'),
        (6, '2026-06-02', 1, 120, 18, 'Haftalık ekmek'),
        (7, '2026-06-05', 2, 100, 15, 'Tam buğday partisi'),
        (8, '2026-06-08', 4, 80, 8, 'Poğaça sabah'),
        (9, '2026-06-10', 3, 150, 6, 'Simit büyük parti'),
        (10, '2026-06-11', 1, 60, 9, 'Günlük ekmek'),
    ])

    cursor.executemany("INSERT OR IGNORE INTO fire (id, tarih, urun_id, fire_turu, miktar) VALUES (?,?,?,?,?)", [
        (1, '2026-05-15', 3, 'bayat', 5),
        (2, '2026-05-25', 4, 'bayat', 3),
        (3, '2026-05-28', 1, 'dagitim', 2),
        (4, '2026-06-02', 3, 'uretim', 4),
        (5, '2026-06-08', 4, 'bayat', 2),
        (6, '2026-06-11', 1, 'uretim', 3),
    ])

    cursor.executemany("INSERT OR IGNORE INTO musteri_borclari (id, musteri_id, tarih, borc_tutari, durum) VALUES (?,?,?,?,?)", [
        (1, 2, '2026-06-09', 630, 'bekliyor'),
        (2, 1, '2026-06-11', 360, 'bekliyor'),
    ])

    conn.commit()
    conn.close()
