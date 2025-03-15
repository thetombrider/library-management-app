import streamlit as st
import requests
from utils.api import get_book_cover_url, invalidate_caches
from utils.state import set_state
from utils.api import get_auth_header, get_user_name, get_current_user_id

# Configurazione
API_URL = "http://localhost:8000"

def show_add_book_page():
    """Pagina per aggiungere un nuovo libro tramite ISBN"""
    st.title("Aggiungi un Nuovo Libro")
    st.subheader("Inserisci l'ISBN e lascia che il sistema recuperi automaticamente i dettagli")
    
    # Se c'è un ISBN scansionato, pre-riempire il form
    initial_isbn = st.session_state.scanned_isbn if 'scanned_isbn' in st.session_state else ""
    
    # Controlla se siamo in fase di conferma dopo aggiunta
    if 'temp_added_book' in st.session_state:
        book_id = st.session_state.temp_added_book
        st.success("Libro aggiunto con successo!")
        st.info("Cosa vuoi fare ora?")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Visualizza Libro", key="view_added_book"):
                del st.session_state.temp_added_book  # Pulisci lo stato
                set_state('detail', selected_book=book_id)
                st.rerun()
        
        with col2:
            if st.button("Aggiungi un altro libro", key="add_another"):
                del st.session_state.temp_added_book  # Pulisci lo stato
                st.rerun()  # Semplicemente ricarica la pagina
                
        # Aggiungi un terzo pulsante per tornare alla home
        if st.button("Torna alla home", key="home_from_added"):
            del st.session_state.temp_added_book  # Pulisci lo stato
            set_state('grid')
            st.rerun()
            
        return  # Esci dalla funzione evitando di mostrare il form
    
    # Fase 1: Form per inserire l'ISBN
    with st.form("isbn_entry"):
        isbn = st.text_input("ISBN del libro:", value=initial_isbn, placeholder="Es. 9788804507451")
        submit = st.form_submit_button("Aggiungi Libro")
    
    # Fase 2: Gestione dell'invio del form (fuori dal form)
    if submit:
        if not isbn:
            st.error("È necessario inserire un ISBN.")
        else:
            with st.spinner("Recupero informazioni dal database Google Books..."):
                try:
                    # Pulizia cache prima della richiesta
                    invalidate_caches()
                    
                    # MODIFICA: Ottieni gli headers di autenticazione
                    headers = get_auth_header()
                    
                    # Richiedi aggiunta libro
                    response = requests.post(
                        f"{API_URL}/books/", 
                        json={"isbn": isbn},
                        headers=headers  # Aggiungi gli headers di autenticazione
                    )
                    
                    if response.status_code == 200:
                        book = response.json()
                        
                        # Mostra dettagli del libro aggiunto
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            if book.get('has_cover', False):
                                st.image(get_book_cover_url(book['id']), width=150)
                            else:
                                st.markdown(
                                    """
                                    <div style="width: 150px; height: 200px; 
                                            background-color: #f0f0f0; 
                                            border-radius: 5px;
                                            display: flex; 
                                            align-items: center; 
                                            justify-content: center;">
                                        <span style="color: #999;">No Cover</span>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                        
                        with col2:
                            st.write(f"**Titolo:** {book.get('title', 'N/A')}")
                            st.write(f"**Autore:** {book.get('author', 'N/A')}")
                            st.write(f"**Editore:** {book.get('publisher', 'N/A')}")
                            st.write(f"**Anno:** {book.get('publish_year', 'N/A')}")
                            
                            # AGGIUNTA: Mostra anche il proprietario
                            owner_name = "Tu" if book.get('owner_id') == get_current_user_id() else get_user_name(book.get('owner_id'))
                            st.write(f"**Proprietario:** {owner_name}")
                        
                        # Salva l'ID del libro e ricarica la pagina per evitare problemi con i bottoni
                        st.session_state.temp_added_book = book['id']
                        st.rerun()  # Ricarica la pagina che mostrerà l'interfaccia di conferma
                    else:
                        st.error(f"Errore: {response.json().get('detail', 'Errore sconosciuto')}")
                except Exception as e:
                    st.error(f"Errore di connessione: {str(e)}")
    
    # Pulisci l'ISBN scansionato dopo averlo usato
    if 'scanned_isbn' in st.session_state:
        st.session_state.scanned_isbn = None