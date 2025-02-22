from pydantic import BaseModel

class BookBase(BaseModel):
    title: str
    author: str
    description: str
    isbn: str | None = None

class BookCreate(BookBase):
    pass

class BookUpdate(BookBase):
    pass

class Book(BookBase):
    id: int

    class Config:
        from_attributes = True

class BookDelete(BaseModel):
    message: str
    book: Book