import sys
from backend.database import SessionLocal
from backend.models.user import User
from backend.crud.user import get_password_hash
import argparse

def create_admin_user(username, password, name):
    db = SessionLocal()
    
    # Verifica se l'utente esiste già
    existing_user = db.query(User).filter(User.email == username).first()
    if existing_user:
        print(f"L'utente {username} esiste già.")
        return
    
    # Crea il nuovo utente admin
    hashed_password = get_password_hash(password)
    db_user = User(email=username, 
                   hashed_password=hashed_password,
                   name=name,
                   role="admin",
                   is_active=True)
    
    db.add(db_user)
    db.commit()
    print(f"Utente admin {username} creato con successo!")
    db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Crea un utente admin')
    parser.add_argument('username', help='Email/username dell\'utente admin')
    parser.add_argument('password', help='Password dell\'utente admin')
    parser.add_argument('name', help='Nome completo dell\'utente admin')
    
    args = parser.parse_args()
    
    create_admin_user(args.username, args.password, args.name)