from src.database import engine, Base
from src.models.book import Book
from src.models.user import User
from src.models.loan import Loan

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()