import psycopg2
import random
from faker import Faker
import numpy as np

# Faker nesnesi oluştur
fake = Faker()

# Veritabanı bağlantısı
conn = psycopg2.connect(
    dbname="netflix_db",
    user="postgres",
    password="2228",
    host="localhost"
)
cur = conn.cursor()

# Tabloları oluştur
cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL
    );
    
    CREATE TABLE IF NOT EXISTS movies (
        id SERIAL PRIMARY KEY,
        title VARCHAR(200) NOT NULL,
        genre VARCHAR(50) NOT NULL,
        year INTEGER NOT NULL
    );
    
    CREATE TABLE IF NOT EXISTS ratings (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        movie_id INTEGER REFERENCES movies(id),
        rating INTEGER CHECK (rating >= 1 AND rating <= 5)
    );
""")

# Film türleri
genres = ['Action', 'Comedy', 'Drama', 'Horror', 'Romance', 'Sci-Fi', 
          'Thriller', 'Documentary', 'Animation', 'Adventure']

# Kullanıcıları oluştur
for _ in range(50):
    cur.execute("INSERT INTO users (name) VALUES (%s)", (fake.name(),))

# Filmleri oluştur
for _ in range(100):
    title = fake.catch_phrase()
    genre = random.choice(genres)
    year = random.randint(1990, 2023)
    cur.execute(
        "INSERT INTO movies (title, genre, year) VALUES (%s, %s, %s)",
        (title, genre, year)
    )

# Kullanıcı ID'lerini ve film ID'lerini al
cur.execute("SELECT id FROM users")
user_ids = [row[0] for row in cur.fetchall()]

cur.execute("SELECT id FROM movies")
movie_ids = [row[0] for row in cur.fetchall()]

# Her kullanıcı için 10 rastgele film seç ve puan ver
for user_id in user_ids:
    # Rastgele 10 film seç
    selected_movies = random.sample(movie_ids, 10)
    
    for movie_id in selected_movies:
        # Normal dağılımdan puan üret (ortalama 3, standart sapma 1)
        rating = int(np.random.normal(3, 1))
        # Puanı 1-5 aralığında sınırla
        rating = max(1, min(5, rating))
        
        cur.execute(
            "INSERT INTO ratings (user_id, movie_id, rating) VALUES (%s, %s, %s)",
            (user_id, movie_id, rating)
        )

# Değişiklikleri kaydet ve bağlantıyı kapat
conn.commit()
cur.close()
conn.close()

print("Veritabanı ve tablolar başarıyla oluşturuldu ve dolduruldu!") 