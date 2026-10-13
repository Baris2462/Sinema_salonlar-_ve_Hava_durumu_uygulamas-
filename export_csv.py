import os
import pandas as pd
from sqlalchemy import create_engine

# WSL içinden Windows IP adresini dinamik al
windows_ip = os.popen("ip route show default | awk '{print $3}'").read().strip()

# Veritabanı bağlantı bilgileri
DB_USER = "postgres"
DB_PASSWORD = "12345"  # PostgreSQL şifrenizi girin
DB_HOST = windows_ip
DB_PORT = "5432"
DB_NAME = "postgres"

# SQLAlchemy Engine oluştur
connection_string = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
engine = create_engine(connection_string)

# SELECT sorgusunu çalıştır ve CSV olarak kaydet
table_name = "family_tree"  # Çekmek istediğiniz tablo adı
df = pd.read_sql(f"SELECT * FROM {table_name}", con=engine)

# CSV dosyasına aktar
output_filename = "cikti.csv"
df.to_csv(output_filename, index=False, encoding="utf-8-sig")

print(
    f"'{table_name}' tablosu başarıyla '{output_filename}' olarak kaydedildi."
)
