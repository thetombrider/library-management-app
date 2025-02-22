from pydantic import BaseModel, Field
from datetime import datetime, timedelta, timezone

class LoanBase(BaseModel):
    book_id: int
    user_id: int
    loan_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    return_date: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=30))

class LoanCreate(LoanBase):
    pass

class LoanUpdate(BaseModel):
    return_date: datetime

class Loan(LoanBase):
    id: int

    class Config:
        from_attributes = True

class LoanDelete(BaseModel):
    message: str
    loan: Loan