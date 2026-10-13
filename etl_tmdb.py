import os
import psycopg2
import requests
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler("tmdb_etl.log", mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

TMDB_API_KEY = "6919cd8c6752a33c955259b9aa431476"
windows_ip = os.popen("ip route show default | awk '{print $3}'").read().strip()

DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "12345",
    "host": windows_ip,
    "port": "5432"
}

def tmdb_etl_sureci():
    # EXTRACT: API'den veriyi çek
    url = f"https://api.themoviedb.org/3/movie/now_playing?api_key={TMDB_API_KEY}&language=tr-TR&page=1"
    try:
        response = requests.get(url)
        response.raise_for_status()
        movies = response.json().get('results', [])
    except Exception as e:
        logging.error(f"API Çekme Hatası: {e}")
        return

    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        baslangic = datetime.now()
        islenen = 0
        hata_mesaji = None

        # LOAD için sorgu (Aynı film varsa puanını ve popülerliğini güncelle)
        insert_query = """
        INSERT INTO tmdb_movies (tmdb_id, title, release_date, popularity, vote_average)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (tmdb_id) DO UPDATE SET
            popularity = EXCLUDED.popularity,
            vote_average = EXCLUDED.vote_average;
        """
        
        for movie in movies:
            tmdb_id = movie.get('id')
            title = movie.get('title')
            release_date = movie.get('release_date')
            popularity = movie.get('popularity')
            vote_average = movie.get('vote_average')
            
            # TRANSFORM: Çıkış tarihi boş olan hatalı kayıtları filtrele
            if not release_date:
                continue

            try:
                cursor.execute(insert_query, (tmdb_id, title, release_date, popularity, vote_average))
                islenen += 1
            except Exception as e:
                hata_mesaji = str(e)
                conn.rollback()
                continue

        conn.commit()
        bitis = datetime.now()

        # LOGGING: İşlemi etl_log tablosuna kaydet
        log_query = """
        INSERT INTO etl_log (calisan_prosedur, hedef_tablo, islenen_kayit_sayisi, hata, baslangic_zamani, bitis_zamani)
        VALUES (%s, %s, %s, %s, %s, %s);
        """
        cursor.execute(log_query, ("tmdb_api_cekimi", "tmdb_movies", islenen, hata_mesaji, baslangic, bitis))
        conn.commit()
        
        logging.info(f"TMDB ETL Tamamlandı. İşlenen kayıt: {islenen}")

    except Exception as e:
        logging.error(f"Veritabanı Hatası: {e}")
    finally:
        if conn is not None:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    tmdb_etl_sureci()