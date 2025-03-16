from backend.database import Base, engine
from backend.models import Book, User, Loan

def init_database():
    print("Creazione delle tabelle nel database...")
    Base.metadata.create_all(bind=engine)
    print("Database inizializzato con successo!")

if __name__ == "__main__":
    init_database()