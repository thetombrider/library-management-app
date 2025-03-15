from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserLogin(BaseModel):
    """Schema per il login."""
    email: EmailStr
    password: str

class UserCreate(UserBase):
    """Schema per la creazione di un utente."""
    password: str = None  # Opzionale per compatibilità con il codice esistente

class UserUpdate(BaseModel):
    """Schema per l'aggiornamento di un utente."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class User(UserBase):
    """Schema per la risposta con i dati dell'utente."""
    id: int
    role: str = "user"
    last_login: Optional[datetime] = None
    is_active: bool = True
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserDelete(BaseModel):
    message: str
    user: User

class UserInDB(User):
    """Schema interno con dati sensibili."""
    hashed_password: Optional[str] = None

class Token(BaseModel):
    """Schema per il token di accesso."""
    access_token: str
    token_type: str
    user: User