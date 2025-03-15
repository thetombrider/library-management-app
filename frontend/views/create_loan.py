import streamlit as st
import requests
from utils.api import fetch_book, get_book_cover_url, fetch_users, invalidate_caches
from utils.state import set_state
from components.ui import render_book_cover, show_message_box

# Configurazione
API_URL = "http://localhost:8000"

def show_create_loan_page():
    """Pagina per creare un nuovo prestito"""
    book_id = st.session_state.selected_book_for_loan
    book = fetch_book(book_id)
    
    if not book:
        show_message_box("Libro non trovato", "error")
        if st.button("Torna alla home"):
            set_state('grid')
            st.rerun()
        return
    
    st.title(f"Presta il libro: {book['title']}")
    
    # Visualizza le informazioni del libro
    col1, col2 = st.columns([1, 2])
    with col1:
        render_book_cover(book, width=150)
    
    with col2:
        st.markdown(f"**Titolo:** {book['title']}")
        st.markdown(f"**Autore:** {book['author']}")
        if book.get('publisher'):
            st.markdown(f"**Editore:** {book['publisher']}")
        if book.get('isbn'):
            st.markdown(f"**ISBN:** {book['isbn']}")
    
    st.markdown("---")
    
    # Ottieni tutti gli utenti
    all_users = fetch_users()
    
    # Escludi il proprietario dalla lista (se esiste)
    owner_id = book.get('owner_id')
    eligible_users = [user for user in all_users if user['id'] != owner_id]
    
    if not eligible_users:
        show_message_box("Non ci sono utenti disponibili a cui prestare il libro", "warning")
        if st.button("← Torna al libro"):
            set_state('detail')
            st.rerun()
        return
    
    st.subheader("Seleziona il destinatario")
    
    # Crea un selettore utenti con nome e email
    user_options = [f"{user['name']} ({user['email']})" for user in eligible_users]
    user_dict = {f"{user['name']} ({user['email']})": user['id'] for user in eligible_users}
    
    selected_user_display = st.selectbox("Destinatario:", options=user_options)
    selected_user_id = user_dict[selected_user_display] if selected_user_display else None
    
    # Bottoni per azioni
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Annulla"):
            set_state('detail')
            st.rerun()
            
    with col2:
        if st.button("✓ Conferma prestito"):
            if selected_user_id:
                with st.spinner("Registrazione del prestito..."):
                    try:
                        # Crea oggetto prestito
                        loan_data = {
                            "book_id": book_id,
                            "user_id": selected_user_id,
                            # Le date verranno gestite dal backend con valori predefiniti
                        }
                        
                        # Pulisci cache prima della richiesta
                        invalidate_caches()
                        
                        # Invia richiesta al backend
                        response = requests.post(f"{API_URL}/loans/", json=loan_data, timeout=30)
                        
                        if response.status_code == 200:
                            # Pulisci di nuovo la cache
                            invalidate_caches()
                            
                            st.success(f"Libro prestato con successo a {selected_user_display.split('(')[0].strip()}")
                            
                            # Bottone per tornare alla pagina di dettaglio
                            if st.button("Torna al libro"):
                                set_state('detail', selected_book=book_id)
                                st.rerun()
                        else:
                            error_detail = response.json().get("detail", "Errore sconosciuto")
                            st.error(f"Errore nel prestito: {error_detail}")
                    except Exception as e:
                        st.error(f"Errore di connessione: {str(e)}")
            else:
                st.error("Seleziona un destinatario per il prestito")