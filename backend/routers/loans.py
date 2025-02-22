from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend import crud, models, schemas
from backend.database import get_db

router = APIRouter()

@router.get("/", response_model=list[schemas.Loan])
def read_loans(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    loans = crud.loan.get_loans(db, skip=skip, limit=limit)
    return loans

@router.post("/", response_model=schemas.Loan)
def create_loan(loan: schemas.LoanCreate, db: Session = Depends(get_db)):
    return crud.loan.create_loan(db=db, loan=loan)

@router.put("/{loan_id}", response_model=schemas.Loan)
def update_loan(loan_id: int, loan: schemas.LoanUpdate, db: Session = Depends(get_db)):
    return crud.loan.update_loan(db=db, loan_id=loan_id, loan=loan)

@router.delete("/{loan_id}", response_model=schemas.LoanDelete)
def delete_loan(loan_id: int, db: Session = Depends(get_db)):
    deleted_loan = crud.loan.delete_loan(db=db, loan_id=loan_id)
    return schemas.LoanDelete(message="Loan deleted successfully", loan=deleted_loan["loan"])