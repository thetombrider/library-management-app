import streamlit as st
import math
from utils.api import fetch_books, get_book_cover_url
from utils.state import set_state
from components.book_card import render_book_card

# Numero di libri per riga
BOOKS_PER_ROW = 4

def show_book_grid():
    """Mostra la griglia dei libri"""
    books = fetch_books()
    
    if not books:
        st.info("Nessun libro disponibile nella biblioteca.")
        return
    
    # Calcola il numero di righe necessarie
    num_rows = math.ceil(len(books) / BOOKS_PER_ROW)
    
    for row_idx in range(num_rows):
        # Crea una riga di colonne
        cols = st.columns(BOOKS_PER_ROW)
        
        for col_idx in range(BOOKS_PER_ROW):
            book_idx = row_idx * BOOKS_PER_ROW + col_idx
            
            # Controlla se abbiamo ancora libri da mostrare
            if book_idx < len(books):
                book = books[book_idx]
                
                # Verifica che il libro sia valido
                if book is None:
                    continue
                
                with cols[col_idx]:
                    render_book_card(book, show_button=True)