from pydantic import BaseModel, Field
from datetime import datetime, timedelta

class LoanBase(BaseModel):
    book_id: int
    user_id: int
    loan_date: datetime = Field(default_factory=datetime.utcnow)
    return_date: datetime | None = Field(default_factory=lambda: datetime.utcnow() + timedelta(days=30))

class LoanCreate(LoanBase):
    pass

class LoanUpdate(BaseModel):
    return_date: datetime

class Loan(LoanBase):
    id: int

    class Config:
        from_attributes = True