from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from models import Base, User, Movie, Rating, engine
import random
from faker import Faker

# Faker nesnesi oluştur
fake = Faker()

# Veritabanı oturumu oluştur
db = Session(engine)

# Tabloları oluştur
Base.metadata.create_all(engine)

# Film türleri
genres = ['Action', 'Comedy', 'Drama', 'Horror', 'Romance', 'Sci-Fi', 
          'Thriller', 'Documentary', 'Animation', 'Adventure']

# 50 kullanıcı oluştur
for _ in range(50):
    user = User(name=fake.name())
    db.add(user)

# Değişiklikleri kaydet
db.commit()

# 100 film oluştur
for _ in range(100):
    movie = Movie(
        title=fake.catch_phrase(),
        genre=random.choice(genres),
        year=random.randint(1990, 2023)
    )
    db.add(movie)

# Değişiklikleri kaydet
db.commit()

# Her kullanıcı için 10 rastgele film seç ve puan ver
users = db.query(User).all()
movies = db.query(Movie).all()

for user in users:
    # Rastgele 10 film seç
    selected_movies = random.sample(movies, 10)
    
    for movie in selected_movies:
        # Normal dağılımdan puan üret (ortalama 3, standart sapma 1)
        rating_value = random.normalvariate(3, 1)
        # Puanı 1-5 aralığında sınırla
        rating_value = max(1, min(5, rating_value))
        
        rating = Rating(
            user_id=user.id,
            movie_id=movie.id,
            rating=round(rating_value, 2)
        )
        db.add(rating)

# Değişiklikleri kaydet
db.commit()

print("Örnek veriler başarıyla oluşturuldu!") 