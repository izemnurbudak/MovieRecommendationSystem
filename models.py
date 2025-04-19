from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    
    # İlişkiler
    ratings = relationship("Rating", back_populates="user")

class Movie(Base):
    __tablename__ = 'movies'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    genre = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    
    # İlişkiler
    ratings = relationship("Rating", back_populates="movie")

class Rating(Base):
    __tablename__ = 'ratings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    movie_id = Column(Integer, ForeignKey('movies.id'), nullable=False)
    rating = Column(Float, nullable=False)
    
    # İlişkiler
    user = relationship("User", back_populates="ratings")
    movie = relationship("Movie", back_populates="ratings")

# Veritabanı bağlantısı
engine = create_engine('postgresql://postgres:2228@localhost/netflix_db')

# Tabloları oluştur
def create_tables():
    Base.metadata.create_all(engine) 