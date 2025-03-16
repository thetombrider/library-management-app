import streamlit as st
import math
from utils.api import fetch_books, get_book_cover_url, get_user_name, get_current_user_id, search_books
from utils.state import set_state
from components.book_card import render_book_card

# Numero di libri per riga
BOOKS_PER_ROW = 4

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
    
    # Aggiungi barra di ricerca e filtri
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        # Carica il valore precedente della query se presente
        previous_query = st.session_state.get("search_query", "")
        search_query = st.text_input("🔍 Cerca per titolo, autore, ISBN...", value=previous_query)
        if search_query != previous_query:
            st.session_state.search_query = search_query
            # Resetta il filtro quando cambia la query
            st.session_state.filter_by = "all"
    
    with col2:
        filter_options = {
            "all": "Tutti i libri",
            "available": "Disponibili",
            "loaned": "In prestito"
        }
        # Carica il valore precedente del filtro se presente
        previous_filter = st.session_state.get("filter_by", "all")
        filter_by = st.selectbox("Filtro:", options=list(filter_options.keys()), 
                                format_func=lambda x: filter_options[x],
                                index=list(filter_options.keys()).index(previous_filter))
        if filter_by != previous_filter:
            st.session_state.filter_by = filter_by
    
    with col3:
        # Bottone per pulire i filtri
        if st.button("🔄 Azzera filtri", use_container_width=True):
            st.session_state.search_query = ""
            st.session_state.filter_by = "all"
            st.rerun()
    
    # Recupera i libri in base ai filtri
    query = st.session_state.get("search_query", "")
    filter_by = st.session_state.get("filter_by", "all")
    
    # Debug info
    print(f"Ricerca libri con query='{query}', filter_by='{filter_by}'")
    
    # Usa la funzione search_books
    books = search_books(query=query, filter_by=filter_by)
    
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