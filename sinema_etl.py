import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import psycopg2
import random

API_KEY = "1d9b9c95aabc5f899b1c1921c774285a"
windows_ip = os.popen("ip route show default | awk '{print $3}'").read().strip()

DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "12345",
    "host": windows_ip,
    "port": "5432"
}

SEHIRLER_81 = [
    "Adana", "Adiyaman", "Afyonkarahisar", "Agri", "Aksaray", "Amasya", "Ankara", "Antalya", "Ardahan", "Artvin",
    "Aydin", "Balikesir", "Bartin", "Batman", "Bayburt", "Bilecik", "Bingol", "Bitlis", "Bolu", "Burdur",
    "Bursa", "Canakkale", "Cankiri", "Corum", "Denizli", "Diyarbakir", "Duzce", "Edirne", "Elazig", "Erzincan",
    "Erzurum", "Eskisehir", "Gaziantep", "Giresun", "Gumushane", "Hakkari", "Hatay", "Igdir", "Isparta", "Istanbul",
    "Izmir", "Kahramanmaras", "Karabuk", "Karaman", "Kars", "Kastamonu", "Kayseri", "Kilis", "Kirikkale", "Kirklareli",
    "Kirsehir", "Kocaeli", "Konya", "Kutahya", "Malatya", "Manisa", "Mardin", "Mersin", "Mugla", "Mus",
    "Nevsehir", "Nigde", "Ordu", "Osmaniye", "Rize", "Sakarya", "Samsun", "Sanliurfa", "Siirt", "Sinop",
    "Sirnak", "Sivas", "Tekirdag", "Tokat", "Trabzon", "Tunceli", "Usak", "Van", "Yalova", "Yozgat", "Zonguldak"
]

SALONLAR = [
    "Paribu Cineverse", "Cinens Sinemalari", "Avsar Sinemalari", 
    "Cinetime", "Prestige Sinemalari", "Site Sinemalari", "Büyülü Fener"
]

def sinema_hava_etl():
    url = "https://www.sinemalar.com/filmler/vizyondaki-filmler"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }
    
    filmler = []
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            for film in soup.find_all("div", class_="title"):
                t = film.text.strip()
                if t and t not in filmler:
                    filmler.append(t)
    except Exception:
        pass

    if not filmler:
        filmler = [
            "Dune: Part Two", "Oppenheimer", "Inside Out 2", "Deadpool & Wolverine", 
            "Gladiator II", "Joker: Folie a Deux", "Interstellar", "Inception"
        ]

    sinema_verisi = []
    for sehir in SEHIRLER_81:
        sinema_verisi.append({
            "film_adi": random.choice(filmler),
            "sinema_salonu": random.choice(SALONLAR),
            "sehir": sehir
        })

    df_sinema = pd.DataFrame(sinema_verisi, columns=["film_adi", "sinema_salonu", "sehir"])
    kullanilan_sehirler = df_sinema['sehir'].unique()
    hava_durumu_verisi = []

    for sehir in kullanilan_sehirler:
        weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={sehir}&appid={API_KEY}&units=metric&lang=tr"
        try:
            w_resp = requests.get(weather_url, timeout=5)
            if w_resp.status_code == 200:
                data = w_resp.json()
                hava_durumu_verisi.append({
                    "sehir": sehir,
                    "sicaklik": data['main']['temp'],
                    "hava_durumu": data['weather'][0]['description']
                })
            else:
                hava_durumu_verisi.append({"sehir": sehir, "sicaklik": None, "hava_durumu": "Bilinmiyor"})
        except Exception:
            hava_durumu_verisi.append({"sehir": sehir, "sicaklik": None, "hava_durumu": "Bilinmiyor"})

    df_hava = pd.DataFrame(hava_durumu_verisi)
    df_final = pd.merge(df_sinema, df_hava, on="sehir", how="left")

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vizyon_sinema_hava (
            id SERIAL PRIMARY KEY,
            film_adi VARCHAR(255),
            sinema_salonu VARCHAR(255),
            sehir VARCHAR(50),
            sicaklik NUMERIC(5,2),
            hava_durumu VARCHAR(100),
            islem_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    for _, row in df_final.iterrows():
        cursor.execute("""
            INSERT INTO vizyon_sinema_hava (film_adi, sinema_salonu, sehir, sicaklik, hava_durumu)
            VALUES (%s, %s, %s, %s, %s)
        """, (row['film_adi'], row['sinema_salonu'], row['sehir'], row['sicaklik'], row['hava_durumu']))

    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    sinema_hava_etl()