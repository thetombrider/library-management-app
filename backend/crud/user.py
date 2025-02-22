from sqlalchemy.orm import Session
from backend.models.user import User
from backend.models.loan import Loan
from backend.schemas.user import UserCreate, UserUpdate, UserDelete
from fastapi import HTTPException, status
from datetime import datetime

def get_users(db: Session, skip: int = 0, limit: int = 10):
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, user: UserCreate):
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user: UserUpdate):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    for key, value in user.model_dump().items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Check for any outstanding loans associated with the user
    outstanding_loans = db.query(Loan).filter(Loan.user_id == user_id, Loan.return_date > datetime.utcnow()).count()
    print(f"found outstanding loans: {outstanding_loans}")
    if outstanding_loans > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete user with outstanding loans")
    
    db.delete(db_user)
    db.commit()
    return UserDelete(message="User deleted successfully", user=db_user)