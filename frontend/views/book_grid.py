import streamlit as st
import math
from utils.api import fetch_books, get_book_cover_url, get_user_name, get_current_user_id
from utils.state import set_state
from components.book_card import render_book_card

# Numero di libri per riga
BOOKS_PER_ROW = 4

def show_book_grid():
    """Mostra la griglia dei libri dell'utente"""
    st.subheader("La mia libreria")
    
    current_user_id = get_current_user_id()
    books = fetch_books()
    
    if not books:
        st.info("Non hai ancora libri nella tua libreria. Aggiungi un nuovo libro usando il pulsante 'Aggiungi Libro'.")
        return
    
    # Separa i libri di proprietà da quelli presi in prestito
    owned_books = [book for book in books if book.get('owner_id') == current_user_id]
    borrowed_books = [book for book in books if book.get('owner_id') != current_user_id]
    
    # Mostra prima i libri di proprietà
    if owned_books:
        st.markdown("### I miei libri")
        # Calcola il numero di righe necessarie
        num_rows = math.ceil(len(owned_books) / BOOKS_PER_ROW)
        
        for row_idx in range(num_rows):
            # Crea una riga di colonne
            cols = st.columns(BOOKS_PER_ROW)
            
            for col_idx in range(BOOKS_PER_ROW):
                book_idx = row_idx * BOOKS_PER_ROW + col_idx
                
                # Controlla se abbiamo ancora libri da mostrare
                if book_idx < len(owned_books):
                    book = owned_books[book_idx]
                    
                    # Verifica che il libro sia valido
                    if book is None:
                        continue
                    
                    with cols[col_idx]:
                        render_book_card(book, show_button=True)
    
    # Mostra i libri presi in prestito
    if borrowed_books:
        st.markdown("### Libri presi in prestito")
        # Calcola il numero di righe necessarie
        num_rows = math.ceil(len(borrowed_books) / BOOKS_PER_ROW)
        
        for row_idx in range(num_rows):
            # Crea una riga di colonne
            cols = st.columns(BOOKS_PER_ROW)
            
            for col_idx in range(BOOKS_PER_ROW):
                book_idx = row_idx * BOOKS_PER_ROW + col_idx
                
                # Controlla se abbiamo ancora libri da mostrare
                if book_idx < len(borrowed_books):
                    book = borrowed_books[book_idx]
                    
                    # Verifica che il libro sia valido
                    if book is None:
                        continue
                    
                    with cols[col_idx]:
                        # Aggiungi un indicatore che questo libro è preso in prestito
                        book_owner = get_user_name(book.get('owner_id'))
                        render_book_card(
                            book, 
                            show_button=True, 
                            additional_info=f"Da: {book_owner}"
                        )
    
    # Se non ci sono né libri di proprietà né libri in prestito
    if not owned_books and not borrowed_books:
        st.info("Non hai ancora libri nella tua libreria. Aggiungi un nuovo libro usando il pulsante 'Aggiungi Libro'.")