from flask import Flask, render_template, request, jsonify, g, session, redirect
from config import SECRET_KEY, DATABASE
from auth import login_required, role_required
import sqlite3
import os

app = Flask(__name__)
app.secret_key = SECRET_KEY


@app.context_processor
def inject_globals():
    from i18n import t, get_lang
    lang = get_lang()
    role = session.get("role", "")
    role_pages = {
        "patron": ["dashboard", "sales", "expenses", "production", "customers", "products", "categories", "fire", "query"],
        "kasiyer": ["sales"],
        "usta": ["production", "fire"],
    }
    allowed_pages = role_pages.get(role, [])
    return dict(t=t, lang=lang, role=role, allowed_pages=allowed_pages)


@app.route("/giris", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        from auth import verify_login
        user = verify_login(request.form["username"], request.form["pin"])
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            next_url = request.args.get("next", "")
            if not next_url:
                role_home = {"patron": "/", "kasiyer": "/satis", "usta": "/uretim"}
                next_url = role_home.get(user["role"], "/")
            return redirect(next_url)
        return render_template("login.html", hata="Kullanıcı adı veya PIN hatalı.")
    return render_template("login.html", hata=None)


@app.route("/cikis")
def logout():
    session.clear()
    return redirect("/giris")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.route("/")
@login_required
@role_required("patron")
def index():
    db = get_db()
    row = db.execute("""
        SELECT COALESCE(SUM(s.toplam),0) as ciro,
               COALESCE((SELECT SUM(s2.toplam) FROM satislar s2 WHERE strftime('%m', s2.tarih) = strftime('%m', 'now') AND strftime('%Y', s2.tarih) = strftime('%Y', 'now')),0) as bu_ay_ciro,
               COALESCE((SELECT SUM(s2.toplam) FROM satislar s2 WHERE strftime('%m', s2.tarih) = strftime('%m', date('now','-1 month')) AND strftime('%Y', s2.tarih) = strftime('%Y', 'now')),0) as gecen_ay_ciro,
               COALESCE((SELECT SUM(g.tutar) FROM giderler g WHERE strftime('%m', g.tarih) = strftime('%m', 'now') AND strftime('%Y', g.tarih) = strftime('%Y', 'now')),0) as bu_ay_gider,
               COALESCE((SELECT SUM(f.miktar * u.birim_maliyet) FROM fire f JOIN urunler u ON f.urun_id = u.id WHERE strftime('%m', f.tarih) = strftime('%m', 'now') AND strftime('%Y', f.tarih) = strftime('%Y', 'now')),0) as bu_ay_fire_maliyet
        FROM satislar s
        WHERE strftime('%m', s.tarih) = strftime('%m', 'now')
        AND strftime('%Y', s.tarih) = strftime('%Y', 'now')
    """).fetchone()

    bu_ay_ciro = row["bu_ay_ciro"]
    gecen_ay_ciro = row["gecen_ay_ciro"]
    bu_ay_gider = row["bu_ay_gider"]
    bu_ay_fire = row["bu_ay_fire_maliyet"]
    bu_ay_kar = bu_ay_ciro - bu_ay_gider - bu_ay_fire

    top_urunler = db.execute("""
        SELECT u.ad, SUM(s.toplam) as toplam
        FROM satislar s JOIN urunler u ON s.urun_id = u.id
        WHERE strftime('%m', s.tarih) = strftime('%m', 'now') AND strftime('%Y', s.tarih) = strftime('%Y', 'now')
        GROUP BY u.id ORDER BY toplam DESC LIMIT 5
    """).fetchall()

    musteri_kar = db.execute("""
        SELECT m.ad, SUM(s.toplam) as alis,
               ROUND(AVG((s.birim_fiyat - u.birim_maliyet) / s.birim_fiyat * 100), 1) as marj
        FROM satislar s JOIN musteriler m ON s.musteri_id = m.id
             JOIN urunler u ON s.urun_id = u.id
        WHERE strftime('%m', s.tarih) = strftime('%m', 'now') AND strftime('%Y', s.tarih) = strftime('%Y', 'now')
        GROUP BY m.id ORDER BY alis DESC LIMIT 5
    """).fetchall()

    toplam_borc = db.execute("""
        SELECT COALESCE(SUM(borc_tutari),0) as toplam,
               (SELECT COUNT(*) FROM musteri_borclari WHERE durum='bekliyor') as bekleyen
        FROM musteri_borclari WHERE durum='bekliyor'
    """).fetchone()

    fire_oran = db.execute("""
        SELECT COALESCE(ROUND((SELECT SUM(miktar) FROM fire WHERE strftime('%m', tarih) = strftime('%m', 'now') AND strftime('%Y', tarih) = strftime('%Y', 'now'))
        / NULLIF((SELECT SUM(uretilen_miktar) FROM uretim WHERE strftime('%m', tarih) = strftime('%m', 'now') AND strftime('%Y', tarih) = strftime('%Y', 'now')),0) * 100, 1),0) as oran
    """).fetchone()["oran"]

    return render_template("dashboard.html",
        bu_ay_kar=bu_ay_kar, bu_ay_ciro=bu_ay_ciro, gecen_ay_ciro=gecen_ay_ciro,
        bu_ay_gider=bu_ay_gider, top_urunler=top_urunler,
        musteri_kar=musteri_kar, toplam_borc=toplam_borc["toplam"],
        bekleyen_borc=toplam_borc["bekleyen"], fire_oran=fire_oran,
        active_page="dashboard")


@app.route("/satis", methods=["GET", "POST"])
@login_required
@role_required("kasiyer", "patron")
def sales():
    db = get_db()
    if request.method == "POST":
        musteri_id = request.form.get("musteri_id")
        urun_id = request.form.get("urun_id")
        miktar = float(request.form.get("miktar", 1))
        urun = db.execute("SELECT * FROM urunler WHERE id=?", (urun_id,)).fetchone()
        birim_fiyat = urun["birim_fiyat"]
        toplam = miktar * birim_fiyat
        odeme = request.form.get("odeme_turu", "nakit")
        db.execute("INSERT INTO satislar (musteri_id, urun_id, miktar, birim_fiyat, toplam, odeme_turu) VALUES (?,?,?,?,?,?)",
                   (musteri_id, urun_id, miktar, birim_fiyat, toplam, odeme))

        if odeme == "veresiye":
            db.execute("INSERT INTO musteri_borclari (musteri_id, borc_tutari) VALUES (?,?)",
                       (musteri_id, toplam))
        db.commit()
        return "", 204

    urunler = db.execute("SELECT * FROM urunler WHERE is_active=1 ORDER BY ad").fetchall()
    musteriler = db.execute("SELECT * FROM musteriler ORDER BY ad").fetchall()
    satislar = db.execute("""
        SELECT s.*, u.ad as urun_ad, m.ad as musteri_ad
        FROM satislar s JOIN urunler u ON s.urun_id = u.id
        JOIN musteriler m ON s.musteri_id = m.id
        ORDER BY s.tarih DESC LIMIT 20
    """).fetchall()
    return render_template("sales.html", urunler=urunler, musteriler=musteriler, satislar=satislar, active_page="sales")


@app.route("/gider", methods=["GET", "POST"])
@login_required
@role_required("patron")
def expenses():
    db = get_db()
    if request.method == "POST":
        kategori_id = request.form.get("kategori_id")
        tutar = float(request.form["tutar"])
        aciklama = request.form.get("aciklama", "")
        kat = db.execute("SELECT ad FROM gider_kategorileri WHERE id=?", (kategori_id,)).fetchone()
        kategori_ad = kat["ad"] if kat else "diger"
        db.execute("INSERT INTO giderler (kategori, gider_kategori_id, tutar, aciklama) VALUES (?,?,?,?)",
                   (kategori_ad, kategori_id, tutar, aciklama))
        db.commit()
        return "", 204

    kategoriler = db.execute("SELECT * FROM gider_kategorileri WHERE is_active=1 ORDER BY ad").fetchall()
    giderler = db.execute("""
        SELECT g.*, COALESCE(gk.ad, g.kategori) as kategori_ad
        FROM giderler g LEFT JOIN gider_kategorileri gk ON g.gider_kategori_id = gk.id
        ORDER BY g.tarih DESC LIMIT 20
    """).fetchall()
    toplam = db.execute("SELECT COALESCE(SUM(tutar),0) as t FROM giderler WHERE strftime('%m', tarih)=strftime('%m','now') AND strftime('%Y', tarih)=strftime('%Y','now')").fetchone()["t"]
    return render_template("expenses.html", giderler=giderler, toplam=toplam, kategoriler=kategoriler, active_page="expenses")


@app.route("/uretim", methods=["GET", "POST"])
@login_required
@role_required("usta", "patron")
def production():
    db = get_db()
    if request.method == "POST":
        urun_id = request.form["urun_id"]
        miktar = float(request.form["uretilen_miktar"])
        un = float(request.form.get("kullanilan_un_kg", 0))
        notlar = request.form.get("notlar", "")
        db.execute("INSERT INTO uretim (urun_id, uretilen_miktar, kullanilan_un_kg, notlar) VALUES (?,?,?,?)",
                   (urun_id, miktar, un, notlar))
        db.commit()
        return "", 204

    urunler = db.execute("SELECT * FROM urunler WHERE is_active=1 ORDER BY ad").fetchall()
    kayitlar = db.execute("""
        SELECT u.*, ur.ad as urun_ad
        FROM uretim u JOIN urunler ur ON u.urun_id = ur.id
        ORDER BY u.tarih DESC LIMIT 20
    """).fetchall()
    return render_template("production.html", urunler=urunler, kayitlar=kayitlar, active_page="production")


@app.route("/musteriler", methods=["GET", "POST"])
@login_required
@role_required("patron")
def customers():
    db = get_db()
    if request.method == "POST":
        ad = request.form["ad"]
        telefon = request.form.get("telefon", "")
        tur = request.form.get("tur", "perakende")
        db.execute("INSERT INTO musteriler (ad, telefon, tur) VALUES (?,?,?)", (ad, telefon, tur))
        db.commit()
        return "", 204

    musteriler = db.execute("""
        SELECT m.*,
               COALESCE((SELECT SUM(s.toplam) FROM satislar s WHERE s.musteri_id = m.id AND strftime('%m',s.tarih)=strftime('%m','now')),0) as bu_ay_alis,
               COALESCE((SELECT SUM(mb.borc_tutari) FROM musteri_borclari mb WHERE mb.musteri_id = m.id AND mb.durum='bekliyor'),0) as borc,
               ROUND(COALESCE((SELECT AVG((s.birim_fiyat - u.birim_maliyet)/s.birim_fiyat*100) FROM satislar s JOIN urunler u ON s.urun_id=u.id WHERE s.musteri_id=m.id),0),1) as marj
        FROM musteriler m ORDER BY bu_ay_alis DESC
    """).fetchall()
    return render_template("customers.html", musteriler=musteriler, active_page="customers")


@app.route("/fire", methods=["GET", "POST"])
@login_required
@role_required("usta", "patron")
def fire_page():
    db = get_db()
    if request.method == "POST":
        urun_id = request.form["urun_id"]
        fire_turu = request.form["fire_turu"]
        miktar = float(request.form["miktar"])
        db.execute("INSERT INTO fire (urun_id, fire_turu, miktar) VALUES (?,?,?)",
                   (urun_id, fire_turu, miktar))
        db.commit()
        return "", 204

    urunler = db.execute("SELECT * FROM urunler WHERE is_active=1 ORDER BY ad").fetchall()
    kayitlar = db.execute("""
        SELECT f.*, u.ad as urun_ad FROM fire f JOIN urunler u ON f.urun_id = u.id ORDER BY f.tarih DESC LIMIT 20
    """).fetchall()
    return render_template("fire.html", urunler=urunler, kayitlar=kayitlar, active_page="fire")


@app.route("/urunler", methods=["GET", "POST"])
@login_required
@role_required("patron")
def products():
    db = get_db()
    if request.method == "POST":
        ad = request.form["ad"]
        birim = request.form.get("birim", "adet")
        tur = request.form.get("tur", "perakende")
        maliyet = float(request.form.get("birim_maliyet", 0))
        fiyat = float(request.form.get("birim_fiyat", 0))
        urun_id = request.form.get("id")
        if urun_id:
            db.execute("UPDATE urunler SET ad=?, birim=?, tur=?, birim_maliyet=?, birim_fiyat=? WHERE id=?",
                       (ad, birim, tur, maliyet, fiyat, urun_id))
        else:
            db.execute("INSERT INTO urunler (ad, birim, tur, birim_maliyet, birim_fiyat) VALUES (?,?,?,?,?)",
                       (ad, birim, tur, maliyet, fiyat))
        db.commit()
        return "", 204

    urunler = db.execute("SELECT * FROM urunler WHERE is_active=1 ORDER BY ad").fetchall()
    return render_template("products.html", urunler=urunler, active_page="products")


@app.route("/urunler/sil/<int:id>", methods=["POST"])
@login_required
@role_required("patron")
def product_delete(id):
    db = get_db()
    db.execute("UPDATE urunler SET is_active=0 WHERE id=?", (id,))
    db.commit()
    return "", 204


@app.route("/kategoriler", methods=["GET", "POST"])
@login_required
@role_required("patron")
def categories():
    db = get_db()
    if request.method == "POST":
        ad = request.form["ad"].strip().lower()
        kat_id = request.form.get("id")
        if kat_id:
            db.execute("UPDATE gider_kategorileri SET ad=? WHERE id=?", (ad, kat_id))
        else:
            db.execute("INSERT INTO gider_kategorileri (ad) VALUES (?)", (ad,))
        db.commit()
        return "", 204

    kategoriler = db.execute("SELECT * FROM gider_kategorileri ORDER BY is_active DESC, ad").fetchall()
    return render_template("categories.html", kategoriler=kategoriler, active_page="categories")


@app.route("/kategoriler/sil/<int:id>", methods=["POST"])
@login_required
@role_required("patron")
def category_delete(id):
    db = get_db()
    db.execute("UPDATE gider_kategorileri SET is_active=0 WHERE id=?", (id,))
    db.commit()
    return "", 204


@app.route("/sorgu", methods=["GET", "POST"])
@login_required
@role_required("patron")
def query_page():
    sonuc = None
    aktif_sorgu = None
    baslangic = ""
    bitis = ""
    urun_id = None
    musteri_id = None
    zaman = "ay"

    if request.method == "POST":
        zaman = request.form.get("zaman", "ay")
        query_type = request.form.get("query_type")
        if query_type:
            baslangic = request.form.get("baslangic", "")
            bitis = request.form.get("bitis", "")
            urun_id = request.form.get("urun_id") or None
            musteri_id = request.form.get("musteri_id") or None
            from query_engine import execute_query
            sonuc = execute_query(query_type, baslangic, bitis, urun_id, musteri_id)
            aktif_sorgu = query_type

    from query_engine import get_overview
    overview = get_overview(zaman)

    db = get_db()
    urunler = db.execute("SELECT id, ad FROM urunler WHERE is_active=1 ORDER BY ad").fetchall()
    musteriler = db.execute("SELECT id, ad FROM musteriler ORDER BY ad").fetchall()

    hx_request = bool(request.headers.get("HX-Request"))

    return render_template("query.html", sonuc=sonuc, aktif_sorgu=aktif_sorgu,
                           baslangic=baslangic, bitis=bitis,
                           urun_id=urun_id, musteri_id=musteri_id,
                           urunler=urunler, musteriler=musteriler,
                           overview=overview, zaman=zaman,
                           active_page="query", hx_request=hx_request)


@app.errorhandler(403)
def forbidden(e):
    return render_template("forbidden.html"), 403


if __name__ == "__main__":
    os.makedirs(os.path.join(os.path.dirname(__file__), "templates"), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), "static"), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), "locales"), exist_ok=True)
    from models import init_db, seed_data
    init_db()
    seed_data()
    from i18n import load_translations
    load_translations()
    app.run(debug=True, host="0.0.0.0", port=5001)
