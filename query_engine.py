import sqlite3
from config import DATABASE

QUERY_TYPES = [
    {"id": "kar_zarar", "label_key": "query_kar_zarar"},
    {"id": "ciro", "label_key": "query_ciro"},
    {"id": "giderler", "label_key": "query_giderler"},
    {"id": "un_kullanim", "label_key": "query_un_kullanim"},
    {"id": "fire_orani", "label_key": "query_fire_orani"},
    {"id": "en_cok_satan", "label_key": "query_en_cok_satan"},
    {"id": "musteri_siralamasi", "label_key": "query_musteri_siralamasi"},
    {"id": "borclar", "label_key": "query_borclar"},
    {"id": "gunluk_satislar", "label_key": "query_gunluk_satislar"},
    {"id": "gecen_ay_karsilastirma", "label_key": "query_gecen_ay"},
]


def _db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def execute_query(query_type, baslangic="", bitis="", urun_id=None, musteri_id=None):
    try:
        fn = _QUERY_FUNCS.get(query_type)
        if not fn:
            return {"columns": [[""]], "rows": []}
        return fn(baslangic, bitis, urun_id, musteri_id)
    except Exception as e:
        return {"columns": [["Hata"]], "rows": [[str(e)]]}


def _date_cond(baslangic, bitis, prefix="tarih"):
    if baslangic and bitis:
        return f"date({prefix}) >= ? AND date({prefix}) <= ?", [baslangic, bitis]
    if baslangic:
        return f"date({prefix}) >= ?", [baslangic]
    if bitis:
        return f"date({prefix}) <= ?", [bitis]
    return f"strftime('%m', {prefix}) = strftime('%m', 'now') AND strftime('%Y', {prefix}) = strftime('%Y', 'now')", []


def _q_kar_zarar(baslangic, bitis, urun_id, musteri_id):
    dc, dp = _date_cond(baslangic, bitis)
    conn = _db()
    row = conn.execute(f"""
        SELECT
            COALESCE((SELECT COALESCE(SUM(s.toplam),0) FROM satislar s WHERE {dc}),0) as ciro,
            COALESCE((SELECT COALESCE(SUM(g.tutar),0) FROM giderler g WHERE {dc}),0) as gider,
            COALESCE((SELECT COALESCE(SUM(f.miktar * u.birim_maliyet),0) FROM fire f JOIN urunler u ON f.urun_id=u.id WHERE {dc}),0) as fire_maliyet
    """, dp * 3 if dp else dp).fetchone()
    conn.close()
    kar = row["ciro"] - row["gider"] - row["fire_maliyet"]
    return {
        "columns": [["Ciro (TL)", "Gider (TL)", "Fire Maliyet (TL)", "Kar/Zarar (TL)"]],
        "rows": [[row["ciro"], row["gider"], row["fire_maliyet"], kar]]
    }


def _q_ciro(baslangic, bitis, urun_id, musteri_id):
    dc, dp = _date_cond(baslangic, bitis)
    conn = _db()
    if musteri_id:
        dc += " AND s.musteri_id = ?"
        dp.append(musteri_id)
    if urun_id:
        dc += " AND s.urun_id = ?"
        dp.append(urun_id)
    row = conn.execute(f"""
        SELECT COALESCE(SUM(s.toplam),0) as ciro, COALESCE(COUNT(*),0) as adet,
               COALESCE(ROUND(AVG(s.toplam),2),0) as ortalama
        FROM satislar s WHERE {dc}
    """, dp).fetchone()
    conn.close()
    return {
        "columns": [["Toplam Ciro (TL)", "İşlem Sayısı", "Ortalama İşlem (TL)"]],
        "rows": [[row["ciro"], row["adet"], row["ortalama"]]]
    }


def _q_giderler(baslangic, bitis, urun_id, musteri_id):
    dc, dp = _date_cond(baslangic, bitis)
    conn = _db()
    rows = conn.execute(f"""
        SELECT COALESCE(gk.ad, g.kategori) as kategori, COALESCE(SUM(g.tutar),0) as toplam, COUNT(*) as adet
        FROM giderler g LEFT JOIN gider_kategorileri gk ON g.gider_kategori_id = gk.id
        WHERE {dc} GROUP BY g.kategori ORDER BY toplam DESC
    """, dp).fetchall()
    conn.close()
    toplam_tutar = sum(r["toplam"] for r in rows)
    toplam_adet = sum(r["adet"] for r in rows)
    return {
        "columns": [["Kategori", "Toplam (TL)", "İşlem Sayısı"]],
        "rows": [[r["kategori"], r["toplam"], r["adet"]] for r in rows] +
                [["TOPLAM", toplam_tutar, toplam_adet]]
    }


def _q_un_kullanim(baslangic, bitis, urun_id, musteri_id):
    dc, dp = _date_cond(baslangic, bitis)
    conn = _db()
    row = conn.execute(f"""
        SELECT COALESCE(SUM(u.kullanilan_un_kg),0) as un_kg,
               COALESCE(SUM(u.uretilen_miktar),0) as toplam_uretim,
               COALESCE(ROUND(SUM(u.kullanilan_un_kg) * 100.0 / NULLIF(SUM(u.uretilen_miktar),0), 2), 0) as birim_basi_un
        FROM uretim u WHERE {dc}
    """, dp).fetchone()
    conn.close()
    return {
        "columns": [["Kullanılan Un (kg)", "Toplam Üretim (adet)", "Birim Başı Un (kg)"]],
        "rows": [[row["un_kg"], row["toplam_uretim"], row["birim_basi_un"]]]
    }


def _q_fire_orani(baslangic, bitis, urun_id, musteri_id):
    dc, dp = _date_cond(baslangic, bitis)
    conn = _db()
    row = conn.execute(f"""
        SELECT COALESCE(SUM(CASE WHEN fire_turu='uretim' THEN f.miktar END),0) as uretim_fire,
               COALESCE(SUM(CASE WHEN fire_turu='bayat' THEN f.miktar END),0) as bayat_fire,
               COALESCE(SUM(CASE WHEN fire_turu='dagitim' THEN f.miktar END),0) as dagitim_fire,
               COALESCE(SUM(f.miktar),0) as toplam_fire,
               COALESCE(ROUND(SUM(f.miktar) * 100.0 / NULLIF((SELECT SUM(uretilen_miktar) FROM uretim WHERE {dc}),0), 1),0) as oran
        FROM fire f WHERE {dc}
    """, dp * 2 if dp else dp).fetchone()
    conn.close()
    return {
        "columns": [["Üretim Fire", "Bayat Fire", "Dağıtım Fire", "Toplam Fire", "Fire Oranı (%)"]],
        "rows": [[row["uretim_fire"], row["bayat_fire"], row["dagitim_fire"], row["toplam_fire"], row["oran"]]]
    }


def _q_en_cok_satan(baslangic, bitis, urun_id, musteri_id):
    dc, dp = _date_cond(baslangic, bitis)
    conn = _db()
    rows = conn.execute(f"""
        SELECT u.ad, COALESCE(SUM(s.toplam),0) as toplam,
               COALESCE(SUM(s.miktar),0) as miktar, COUNT(*) as adet
        FROM satislar s JOIN urunler u ON s.urun_id = u.id
        WHERE {dc} GROUP BY u.id ORDER BY toplam DESC
    """, dp).fetchall()
    conn.close()
    return {
        "columns": [["Ürün", "Toplam (TL)", "Miktar", "İşlem Sayısı"]],
        "rows": [[r["ad"], r["toplam"], r["miktar"], r["adet"]] for r in rows]
    }


def _q_musteri_siralamasi(baslangic, bitis, urun_id, musteri_id):
    dc, dp = _date_cond(baslangic, bitis)
    conn = _db()
    rows = conn.execute(f"""
        SELECT m.ad, COALESCE(SUM(s.toplam),0) as toplam, COALESCE(COUNT(s.id),0) as adet
        FROM musteriler m LEFT JOIN satislar s ON s.musteri_id=m.id AND {dc}
        GROUP BY m.id ORDER BY toplam DESC
    """, dp).fetchall()
    conn.close()
    return {
        "columns": [["Müşteri", "Toplam Alışveriş (TL)", "İşlem Sayısı"]],
        "rows": [[r["ad"], r["toplam"], r["adet"]] for r in rows]
    }


def _q_borclar(baslangic, bitis, urun_id, musteri_id):
    conn = _db()
    rows = conn.execute("""
        SELECT m.ad, COALESCE(SUM(mb.borc_tutari),0) as borc, COUNT(*) as adet,
               MIN(mb.tarih) as en_eski
        FROM musteri_borclari mb JOIN musteriler m ON mb.musteri_id=m.id
        WHERE mb.durum='bekliyor' GROUP BY m.id ORDER BY borc DESC
    """).fetchall()
    conn.close()
    toplam = sum(r["borc"] for r in rows)
    return {
        "columns": [["Müşteri", "Borç (TL)", "İşlem Sayısı", "En Eski Borç"]],
        "rows": [[r["ad"], r["borc"], r["adet"], r["en_eski"]] for r in rows] +
                [["TOPLAM", toplam, sum(r["adet"] for r in rows), ""]]
    }


def _q_gunluk_satislar(baslangic, bitis, urun_id, musteri_id):
    dc, dp = _date_cond(baslangic, bitis)
    conn = _db()
    rows = conn.execute(f"""
        SELECT date(s.tarih) as gun, COALESCE(SUM(s.toplam),0) as ciro, COUNT(*) as adet
        FROM satislar s WHERE {dc} GROUP BY gun ORDER BY gun DESC
    """, dp).fetchall()
    conn.close()
    return {
        "columns": [["Tarih", "Ciro (TL)", "İşlem Sayısı"]],
        "rows": [[r["gun"], r["ciro"], r["adet"]] for r in rows]
    }


def _q_gecen_ay_karsilastirma(baslangic, bitis, urun_id, musteri_id):
    conn = _db()
    bu_ay = conn.execute("""
        SELECT COALESCE(SUM(s.toplam),0) as ciro,
               COALESCE((SELECT SUM(g.tutar) FROM giderler g WHERE strftime('%m',g.tarih)=strftime('%m','now') AND strftime('%Y',g.tarih)=strftime('%Y','now')),0) as gider
        FROM satislar s WHERE strftime('%m',s.tarih)=strftime('%m','now') AND strftime('%Y',s.tarih)=strftime('%Y','now')
    """).fetchone()
    gecen_ay = conn.execute("""
        SELECT COALESCE(SUM(s.toplam),0) as ciro,
               COALESCE((SELECT SUM(g.tutar) FROM giderler g WHERE strftime('%m',g.tarih)=strftime('%m',date('now','-1 month')) AND strftime('%Y',g.tarih)=strftime('%Y','now')),0) as gider
        FROM satislar s WHERE strftime('%m',s.tarih)=strftime('%m',date('now','-1 month')) AND strftime('%Y',s.tarih)=strftime('%Y','now')
    """).fetchone()
    conn.close()
    bu_ciro, bu_gider = bu_ay["ciro"], bu_ay["gider"]
    ge_ciro, ge_gider = gecen_ay["ciro"], gecen_ay["gider"]
    bu_kar, ge_kar = bu_ciro - bu_gider, ge_ciro - ge_gider
    fark_yuzde = round((bu_ciro - ge_ciro) / ge_ciro * 100, 1) if ge_ciro else 0
    return {
        "columns": [["Dönem", "Ciro (TL)", "Gider (TL)", "Kar (TL)"]],
        "rows": [
            ["Bu Ay", bu_ciro, bu_gider, bu_kar],
            ["Geçen Ay", ge_ciro, ge_gider, ge_kar],
            ["Fark", bu_ciro - ge_ciro, bu_gider - ge_gider, bu_kar - ge_kar],
            ["Değişim (%)", f"{fark_yuzde}%", "", ""],
        ]
    }


def get_overview(zaman="ay"):
    conn = _db()
    now = conn.execute("SELECT date('now') as bugun, date('now','weekday 1','-7 days') as hafta_basi").fetchone()

    if zaman == "bugun":
        dc = dc_u = dc_f = "date(tarih) = date('now')"
        dc_s = "date(tarih) = date('now')"
    elif zaman == "hafta":
        dc = fw = "strftime('%W',tarih)=strftime('%W','now') AND strftime('%Y',tarih)=strftime('%Y','now')"
        dc_s = "strftime('%W',s.tarih)=strftime('%W','now') AND strftime('%Y',s.tarih)=strftime('%Y','now')"
        dc_f = dc_u = fw
    else:
        dc = fm = "strftime('%m',tarih)=strftime('%m','now') AND strftime('%Y',tarih)=strftime('%Y','now')"
        dc_s = "strftime('%m',s.tarih)=strftime('%m','now') AND strftime('%Y',s.tarih)=strftime('%Y','now')"
        dc_f = dc_u = fm

    ciro = conn.execute(f"SELECT COALESCE(SUM(toplam),0) as v FROM satislar s WHERE {dc_s}").fetchone()["v"]
    gider = conn.execute(f"SELECT COALESCE(SUM(tutar),0) as v FROM giderler WHERE {dc}").fetchone()["v"]
    fire = conn.execute(f"SELECT COALESCE(SUM(f.miktar*u.birim_maliyet),0) as v FROM fire f JOIN urunler u ON f.urun_id=u.id WHERE {dc_f}").fetchone()["v"]
    kar = ciro - gider - fire
    un = conn.execute(f"SELECT COALESCE(SUM(kullanilan_un_kg),0) as v FROM uretim WHERE {dc}").fetchone()["v"]
    fire_oran = conn.execute(f"""
        SELECT COALESCE(ROUND(SUM(f.miktar)*100.0/NULLIF((SELECT SUM(uretilen_miktar) FROM uretim WHERE {dc_f.replace('f.','')}),0),1),0) as v
        FROM fire f WHERE {dc_f}
    """).fetchone()["v"]
    pop_urun = conn.execute(f"""
        SELECT COALESCE(u.ad,'-') as ad, COALESCE(SUM(s.toplam),0) as t
        FROM satislar s JOIN urunler u ON s.urun_id=u.id WHERE {dc_s} GROUP BY u.id ORDER BY t DESC LIMIT 1
    """).fetchone()
    pop_urun_ad = pop_urun["ad"] if pop_urun else "-"
    pop_urun_t = pop_urun["t"] if pop_urun else 0
    borc = conn.execute("SELECT COALESCE(SUM(borc_tutari),0) as v FROM musteri_borclari WHERE durum='bekliyor'").fetchone()["v"]

    if zaman == "ay":
        gecen_ciro = conn.execute("SELECT COALESCE(SUM(toplam),0) as v FROM satislar WHERE strftime('%m',tarih)=strftime('%m',date('now','-1 month')) AND strftime('%Y',tarih)=strftime('%Y','now')").fetchone()["v"]
        gecen_gider = conn.execute("SELECT COALESCE(SUM(tutar),0) as v FROM giderler WHERE strftime('%m',tarih)=strftime('%m',date('now','-1 month')) AND strftime('%Y',tarih)=strftime('%Y','now')").fetchone()["v"]
        gecen_fire = conn.execute("SELECT COALESCE(SUM(f.miktar*u.birim_maliyet),0) as v FROM fire f JOIN urunler u ON f.urun_id=u.id WHERE strftime('%m',f.tarih)=strftime('%m',date('now','-1 month')) AND strftime('%Y',f.tarih)=strftime('%Y','now')").fetchone()["v"]
        gecen_kar = gecen_ciro - gecen_gider - gecen_fire
        kar_trend = "up" if kar > gecen_kar else ("down" if kar < gecen_kar else "flat")
        ciro_trend = "up" if ciro > gecen_ciro else ("down" if ciro < gecen_ciro else "flat")
    else:
        kar_trend = "flat"
        ciro_trend = "flat"

    conn.close()
    return {
        "zaman": zaman,
        "ciro": ciro, "gider": gider, "kar": kar, "fire": fire_oran,
        "un": un, "pop_urun": pop_urun_ad, "pop_urun_t": pop_urun_t,
        "borc": borc,
        "kar_trend": kar_trend, "ciro_trend": ciro_trend,
    }


_QUERY_FUNCS = {
    "kar_zarar": _q_kar_zarar,
    "ciro": _q_ciro,
    "giderler": _q_giderler,
    "un_kullanim": _q_un_kullanim,
    "fire_orani": _q_fire_orani,
    "en_cok_satan": _q_en_cok_satan,
    "musteri_siralamasi": _q_musteri_siralamasi,
    "borclar": _q_borclar,
    "gunluk_satislar": _q_gunluk_satislar,
    "gecen_ay_karsilastirma": _q_gecen_ay_karsilastirma,
}
