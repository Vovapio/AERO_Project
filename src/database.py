from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
from dotenv import load_dotenv
from datetime import datetime
import enum

# Загрузка переменных окружения
load_dotenv('config/.env')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///database/bot.db')

# Создание базового класса для моделей
Base = declarative_base()

class Simulator(enum.Enum):
    FPV_FREERIDER = "FPV Freerider"
    DCL_THE_GAME = "DCL The Game"
    LIFTOFF = "Liftoff"

class FlightMode(enum.Enum):
    SELF_LEVELING = "Self-Leveling"
    ACRO = "Acro"

class Map(enum.Enum):
    MAP1 = "map1"
    MAP2 = "map2"

class User(Base):
    """Модель пользователя"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    group = Column(String, nullable=False)
    birth_date = Column(DateTime, nullable=False)
    is_mentor = Column(Boolean, default=False)
    mentor_groups = Column(String, nullable=True)  # Для наставников: список групп через запятую
    created_at = Column(DateTime, default=datetime.utcnow)
    
    results = relationship("Result", back_populates="user")

class Result(Base):
    """Модель результата полета"""
    __tablename__ = 'results'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    simulator = Column(Enum(Simulator), nullable=False)
    flight_mode = Column(Enum(FlightMode), nullable=False)
    map_name = Column(Enum(Map), nullable=False)
    time = Column(Float, nullable=False)
    photo_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="results")

# Создание подключения к базе данных
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Создание таблиц
def init_db():
    Base.metadata.create_all(engine)

# Функции для работы с пользователями
def get_or_create_user(telegram_id: int, first_name: str, last_name: str, group: str, birth_date: datetime) -> User:
    """Получение или создание пользователя"""
    with SessionLocal() as session:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(
                telegram_id=telegram_id,
                first_name=first_name,
                last_name=last_name,
                group=group,
                birth_date=birth_date
            )
            session.add(user)
            session.commit()
            session.refresh(user)
        else:
            # Обновляем данные существующего пользователя
            user.first_name = first_name
            user.last_name = last_name
            user.group = group
            user.birth_date = birth_date
            session.commit()
            session.refresh(user)
        
        # Создаем новый объект с данными из базы
        return User(
            id=user.id,
            telegram_id=user.telegram_id,
            first_name=user.first_name,
            last_name=user.last_name,
            group=user.group,
            birth_date=user.birth_date,
            is_mentor=user.is_mentor,
            mentor_groups=user.mentor_groups,
            created_at=user.created_at
        )

# Функции для работы с результатами
def add_result(user_id: int, simulator: Simulator, flight_mode: FlightMode, map_name: Map, time: float, photo_path: str = None) -> Result:
    """Добавление нового результата"""
    session = SessionLocal()
    result = Result(
        user_id=user_id,
        simulator=simulator,
        flight_mode=flight_mode,
        map_name=map_name,
        time=time,
        photo_path=photo_path
    )
    session.add(result)
    session.commit()
    session.refresh(result)
    session.close()
    return result

def get_leaderboard(simulator: Simulator, flight_mode: FlightMode, map_name: Map, limit: int = 10) -> list[tuple]:
    """Получение таблицы лидеров"""
    session = SessionLocal()
    results = session.query(Result, User).join(User).filter(
        Result.simulator == simulator,
        Result.flight_mode == flight_mode,
        Result.map_name == map_name
    ).order_by(Result.time.asc()).limit(limit).all()
    
    leaderboard = []
    for result, user in results:
        leaderboard.append({
            'time': result.time,
            'name': f"{user.last_name} {user.first_name}",
            'group': user.group
        })
    
    session.close()
    return leaderboard 