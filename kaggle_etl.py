import os
import pandas as pd
import psycopg2
from kaggle.api.kaggle_api_extended import KaggleApi

windows_ip = os.popen("ip route show default | awk '{print $3}'").read().strip()

DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "12345",
    "host": windows_ip,
    "port": "5432"
}

def kaggle_kripto_yukle():
    api = KaggleApi()
    api.authenticate()

    # Kripto para veri setinin indirilmesi
    dataset_name = 'sudalairajkumar/cryptocurrencypricehistory'
    api.dataset_download_files(dataset_name, path='./kaggle_kripto', unzip=True)

    # Bitcoin verilerinin okunması (İlk 100 satır)
    df = pd.read_csv('./kaggle_kripto/coin_Bitcoin.csv').head(100)

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kripto_fiyatlari (
            id SERIAL PRIMARY KEY,
            isim VARCHAR(50),
            tarih TIMESTAMP,
            kapanis_fiyati NUMERIC,
            hacim NUMERIC
        );
    """)

    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO kripto_fiyatlari (isim, tarih, kapanis_fiyati, hacim)
            VALUES (%s, %s, %s, %s)
        """, (row['Name'], row['Date'], row['Close'], row['Volume']))
    
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    kaggle_kripto_yukle()
