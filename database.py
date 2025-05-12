from sqlalchemy.orm import sessionmaker
from models import engine, User, FlightResult
from datetime import datetime
import logging


Session = sessionmaker(bind=engine)

def get_user(user_id: int) -> User:
    try:
        session = Session()
        user = session.query(User).filter(User.user_id == user_id).first()
        return user
    except Exception as e:
        raise e
    finally:
        session.close()

def create_or_update_user(user_id: int, lastname: str, firstname: str, group_name: str, birthdate: str) -> User:

    try:
        session = Session()
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user:
            user = User(user_id=user_id)
        
        user.lastname = lastname
        user.firstname = firstname
        user.group_name = group_name
        user.birthdate = birthdate
        
        session.add(user)
        session.commit()
        return user
    except Exception as e:
        if session:
            session.rollback()
        raise e
    finally:
        session.close()

def add_flight_result(user_id: int, simulator: str, track: str, mode: str, best_time: float, image_path: str = None) -> FlightResult:
    try:
        session = Session()
        
       
        old_result = session.query(FlightResult).filter(
            FlightResult.user_id == user_id,
            FlightResult.simulator == simulator,
            FlightResult.track == track,
            FlightResult.mode == mode
        ).first()
        
        
        if old_result:
            if best_time < old_result.best_time:
                
                if old_result.image_path:
                    try:
                        import os
                        if os.path.exists(old_result.image_path):
                            os.remove(old_result.image_path)
                    except Exception as e:
                        logging.error(f"Ошибка при удалении старого изображения: {str(e)}")
                
                session.delete(old_result)
                session.commit()
            else:
                
                session.close()
                raise ValueError("Новый результат хуже предыдущего")
        
      
        result = FlightResult(
            user_id=user_id,
            simulator=simulator,
            track=track,
            mode=mode,
            best_time=best_time,
            date=datetime.now(),
            image_path=image_path
        )
        session.add(result)
        session.commit()
        return result
    except Exception as e:
        if session:
            session.rollback()
        raise e
    finally:
        session.close()

def get_leaderboard(simulator: str, mode: str, track: str, limit: int = 10):

    try:
        session = Session()
        results = session.query(
            User.lastname,
            User.firstname,
            User.group_name,
            FlightResult.best_time
        ).join(
            FlightResult,
            User.user_id == FlightResult.user_id
        ).filter(
            FlightResult.simulator == simulator,
            FlightResult.mode == mode,
            FlightResult.track == track
        ).order_by(
            FlightResult.best_time.asc()
        ).limit(limit).all()
        
        return results
    except Exception as e:
        raise e
    finally:
        session.close() 
