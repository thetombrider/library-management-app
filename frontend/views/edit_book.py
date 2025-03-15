import streamlit as st
import requests
from utils.api import fetch_book, get_book_cover_url, fetch_users, invalidate_caches
from utils.state import set_state
from components.ui import render_book_cover

# Configurazione
API_URL = "http://localhost:8000"

def show_edit_book_page():
    """Pagina per modificare un libro esistente"""
    book_id = st.session_state.selected_book
    book = fetch_book(book_id)
    
    if not book:
        st.error("Libro non trovato")
        return
    
    st.title(f"Modifica libro: {book['title']}")
    
    # Visualizza l'immagine della copertina attuale
    col1, col2 = st.columns([1, 2])
    
    with col1:
        render_book_cover(book, width=150)
        st.caption("Copertina attuale")
    
    with col2:
        with st.form("edit_book_form"):
            # Campi per la modifica
            title = st.text_input("Titolo", value=book['title'])
            author = st.text_input("Autore", value=book['author'])
            
            # Creiamo due colonne per i campi opzionali
            col1, col2 = st.columns(2)
            with col1:
                isbn = st.text_input("ISBN", value=book.get('isbn', ''))
                publish_year = st.number_input(
                    "Anno di pubblicazione", 
                    min_value=0, 
                    max_value=2100, 
                    value=book.get('publish_year', 0) or 0
                )
            
            with col2:
                publisher = st.text_input("Editore", value=book.get('publisher', ''))
                
                # Seleziona proprietario
                users = fetch_users()
                user_options = [("Nessuno", None)] + [(user['name'], user['id']) for user in users]
                user_display_dict = {user_id: user_name for user_name, user_id in user_options}
                
                selected_user = st.selectbox(
                    "Proprietario", 
                    options=[user_id for _, user_id in user_options],
                    format_func=lambda x: user_display_dict.get(x, "Sconosciuto"),
                    index=next((i for i, (_, user_id) in enumerate(user_options) if user_id == book.get('owner_id')), 0)
                )
            
            # Descrizione su tutta la larghezza
            description = st.text_area("Descrizione", value=book.get('description', ''), height=150)
            
            # Nota sulle copertine
            st.info("Per aggiornare la copertina, modifica l'ISBN e salva. Il sistema tenterà di scaricare la nuova copertina.")
            
            # Bottoni per le azioni
            col1, col2 = st.columns(2)
            with col1:
                cancel = st.form_submit_button("Annulla")
            with col2:
                submit = st.form_submit_button("Salva modifiche")
            
            if cancel:
                set_state('detail')
                st.rerun()
            
            if submit:
                if not title or not author:
                    st.error("Titolo e autore sono campi obbligatori.")
                else:
                    # Prepara i dati per l'aggiornamento
                    update_data = {
                        "title": title,
                        "author": author,
                        "description": description,
                        "isbn": isbn if isbn else None,
                        "publisher": publisher if publisher else None,
                        "publish_year": publish_year if publish_year > 0 else None,
                        "owner_id": selected_user
                    }
                    
                    try:
                        with st.spinner("Aggiornamento in corso..."):
                            # Pulisci la cache prima dell'aggiornamento
                            invalidate_caches()
                            
                            response = requests.put(f"{API_URL}/books/{book_id}", json=update_data)
                            
                            if response.status_code == 200:
                                st.success("Libro aggiornato con successo!")
                                
                                # Aggiorna la cache di nuovo
                                invalidate_caches()
                                
                                # Ritorna alla pagina di dettaglio
                                set_state('detail')
                                st.rerun()
                            else:
                                error_detail = response.json().get("detail", "Errore sconosciuto")
                                st.error(f"Errore nell'aggiornamento: {error_detail}")
                    except Exception as e:
                        st.error(f"Errore di connessione: {str(e)}")