import os
import tkinter as tk
from tkinter import ttk
import psycopg2

windows_ip = os.popen("ip route show default | awk '{print $3}'").read().strip()

DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "12345",
    "host": windows_ip,
    "port": "5432"
}

def veri_cek():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT id, film_adi, sinema_salonu, sehir, sicaklik, hava_durumu, islem_tarihi FROM vizyon_sinema_hava ORDER BY id ASC;")
    satirlar = cursor.fetchall()
    cursor.close()
    conn.close()
    return satirlar

root = tk.Tk()
root.title("Vizyon Sinema ve Hava Durumu")
root.geometry("1200x500")

kolonlar = ("ID", "Film Adı", "Sinema Salonu", "Şehir", "Sıcaklık", "Hava Durumu", "İşlem Tarihi")
tablo = ttk.Treeview(root, columns=kolonlar, show="headings")

for kolon in kolonlar:
    tablo.heading(kolon, text=kolon)
    tablo.column(kolon, width=150)

tablo.pack(fill="both", expand=True)

for satir in veri_cek():
    tablo.insert("", "end", values=satir)

root.mainloop()