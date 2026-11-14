from sqlalchemy.orm import Session
import logging
from app.models.user import User

logger = logging.getLogger(__name__)

def get_by_id(db: Session, user_id: int):
    logger.info("Fetching user by ID: %s", user_id)

    user = db.query(User).filter(User.id == user_id).first()

    if user:
        logger.info("User found with ID: %s", user_id)
    else:
        logger.info("No user found with ID: %s", user_id)

    return user

def get_by_email(db: Session, email: str):
    logger.info("Fetching user by email: %s", email)
    user = db.query(User).filter(User.email == email).first()

    if user:
        logger.info("User found with email: %s", email)
    else:
        logger.info("No user found with email: %s", email)

    return user

def create(db: Session, db_user: User):
    logger.info("Creating new user with email: %s", db_user.email)

    db.add(db_user)
    db.flush()

    logger.info("User added to database session with ID: %s",db_user.id)

    return db_user