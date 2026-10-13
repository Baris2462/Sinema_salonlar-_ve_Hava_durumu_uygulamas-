import os
import requests
import psycopg2
from datetime import datetime

API_KEY = "1d9b9c95aabc5f899b1c1921c774285a"
SEHIRLER = ["Erzincan", "Ankara", "Istanbul", "Izmir"]

windows_ip = os.popen("ip route show default | awk '{print $3}'").read().strip()

DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "12345",
    "host": windows_ip,
    "port": "5432"
}

def hava_durumu_yukle():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gunluk_hava_durumu (
            id SERIAL PRIMARY KEY,
            sehir VARCHAR(50),
            sicaklik NUMERIC(5,2),
            hissedilen NUMERIC(5,2),
            durum VARCHAR(100),
            tarih TIMESTAMP
        );
    """)

    for sehir in SEHIRLER:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={sehir}&appid={API_KEY}&units=metric&lang=tr"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            sicaklik = data['main']['temp']
            hissedilen = data['main']['feels_like']
            durum = data['weather'][0]['description']
            kayit_zamani = datetime.now()

            cursor.execute("""
                INSERT INTO gunluk_hava_durumu (sehir, sicaklik, hissedilen, durum, tarih)
                VALUES (%s, %s, %s, %s, %s)
            """, (sehir, sicaklik, hissedilen, durum, kayit_zamani))

    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    hava_durumu_yukle()