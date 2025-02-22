import os
from fastapi import FastAPI
from backend.routers import books_router, loans_router, users_router
from init_db import init_db

# Check if the database exists
if not os.path.exists("books.db"):
    print("Database not found. Initializing database...")
    init_db()

app = FastAPI()

app.include_router(books_router, prefix="/books", tags=["books"])
app.include_router(loans_router, prefix="/loans", tags=["loans"])
app.include_router(users_router, prefix="/users", tags=["users"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Library Management API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

