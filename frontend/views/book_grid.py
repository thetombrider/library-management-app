import streamlit as st
import math
from utils.api import fetch_books, get_book_cover_url, get_user_name, get_current_user_id, search_books
from utils.state import set_state
from components.book_card import render_book_card

# Numero di libri per riga
BOOKS_PER_ROW = 4

def get_unique_authors():
    """Ottiene la lista di autori unici dai libri"""
    books = fetch_books()
    # Estrai autori unici e ordina alfabeticamente
    authors = sorted(list(set(book.get('author', '') for book in books if book.get('author'))))
    return authors

def get_unique_publishers():
    """Ottiene la lista di editori unici dai libri"""
    books = fetch_books()
    # Estrai editori unici e ordina alfabeticamente
    publishers = sorted(list(set(book.get('publisher', '') for book in books if book.get('publisher'))))
    return publishers

def get_unique_years():
    """Ottiene la lista di anni unici dai libri"""
    books = fetch_books()
    # Estrai anni unici e ordina numericamente
    years = sorted(list(set(str(book.get('publish_year', '')) for book in books if book.get('publish_year'))), 
                  key=lambda x: int(x) if x.isdigit() else 0)
    return years

def show_book_grid():
    """Mostra la griglia dei libri"""
    
    # Mostra i risultati dell'aggiornamento dei metadati se presenti
    if 'metadata_update_result' in st.session_state:
        with st.expander("Dettagli aggiornamento metadati", expanded=True):
            result = st.session_state.metadata_update_result
            
            st.markdown(f"### Risultato aggiornamento metadati")
            st.markdown(f"- **Totale libri elaborati:** {result['total']}")
            st.markdown(f"- **Libri aggiornati:** {result['updated']}")
            st.markdown(f"- **Libri non aggiornati:** {result['failed']}")
            
            if result['updated'] > 0:
                st.markdown("#### Libri aggiornati")
                for book in result['updated_books']:
                    st.markdown(f"- **{book['title']}** (ID: {book['id']}, ISBN: {book['isbn']})")
                    st.markdown(f"  - Campi aggiornati: {', '.join(book['updated_fields'])}")
            
            if result['failed'] > 0:
                st.markdown("#### Libri non aggiornati")
                for book in result['failed_books']:
                    st.markdown(f"- **{book['title']}** (ID: {book['id']}, ISBN: {book['isbn']})")
                    st.markdown(f"  - Motivo: {book['reason']}")
            
            if st.button("Chiudi", key="close_metadata_details"):
                del st.session_state.metadata_update_result
                st.rerun()
    
    st.subheader("La mia libreria")
    
    # NUOVA ORGANIZZAZIONE DEI FILTRI
    # 1. Barra di ricerca in alto a tutta larghezza
    previous_query = st.session_state.get("search_query", "")
    search_query = st.text_input("🔍 Cerca per titolo, autore, ISBN...", value=previous_query)
    if search_query != previous_query:
        st.session_state.search_query = search_query
    
    # 2. Filtri su due righe con layout migliore
    with st.container():
        # Prima riga di filtri
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Filtro per stato (esistente)
            filter_options = {
                "all": "Tutti i libri",
                "available": "Disponibili",
                "loaned": "In prestito"
            }
            previous_filter = st.session_state.get("filter_by", "all")
            filter_by = st.selectbox("Stato:", options=list(filter_options.keys()), 
                                    format_func=lambda x: filter_options[x],
                                    index=list(filter_options.keys()).index(previous_filter),
                                    key="filter_status")
            if filter_by != previous_filter:
                st.session_state.filter_by = filter_by
        
        with col2:
            # Filtro per autore (nuovo)
            all_authors = ["Tutti"] + get_unique_authors()
            previous_author = st.session_state.get("filter_author", "Tutti")
            author_filter = st.selectbox("Autore:", 
                                        options=all_authors,
                                        index=all_authors.index(previous_author) if previous_author in all_authors else 0,
                                        key="filter_author")
            if author_filter != previous_author:
                st.session_state.filter_author = author_filter
        
        with col3:
            # Filtro per editore (nuovo)
            all_publishers = ["Tutti"] + get_unique_publishers()
            previous_publisher = st.session_state.get("filter_publisher", "Tutti")
            publisher_filter = st.selectbox("Editore:", 
                                           options=all_publishers,
                                           index=all_publishers.index(previous_publisher) if previous_publisher in all_publishers else 0,
                                           key="filter_publisher")
            if publisher_filter != previous_publisher:
                st.session_state.filter_publisher = publisher_filter
        
        # Seconda riga di filtri
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            # Filtro per anno (nuovo)
            all_years = ["Tutti"] + get_unique_years()
            previous_year = st.session_state.get("filter_year", "Tutti")
            year_filter = st.selectbox("Anno:", 
                                      options=all_years,
                                      index=all_years.index(previous_year) if previous_year in all_years else 0,
                                      key="filter_year")
            if year_filter != previous_year:
                st.session_state.filter_year = year_filter
        
        with col3:
            # Bottone per azzerare tutti i filtri
            if st.button("🔄 Azzera filtri", use_container_width=True):
                st.session_state.search_query = ""
                st.session_state.filter_by = "all"
                st.session_state.filter_author = "Tutti"
                st.session_state.filter_publisher = "Tutti"
                st.session_state.filter_year = "Tutti"
                st.rerun()
    
    # Recupera i libri in base ai filtri
    query = st.session_state.get("search_query", "")
    filter_by = st.session_state.get("filter_by", "all")
    filter_author = st.session_state.get("filter_author", "Tutti")
    filter_publisher = st.session_state.get("filter_publisher", "Tutti")
    filter_year = st.session_state.get("filter_year", "Tutti")
    
    # Debug info
    print(f"Ricerca libri con query='{query}', filter_by='{filter_by}', autore='{filter_author}', editore='{filter_publisher}', anno='{filter_year}'")
    
    # Usa la funzione search_books con i parametri aggiuntivi
    books = search_books(
        query=query, 
        filter_by=filter_by,
        filter_author=filter_author if filter_author != "Tutti" else "",
        filter_publisher=filter_publisher if filter_publisher != "Tutti" else "",
        filter_year=filter_year if filter_year != "Tutti" else ""
    )
    
    # Debug info
    print(f"Trovati {len(books)} libri")
    
    if not books:
        if query or filter_by != "all":
            st.info("Nessun libro trovato con i criteri di ricerca specificati.")
        else:
            st.info("Non hai ancora libri nella tua libreria. Aggiungi un nuovo libro usando il pulsante 'Aggiungi Libro'.")
            
            # Debug aggiuntivo
            from utils.api import invalidate_caches
            st.button("🔄 Ricarica dati", on_click=invalidate_caches)
        return
    
    # Resto del codice esistente per mostrare i libri...
    current_user_id = get_current_user_id()
    
    # Separa i libri di proprietà da quelli presi in prestito
    owned_books = [book for book in books if book.get('owner_id') == current_user_id]
    borrowed_books = [book for book in books if book.get('owner_id') != current_user_id]
    
    # Mostra i conteggi dei risultati
    st.markdown(f"**{len(books)} libri trovati** ({len(owned_books)} di tua proprietà, {len(borrowed_books)} presi in prestito)")
    
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