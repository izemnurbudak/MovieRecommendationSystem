from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import numpy as np
from typing import List
from pydantic import BaseModel
from models import Base, User, Movie, Rating, engine
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="Film Öneri Sistemi",
    description="KMeans algoritması kullanarak film önerileri sunan bir API",
    version="1.0.0"
)

# Ana sayfa için HTML yanıtı
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>Film Öneri Sistemi</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }
                h1 {
                    color: #333;
                }
                .endpoint {
                    background-color: #f5f5f5;
                    padding: 10px;
                    border-radius: 5px;
                    margin: 10px 0;
                }
            </style>
        </head>
        <body>
            <h1>Film Öneri Sistemi API</h1>
            <p>Bu API, KMeans algoritması kullanarak kullanıcılara film önerileri sunar.</p>
            
            <h2>Kullanılabilir Endpointler:</h2>
            <div class="endpoint">
                <strong>GET /recommend/{user_id}</strong>
                <p>Belirtilen kullanıcı ID'si için film önerileri döndürür.</p>
                <p>Örnek: <a href="/recommend/1">/recommend/1</a></p>
            </div>
            
            <p>API dokümantasyonu için: <a href="/docs">/docs</a></p>
        </body>
    </html>
    """

# Veritabanı oturumu oluştur
def get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()

# Kullanıcı-film matrisini oluştur
def create_user_movie_matrix(db: Session):
    # Tüm kullanıcı ve filmleri al
    users = db.query(User).all()
    movies = db.query(Movie).all()
    
    # Boş bir DataFrame oluştur
    user_movie_matrix = pd.DataFrame(
        0,
        index=[user.id for user in users],
        columns=[movie.id for movie in movies]
    )
    
    # Puanları doldur
    ratings = db.query(Rating).all()
    for rating in ratings:
        user_movie_matrix.loc[rating.user_id, rating.movie_id] = rating.rating
    
    return user_movie_matrix

# KMeans modelini eğit
def train_kmeans_model(db: Session):
    user_movie_matrix = create_user_movie_matrix(db)
    
    # Veriyi ölçeklendir
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(user_movie_matrix)
    
    # KMeans modelini oluştur ve eğit
    kmeans = KMeans(n_clusters=5, random_state=42)
    kmeans.fit(scaled_data)
    
    return kmeans, scaler, user_movie_matrix

class MovieRecommendation(BaseModel):
    movie_id: int
    title: str
    genre: str
    year: int
    predicted_rating: float

@app.get("/recommend/{user_id}", 
         response_model=List[MovieRecommendation],
         summary="Kullanıcı için film önerileri",
         description="Belirtilen kullanıcı ID'si için en iyi 10 film önerisini döndürür.")
async def get_recommendations(user_id: int):
    try:
        # Veritabanı oturumu oluştur
        db = Session(engine)
        
        # Kullanıcının var olup olmadığını kontrol et
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"ID'si {user_id} olan kullanıcı bulunamadı."
            )
        
        # Modeli eğit
        kmeans_model, scaler, user_movie_matrix = train_kmeans_model(db)
        
        # Kullanıcının küme numarasını bul
        user_ratings = user_movie_matrix.loc[user_id].values.reshape(1, -1)
        scaled_ratings = scaler.transform(user_ratings)
        cluster = kmeans_model.predict(scaled_ratings)[0]
        
        # Aynı kümedeki diğer kullanıcıları bul
        cluster_users = user_movie_matrix[kmeans_model.labels_ == cluster]
        
        # Kullanıcının henüz izlemediği filmleri bul
        unwatched_movies = user_movie_matrix.columns[user_ratings[0] == 0]
        
        if len(unwatched_movies) == 0:
            raise HTTPException(
                status_code=404,
                detail="Kullanıcı için önerilebilecek yeni film bulunamadı."
            )
        
        # Film önerilerini hesapla
        recommendations = []
        
        for movie_id in unwatched_movies:
            # Filmin ortalama puanını hesapla
            avg_rating = cluster_users[movie_id].mean()
            
            # Film bilgilerini al
            movie = db.query(Movie).filter(Movie.id == movie_id).first()
            
            if movie and avg_rating > 0:
                recommendations.append(MovieRecommendation(
                    movie_id=movie.id,
                    title=movie.title,
                    genre=movie.genre,
                    year=movie.year,
                    predicted_rating=round(avg_rating, 2)
                ))
        
        if not recommendations:
            raise HTTPException(
                status_code=404,
                detail="Kullanıcı için uygun film önerisi bulunamadı."
            )
        
        # Önerileri puanlarına göre sırala
        recommendations.sort(key=lambda x: x.predicted_rating, reverse=True)
        
        # En iyi 10 öneriyi döndür
        return recommendations[:10]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Bir hata oluştu: {str(e)}"
        )
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001) 