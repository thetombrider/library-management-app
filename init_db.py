from backend.database import engine, Base
from backend.models.book import Book
from backend.models.user import User
from backend.models.loan import Loan

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()