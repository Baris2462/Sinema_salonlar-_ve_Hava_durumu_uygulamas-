import os
from flask import Flask, render_template, request
import psycopg2

app = Flask(__name__)

windows_ip = os.popen("ip route show default | awk '{print $3}'").read().strip()

DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "12345", 
    "host": windows_ip,
    "port": "5432"
}

LANG = {
    "tr": {"title": "Sinema & Hava Durumu", "city": "Şehir", "cinema": "Sinema Salonu", "movie": "Film Adı", "btn_clear": "Sıfırla", "no_data": "Kayıt bulunamadı.", "map": "Harita"},
    "en": {"title": "Cinema & Weather", "city": "City", "cinema": "Cinema", "movie": "Movie", "btn_clear": "Clear", "no_data": "No records found.", "map": "Map"}
}

@app.route('/')
def index():
    lang = request.args.get('lang', 'tr')
    if lang not in LANG:
        lang = 'tr'
    t = LANG[lang]
    
    secilen_sehir = request.args.get('sehir', '')
    secilen_salon = request.args.get('salon', '')
    secilen_film = request.args.get('film', '')

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT sehir FROM vizyon_sinema_hava WHERE sehir IS NOT NULL ORDER BY sehir;")
        sehirler = [r[0] for r in cursor.fetchall()]

        if secilen_sehir:
            cursor.execute("SELECT DISTINCT sinema_salonu FROM vizyon_sinema_hava WHERE sehir = %s ORDER BY sinema_salonu;", (secilen_sehir,))
        else:
            cursor.execute("SELECT DISTINCT sinema_salonu FROM vizyon_sinema_hava WHERE sinema_salonu IS NOT NULL ORDER BY sinema_salonu;")
        salonlar = [r[0] for r in cursor.fetchall()]

        filmler_query = "SELECT DISTINCT film_adi FROM vizyon_sinema_hava WHERE film_adi IS NOT NULL"
        filmler_params = []
        if secilen_sehir:
            filmler_query += " AND sehir = %s"
            filmler_params.append(secilen_sehir)
        if secilen_salon:
            filmler_query += " AND sinema_salonu = %s"
            filmler_params.append(secilen_salon)
        filmler_query += " ORDER BY film_adi;"
        
        cursor.execute(filmler_query, tuple(filmler_params))
        filmler = [r[0] for r in cursor.fetchall()]

        query = "SELECT id, film_adi, sinema_salonu, sehir, sicaklik, hava_durumu, islem_tarihi FROM vizyon_sinema_hava WHERE 1=1"
        params = []
        if secilen_sehir:
            query += " AND sehir = %s"
            params.append(secilen_sehir)
        if secilen_salon:
            query += " AND sinema_salonu = %s"
            params.append(secilen_salon)
        if secilen_film:
            query += " AND film_adi = %s"
            params.append(secilen_film)
        query += " ORDER BY id ASC;"
        
        cursor.execute(query, tuple(params))
        satirlar = cursor.fetchall()

        cursor.close()
        conn.close()
    except Exception:
        satirlar, sehirler, salonlar, filmler = [], [], [], []

    return render_template('index.html', veriler=satirlar, sehirler=sehirler, salonlar=salonlar, filmler=filmler, secilen_sehir=secilen_sehir, secilen_salon=secilen_salon, secilen_film=secilen_film, lang=lang, t=t)

if __name__ == '__main__':
    app.run(debug=True, port=5000)