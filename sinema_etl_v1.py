import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import psycopg2
import time

API_KEY = "1d9b9c95aabc5f899b1c1921c774285a"
windows_ip = os.popen("ip route show default | awk '{print $3}'").read().strip()

DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "12345",
    "host": windows_ip,
    "port": "5432"
}

def sinema_hava_etl():
    base_url = "https://www.sinemalar.com"
    vizyon_url = f"{base_url}/filmler/vizyondaki"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'}
    
    sinema_verisi = []
    
    try:
        response = requests.get(vizyon_url, headers=headers, timeout=10)
        print(f"1. Vizyon sayfası HTTP Kodu: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            
            film_linkleri = []
            # CSS Selector: 'link' sınıfına sahip ve href içinde '/film/' geçen a etiketleri
            for a_tag in soup.select("a.link[href*='/film/']"): 
                href = a_tag.get('href')
                if href and href not in film_linkleri:
                    film_linkleri.append(href)
                    if len(film_linkleri) == 3:
                        break
            
            print(f"2. Bulunan Film Linki Sayısı: {len(film_linkleri)}")

            for link in film_linkleri:
                if not link.startswith("http"):
                    link = base_url + link
                
                seans_url = link.replace("/film/", "/seans/")
                print(f"3. Seans URL taranıyor: {seans_url}")
                
                s_resp = requests.get(seans_url, headers=headers, timeout=10)
                if s_resp.status_code == 200:
                    s_soup = BeautifulSoup(s_resp.content, "html.parser")
                    
                    film_adi_tag = s_soup.find("h1")
                    film_adi = film_adi_tag.text.strip() if film_adi_tag else "Bilinmeyen Film"
                    
                    sehir_linkleri = []
                    # CSS Selector ile 'metadata-card' sınıfı içeren a etiketleri aranır
                    for a_sehir in s_soup.select("a.metadata-card"):
                        sehir_href = a_sehir.get('href')
                        sehir_h3 = a_sehir.find("h3")
                        sehir_adi = sehir_h3.text.strip() if sehir_h3 else "Bilinmeyen"
                        
                        if sehir_href:
                            tam_link = base_url + sehir_href if not sehir_href.startswith("http") else sehir_href
                            sehir_linkleri.append({"url": tam_link, "sehir": sehir_adi})
                    
                    print(f"   -> Bulunan Şehir Sayısı ({film_adi}): {len(sehir_linkleri)}")

                    for sehir_bilgisi in sehir_linkleri:
                        c_resp = requests.get(sehir_bilgisi["url"], headers=headers, timeout=10)
                        
                        if c_resp.status_code == 200:
                            c_soup = BeautifulSoup(c_resp.content, "html.parser")
                            
                            # CSS Selector ile salon div'leri çekilir
                            salonlar = c_soup.select("div.card-title")
                            for salon_tag in salonlar:
                                temiz_sehir = sehir_bilgisi["sehir"].split()[0]
                                sinema_verisi.append({
                                    "film_adi": film_adi,
                                    "sinema_salonu": salon_tag.text.strip(),
                                    "sehir": temiz_sehir
                                })
                        
                        time.sleep(1)
                time.sleep(2)
                
    except Exception as e:
        print(f"Hata: {e}")

    print(f"4. Toplam Çekilen Salon Verisi: {len(sinema_verisi)}")

    if not sinema_verisi:
        print("İşlem durduruldu: Veritabanına yazılacak veri bulunamadı.")
        return

    df_sinema = pd.DataFrame(sinema_verisi, columns=["film_adi", "sinema_salonu", "sehir"])
    df_sinema.drop_duplicates(inplace=True)
    
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
    print("ETL işlemi tamamlandı.")

if __name__ == "__main__":
    sinema_hava_etl()