from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models.user import User
from backend.security import get_password_hash
from datetime import datetime

def create_admin_user(email="admin@biblioteca.it", password="admin", name="Amministratore"):
    """Crea un utente admin se non esiste già."""
    db = SessionLocal()
    
    try:
        # Verifica se l'admin esiste già
        admin = db.query(User).filter(User.email == email).first()
        
        if admin:
            print(f"L'utente admin ({email}) esiste già.")
            return
        
        # Crea l'utente admin
        hashed_password = get_password_hash(password)
        admin_user = User(
            name=name,
            email=email,
            hashed_password=hashed_password,
            role="admin",
            created_at=datetime.utcnow(),
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        print(f"Utente admin creato con successo: {email}")
        
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    
    # Controlla se sono stati forniti parametri
    if len(sys.argv) > 1:
        password = sys.argv[1]
        email = sys.argv[2] if len(sys.argv) > 2 else "admin@biblioteca.it"
        name = sys.argv[3] if len(sys.argv) > 3 else "Amministratore"
        create_admin_user(email, password, name)
    else:
        create_admin_user()
    
    print("Script completato.")