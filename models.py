from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True)
    lastname = Column(String)
    firstname = Column(String)
    group_name = Column(String)
    birthdate = Column(String)
    
    results = relationship("FlightResult", back_populates="user")

class FlightResult(Base):
    __tablename__ = 'flight_results'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    simulator = Column(String)
    track = Column(String)
    mode = Column(String)
    best_time = Column(Float)
    date = Column(DateTime, default=datetime.now)
    image_path = Column(String, nullable=True)  # Путь к изображению

    user = relationship("User", back_populates="results")


engine = create_engine('sqlite:///fpv_leaderboard.db')
Base.metadata.create_all(engine) 
