from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend import crud, models, schemas
from backend.database import get_db

router = APIRouter()

@router.get("/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = crud.user.get_users(db, skip=skip, limit=limit)
    return users

@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.user.create_user(db=db, user=user)

@router.put("/{user_id}", response_model=schemas.User)
def update_user(user_id: int, user: schemas.UserUpdate, db: Session = Depends(get_db)):
    return crud.user.update_user(db=db, user_id=user_id, user=user)

@router.delete("/{user_id}", response_model=schemas.UserDelete)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    deleted_user = crud.user.delete_user(db=db, user_id=user_id)
    return schemas.UserDelete(message="User deleted successfully", user=deleted_user["user"])