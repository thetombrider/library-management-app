from pydantic import BaseModel

class BookBase(BaseModel):
    title: str | None = None
    author: str | None = None
    description: str | None = None
    isbn: str 
    publisher: str | None = None
    publish_year: int | None = None
    owner_id: int | None = None
    # Non includiamo cover_image qui perché sarà gestito separatamente

class BookCreate(BookBase):
    pass

class BookUpdate(BookBase):
    pass

class Book(BookBase):
    id: int
    has_cover: bool = False  # Flag per indicare se il libro ha una copertina

    class Config:
        from_attributes = True

class BookDelete(BaseModel):
    message: str
    book: Book