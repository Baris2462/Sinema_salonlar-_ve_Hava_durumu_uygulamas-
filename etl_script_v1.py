import os
import psycopg2
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("wsl_etl_islemleri.log", mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

windows_ip = os.popen("ip route show default | awk '{print $3}'").read().strip()

DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "12345",
    "host": windows_ip,
    "port": "5432"
}

TASKS = {
    "sp_musteri_satis_ozeti": {"query": "CALL sp_musteri_satis_ozeti();", "hedef": "musteri_satis_ozeti"},
    "sp_kategori_ozeti": {"query": "CALL sp_kategori_ozeti();", "hedef": "kategori_film_ozeti"},
    "rewards_report": {"query": "SELECT * FROM rewards_report(1, 20.00);", "hedef": "rewards_report_sonuc"},
    "film_in_stock": {"query": "SELECT * FROM film_in_stock(1, 1);", "hedef": "film_stok_durum"},
    "film_not_in_stock": {"query": "SELECT * FROM film_not_in_stock(1, 1);", "hedef": "film_stok_durum"},
    "get_customer_balance": {"query": "SELECT get_customer_balance(1, CURRENT_TIMESTAMP);", "hedef": "musteri_bakiye"},
    "inventory_held_by_customer": {"query": "SELECT inventory_held_by_customer(1);", "hedef": "envanter_durum"},
    "inventory_in_stock": {"query": "SELECT inventory_in_stock(1);", "hedef": "envanter_durum"},
    "last_day": {"query": "SELECT last_day(CURRENT_TIMESTAMP);", "hedef": "sistem_tarihi"}
}

def etl_surecini_baslat():
    conn = None
    try:
        logging.info("ETL süreci başlatılıyor. Veritabanına bağlanılıyor...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        for task_name, task_info in TASKS.items():
            logging.info(f"BAŞLADI: Görev -> {task_name}")
            baslangic = datetime.now()
            etkilenen_satir = 0
            hata_mesaji = None
            
            try:
                cursor.execute(task_info["query"])
                etkilenen_satir = cursor.rowcount if cursor.rowcount > 0 else 0
                conn.commit()
                logging.info(f"BAŞARILI: Görev -> {task_name} | İşlenen Kayıt: {etkilenen_satir}")
            except Exception as e:
                conn.rollback()
                hata_mesaji = str(e)
                logging.error(f"HATA: Görev -> {task_name} | Detay: {hata_mesaji}")

            bitis = datetime.now()

            log_query = """
            INSERT INTO etl_log (calisan_prosedur, hedef_tablo, islenen_kayit_sayisi, hata, baslangic_zamani, bitis_zamani)
            VALUES (%s, %s, %s, %s, %s, %s);
            """
            cursor.execute(log_query, (task_name, task_info["hedef"], etkilenen_satir, hata_mesaji, baslangic, bitis))
            conn.commit()
            
            logging.info(f"BİTTİ: Görev -> {task_name} veritabanı log tablosuna kaydedildi.\n" + "-"*50)

        cursor.close()
        logging.info("Tüm ETL süreci tamamlandı.")
        
    except Exception as error:
        logging.error(f"Sistem Hatası: {error}")
    finally:
        if conn is not None:
            conn.close()

if __name__ == "__main__":
    etl_surecini_baslat()