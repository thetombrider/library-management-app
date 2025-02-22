import os
from fastapi import FastAPI
from src.routers import books, loans, users
from init_db import init_db

# Check if the database exists
if not os.path.exists("src/books.db"):
    print("Database not found. Initializing database...")
    init_db()

app = FastAPI()

app.include_router(books.router, prefix="/books", tags=["books"])
app.include_router(loans.router, prefix="/loans", tags=["loans"])
app.include_router(users.router, prefix="/users", tags=["users"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Library Management API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

