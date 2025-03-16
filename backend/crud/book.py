from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.models.book import Book
from backend.models.loan import Loan
from backend.schemas.book import BookCreate, BookUpdate, BookDelete
from fastapi import HTTPException, status
from backend.services.google_books import fetch_book_metadata
from datetime import datetime
from sqlalchemy import or_, and_  # Aggiungi questa riga per importare gli operatori necessari

def get_books(db: Session, skip: int = 0, limit: int = 10):
    books = db.query(Book).offset(skip).limit(limit).all()
    # Aggiungiamo un flag per indicare se il libro ha una copertina
    for book in books:
        setattr(book, "has_cover", book.cover_image is not None)
    return books

def get_book(db: Session, book_id: int):
    """
    Ottiene un libro specifico dal database tramite ID.
    
    Args:
        db: Session del database
        book_id: ID del libro da recuperare
        
    Returns:
        Il libro richiesto o None se non trovato
    """
    book = db.query(Book).filter(Book.id == book_id).first()
    if book:
        setattr(book, "has_cover", book.cover_image is not None)
    return book

def create_book(db: Session, book: BookCreate):
    # Check per duplicati solo tra i libri dello stesso proprietario
    owner_id = book.owner_id
    
    # Costruisci una query che cerchi libri con lo stesso owner_id
    duplicate_query = db.query(Book).filter(Book.owner_id == owner_id)
    
    # Aggiungi il filtro ISBN o titolo
    if book.isbn:
        duplicate_book = duplicate_query.filter(Book.isbn == book.isbn).first()
    else:
        duplicate_book = duplicate_query.filter(Book.title == book.title).first()
    
    if duplicate_book:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Hai già un libro con lo stesso ISBN o titolo nella tua libreria"
        )
    
    # If ISBN is provided, try to fetch metadata from multiple APIs with fallback
    if book.isbn:
        metadata = fetch_book_metadata(book.isbn)
        if metadata:
            # Update book data with metadata
            book_data = book.model_dump()
            book_data.update(metadata)
            
            # Verifica che l'immagine sia stata recuperata correttamente
            has_cover = metadata.get('cover_image') is not None
            print(f"Cover image retrieved: {has_cover}")
            if has_cover:
                print(f"Cover image size: {len(metadata['cover_image'])} bytes")
            
            # Verifica che i campi essenziali non siano vuoti
            if not book_data.get('title'):
                book_data['title'] = "Titolo non disponibile"
            if not book_data.get('author'):
                book_data['author'] = "Autore sconosciuto"
                
            db_book = Book(**book_data)
            
            # Verifica dopo la creazione dell'oggetto
            print(f"Book object has cover: {db_book.cover_image is not None}")
        else:
            # If no metadata found from any API, use the provided data
            # Aggiungi titolo e autore predefiniti se non disponibili
            book_data = book.model_dump()
            if not book_data.get('title'):
                book_data['title'] = "Titolo mancante"
            if not book_data.get('author'):
                book_data['author'] = "Autore sconosciuto"
                
            db_book = Book(**book_data)
    else:
        # No ISBN provided, use the provided data
        db_book = Book(**book.model_dump())
    
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    
    # Imposta il flag has_cover dopo il refresh del database
    setattr(db_book, "has_cover", db_book.cover_image is not None)
    
    return db_book

def update_book(db: Session, book_id: int, book: BookUpdate):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    for key, value in book.model_dump().items():
        setattr(db_book, key, value)
    db.commit()
    db.refresh(db_book)
    return db_book

def delete_book(db: Session, book_id: int):
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    
    # Verifica se ci sono prestiti attivi per questo libro
    # Un prestito è attivo se non ha data di restituzione o la data è nel futuro
    now = datetime.now()
    active_loans = db.query(Loan).filter(
        Loan.book_id == book_id,
        (Loan.return_date == None) | (Loan.return_date > now)
    ).count()
    
    if active_loans > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete book with active loans")
    
    # Prima elimina tutti i prestiti (restituiti) associati a questo libro
    db.query(Loan).filter(Loan.book_id == book_id).delete()
    
    # Poi elimina il libro
    db.delete(db_book)
    
    try:
        db.commit()
        return {"message": "Book deleted successfully", "book": db_book}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

def refresh_missing_book_metadata(db: Session, owner_id: int = None):
    """
    Cerca libri con informazioni mancanti o di proprietà dell'utente specificato
    e tenta di recuperarle nuovamente dalle API esterne.
    
    Args:
        db: Sessione del database
        owner_id: Se specificato, aggiorna tutti i libri di proprietà dell'utente specificato
    """
    # Costruisci la query di base
    query = db.query(Book)
    
    if owner_id:
        # Se è specificato un owner_id, aggiorna tutti i libri di quell'utente
        query = query.filter(Book.owner_id == owner_id)
    else:
        # Altrimenti, cerca solo i libri con informazioni mancanti
        query = query.filter(
            (Book.title == "Titolo mancante") | 
            (Book.author == "Autore sconosciuto")
        )
    
    # Esegui la query
    books_to_update = query.all()
    
    if not books_to_update:
        return {
            "status": "success", 
            "message": "Nessun libro da aggiornare trovato", 
            "updated": 0, 
            "failed": 0,
            "total": 0
        }
    
    # Contatori per il report
    total_books = len(books_to_update)
    updated_books = 0
    failed_books = 0
    updated_book_details = []
    failed_book_details = []
    
    # Prova a recuperare informazioni per ogni libro
    for book in books_to_update:
        if not book.isbn:
            # Se non c'è ISBN, non possiamo recuperare nulla
            failed_books += 1
            failed_book_details.append({
                "id": book.id,
                "isbn": None,
                "title": book.title,
                "reason": "ISBN mancante"
            })
            continue
        
        # Tenta di recuperare i metadati usando le API
        metadata = fetch_book_metadata(book.isbn)
        
        if metadata and (metadata.get('title') or metadata.get('author')):
            # Aggiorna i campi disponibili
            updated_fields = []
            
            # Aggiorna i campi principali solo se mancanti o generici
            if (book.title == "Titolo mancante" or owner_id) and metadata.get('title'):
                book.title = metadata.get('title')
                updated_fields.append("title")
                
            if (book.author == "Autore sconosciuto" or owner_id) and metadata.get('author'):
                book.author = metadata.get('author')
                updated_fields.append("author")
                
            # Aggiorna altri campi utili se disponibili
            if (not book.description or owner_id) and metadata.get('description'):
                book.description = metadata.get('description')
                updated_fields.append("description")
                
            if (not book.publisher or owner_id) and metadata.get('publisher'):
                book.publisher = metadata.get('publisher')
                updated_fields.append("publisher")
                
            if (not book.publish_year or owner_id) and metadata.get('publish_year'):
                book.publish_year = metadata.get('publish_year')
                updated_fields.append("publish_year")
                
            # Aggiorna la copertina solo se era mancante
            if not book.cover_image and metadata.get('cover_image'):
                book.cover_image = metadata.get('cover_image')
                updated_fields.append("cover_image")
            
            # Se abbiamo effettuato aggiornamenti
            if updated_fields:
                updated_books += 1
                updated_book_details.append({
                    "id": book.id,
                    "isbn": book.isbn,
                    "title": book.title,
                    "updated_fields": updated_fields
                })
            else:
                failed_books += 1
                failed_book_details.append({
                    "id": book.id,
                    "isbn": book.isbn,
                    "title": book.title,
                    "reason": "Nessun nuovo dato disponibile"
                })
        else:
            # I metadati non sono stati trovati
            failed_books += 1
            failed_book_details.append({
                "id": book.id,
                "isbn": book.isbn,
                "title": book.title,
                "reason": "Metadati non trovati"
            })
    
    # Esegui il commit delle modifiche
    try:
        db.commit()
        
        # Prepara il report finale
        return {
            "status": "success",
            "message": f"Elaborazione completata: {updated_books} libri aggiornati, {failed_books} non aggiornati",
            "total": total_books,
            "updated": updated_books,
            "failed": failed_books,
            "updated_books": updated_book_details,
            "failed_books": failed_book_details
        }
    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "message": f"Errore durante l'aggiornamento: {str(e)}",
            "updated": 0,
            "failed": total_books
        }

def search_books(db: Session, user_id: int, query: str = "", filter_by: str = "all", 
                filter_author: str = "", filter_publisher: str = "", filter_year: str = ""):
    """
    Cerca libri in base a criteri specifici.
    
    Args:
        db: Session del database
        user_id: ID dell'utente corrente
        query: Testo da cercare in titolo, autore, ISBN, etc.
        filter_by: Filtro per stato (all, available, loaned)
        filter_author: Filtro per autore specifico
        filter_publisher: Filtro per editore specifico
        filter_year: Filtro per anno di pubblicazione
    """
    # Base query per libri dell'utente (di proprietà o in prestito)
    # Unisci i libri di proprietà dell'utente con quelli che ha preso in prestito
    owned_books = db.query(Book).filter(Book.owner_id == user_id)
    
    borrowed_books = db.query(Book).join(
        Loan, Book.id == Loan.book_id
    ).filter(
        Loan.user_id == user_id,
        Book.owner_id != user_id,
        or_(
            Loan.return_date == None,
            Loan.return_date > datetime.now()
        )
    )
    
    # Combina le due query
    base_query = owned_books.union(borrowed_books)
    
    # Applica filtro di stato
    if filter_by == "available":
        # Libri disponibili (di proprietà e non prestati)
        available_books_ids = db.query(Book.id).outerjoin(
            Loan, and_(
                Book.id == Loan.book_id,
                or_(
                    Loan.return_date == None,
                    Loan.return_date > datetime.now()
                )
            )
        ).filter(
            Book.owner_id == user_id,
            Loan.id == None  # Nessun prestito attivo
        ).subquery()
        
        base_query = db.query(Book).filter(Book.id.in_(available_books_ids))
    
    elif filter_by == "loaned":
        # Libri attualmente in prestito (dell'utente)
        loaned_books_ids = db.query(Book.id).join(
            Loan, Book.id == Loan.book_id
        ).filter(
            Book.owner_id == user_id,
            or_(
                Loan.return_date == None,
                Loan.return_date > datetime.now()
            )
        ).subquery()
        
        base_query = db.query(Book).filter(Book.id.in_(loaned_books_ids))
    
    # Dopo i filtri di stato, applica i filtri aggiuntivi
    if filter_author:
        base_query = base_query.filter(Book.author == filter_author)
    
    if filter_publisher:
        base_query = base_query.filter(Book.publisher == filter_publisher)
    
    if filter_year:
        base_query = base_query.filter(Book.publish_year == int(filter_year))
    
    # Applica la ricerca testuale se specificata
    if query:
        search_term = f"%{query}%"
        base_query = base_query.filter(
            or_(
                Book.title.ilike(search_term),
                Book.author.ilike(search_term),
                Book.isbn.ilike(search_term),
                Book.publisher.ilike(search_term),
                Book.description.ilike(search_term)
            )
        )
    
    # Esegui la query e ritorna i risultati
    return base_query.all()

def bulk_update_books(db: Session, book_ids: List[int], updates: Dict[str, Any], user_id: int):
    """
    Aggiorna in batch i metadati di più libri.
    
    Args:
        db: Session del database
        book_ids: Lista degli ID dei libri da aggiornare
        updates: Dizionario con i campi da aggiornare
        user_id: ID dell'utente che richiede l'aggiornamento
    
    Returns:
        Dict: Risultato dell'operazione
    """
    # Contatori per il report
    total_books = len(book_ids)
    updated_books = 0
    failed_books = 0
    failed_book_ids = []
    
    # Verifica che ci siano campi validi da aggiornare
    valid_fields = ["title", "author", "description", "publisher", "publish_year"]
    update_fields = {k: v for k, v in updates.items() if k in valid_fields}
    
    if not update_fields:
        return {
            "status": "error",
            "message": "Nessun campo valido da aggiornare",
            "updated": 0,
            "failed": total_books
        }
    
    # Recupera i libri da aggiornare
    try:
        # Query per selezionare i libri dell'utente
        books = db.query(Book).filter(
            Book.id.in_(book_ids),
            Book.owner_id == user_id
        ).all()
        
        # Verifica che tutti i libri richiesti siano stati trovati
        if len(books) < total_books:
            return {
                "status": "warning",
                "message": "Alcuni libri non sono stati trovati o non appartengono all'utente",
                "updated": 0,
                "failed": total_books,
                "books_found": len(books)
            }
        
        # Aggiorna ogni libro
        for book in books:
            try:
                # Applica gli aggiornamenti
                for field, value in update_fields.items():
                    setattr(book, field, value)
                
                updated_books += 1
            except Exception as e:
                failed_books += 1
                failed_book_ids.append(book.id)
                print(f"Errore nell'aggiornamento del libro {book.id}: {str(e)}")
        
        # Commit delle modifiche
        db.commit()
        
        return {
            "status": "success",
            "message": f"Aggiornamento completato: {updated_books} libri aggiornati",
            "total": total_books,
            "updated": updated_books,
            "failed": failed_books,
            "failed_book_ids": failed_book_ids
        }
        
    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "message": f"Errore durante l'aggiornamento: {str(e)}",
            "updated": 0,
            "failed": total_books
        }

def bulk_delete_books(db: Session, book_ids: List[int], user_id: int):
    """
    Elimina in batch più libri.
    
    Args:
        db: Session del database
        book_ids: Lista degli ID dei libri da eliminare
        user_id: ID dell'utente che richiede l'eliminazione
    
    Returns:
        Dict: Risultato dell'operazione
    """
    # Contatori per il report
    total_books = len(book_ids)
    deleted_books = 0
    failed_books = 0
    failed_book_ids = []
    not_owned_books = 0
    not_owned_book_ids = []
    loaned_books = 0
    loaned_book_ids = []
    
    try:
        # Per ogni libro, verifica proprietà e prestiti attivi prima di cancellare
        for book_id in book_ids:
            try:
                # Recupera il libro
                book = db.query(Book).filter(Book.id == book_id).first()
                
                # Se il libro non esiste, conteggialo come fallito
                if not book:
                    failed_books += 1
                    failed_book_ids.append(book_id)
                    continue
                
                # Verifica che l'utente sia il proprietario
                if book.owner_id != user_id:
                    not_owned_books += 1
                    not_owned_book_ids.append(book_id)
                    continue
                
                # Verifica che non ci siano prestiti attivi
                active_loans = db.query(Loan).filter(
                    Loan.book_id == book_id,
                    (Loan.return_date.is_(None) | (Loan.return_date > datetime.now()))
                ).count()
                
                if active_loans > 0:
                    loaned_books += 1
                    loaned_book_ids.append(book_id)
                    continue
                
                # Elimina il libro
                db.delete(book)
                deleted_books += 1
                
            except Exception as e:
                failed_books += 1
                failed_book_ids.append(book_id)
                print(f"Errore nell'eliminazione del libro {book_id}: {str(e)}")
        
        # Commit delle modifiche
        db.commit()
        
        return {
            "status": "success",
            "message": f"Eliminazione completata: {deleted_books} libri eliminati",
            "total": total_books,
            "deleted": deleted_books,
            "failed": failed_books,
            "failed_book_ids": failed_book_ids,
            "not_owned": not_owned_books,
            "not_owned_book_ids": not_owned_book_ids,
            "loaned": loaned_books,
            "loaned_book_ids": loaned_book_ids
        }
        
    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "message": f"Errore durante l'eliminazione: {str(e)}",
            "deleted": 0,
            "failed": total_books
        }