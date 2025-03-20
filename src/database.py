from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from datetime import datetime

# Загрузка переменных окружения
load_dotenv('config/.env')
DATABASE_URL = os.getenv('DATABASE_URL')

# Создание базового класса для моделей
Base = declarative_base()

class Task(Base):
    """Модель задачи"""
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

# Создание подключения к базе данных
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Создание таблиц
def init_db():
    Base.metadata.create_all(engine)

# Функции для работы с задачами
def create_task(user_id: int, title: str, description: str = None) -> Task:
    """Создание новой задачи"""
    session = SessionLocal()
    task = Task(user_id=user_id, title=title, description=description)
    session.add(task)
    session.commit()
    session.refresh(task)
    session.close()
    return task

def get_tasks(user_id: int, completed: bool = None) -> list[Task]:
    """Получение списка задач пользователя"""
    session = SessionLocal()
    query = session.query(Task).filter(Task.user_id == user_id)
    if completed is not None:
        query = query.filter(Task.is_completed == completed)
    tasks = query.all()
    session.close()
    return tasks

def complete_task(task_id: int, user_id: int) -> bool:
    """Отметить задачу как выполненную"""
    session = SessionLocal()
    task = session.query(Task).filter(
        Task.id == task_id,
        Task.user_id == user_id
    ).first()
    if task:
        task.is_completed = True
        task.completed_at = datetime.utcnow()
        session.commit()
        session.close()
        return True
    session.close()
    return False

def delete_task(task_id: int, user_id: int) -> bool:
    """Удаление задачи"""
    session = SessionLocal()
    task = session.query(Task).filter(
        Task.id == task_id,
        Task.user_id == user_id
    ).first()
    if task:
        session.delete(task)
        session.commit()
        session.close()
        return True
    session.close()
    return False 