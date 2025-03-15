from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime
from jose import JWTError, jwt

from backend.models.user import User
from backend.models.loan import Loan
from backend.schemas.user import UserCreate, UserUpdate, UserDelete
from backend.security import get_password_hash, verify_password, decode_token, SECRET_KEY, ALGORITHM
from backend.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def get_users(db: Session, skip: int = 0, limit: int = 10):
    return db.query(User).offset(skip).limit(limit).all()

def get_user(db: Session, user_id: int):
    """Ottiene un utente tramite ID."""
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    """Ottiene un utente tramite email."""
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate):
    """Crea un nuovo utente."""
    # Hashing della password se fornita
    hashed_password = get_password_hash(user.password) if user.password else None
    
    # Crea l'oggetto utente
    db_user = User(
        name=user.name,
        email=user.email,
        hashed_password=hashed_password,
        role="user",  # Default: utente normale
        created_at=datetime.utcnow(),
        is_active=True
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user: UserUpdate):
    """Aggiorna un utente esistente."""
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utente non trovato")
    
    # Aggiorna i campi forniti
    user_data = user.model_dump(exclude_unset=True)
    
    # Gestione speciale per la password
    if "password" in user_data:
        password = user_data.pop("password")
        if password:
            user_data["hashed_password"] = get_password_hash(password)
    
    # Aggiorna tutti gli altri campi
    for key, value in user_data.items():
        setattr(db_user, key, value)
        
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    """Elimina un utente."""
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utente non trovato")
    
    # Check for any outstanding loans associated with the user
    outstanding_loans = db.query(Loan).filter(
        Loan.user_id == user_id, 
        (Loan.return_date == None) | (Loan.return_date > datetime.utcnow())
    ).count()
    
    if outstanding_loans > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Impossibile eliminare un utente con prestiti attivi")
    
    db.delete(db_user)
    db.commit()
    return UserDelete(message="Utente eliminato con successo", user=db_user)

def authenticate_user(db: Session, email: str, password: str):
    """Autentica un utente tramite email e password."""
    user = get_user_by_email(db, email)
    if not user:
        return False
    if not user.hashed_password:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def update_last_login(db: Session, user_id: int):
    """Aggiorna il timestamp dell'ultimo accesso."""
    db_user = get_user(db, user_id)
    if db_user:
        db_user.last_login = datetime.utcnow()
        db.commit()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Ottiene l'utente corrente dal token JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenziali non valide",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decodifica il token
        payload = decode_token(token)
        if payload is None:
            raise credentials_exception
            
        email = payload.get("sub")
        user_id = payload.get("user_id")
        if email is None or user_id is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
        
    # Ottieni l'utente dal database
    user = get_user(db, user_id)
    if user is None:
        raise credentials_exception
        
    return user