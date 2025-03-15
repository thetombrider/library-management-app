import streamlit as st
import requests
import time
from utils.api import get_book_cover_url, invalidate_caches
from utils.state import set_state
from utils.api import get_auth_header, get_user_name, get_current_user_id

# Configurazione
API_URL = "http://localhost:8000"

def show_add_book_page():
    """Pagina per aggiungere un nuovo libro tramite ISBN"""
    st.title("Aggiungi un Nuovo Libro")
    
    # Crea tab per le diverse modalità di aggiunta
    tab1, tab2 = st.tabs(["Singolo ISBN", "Importazione multipla"])
    
    # Tab 1: Aggiunta singolo libro
    with tab1:
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
    
    # Tab 2: Importazione multipla
    with tab2:
        st.subheader("Importa più libri contemporaneamente inserendo una lista di ISBN")
        
        # Form per inserire la lista di ISBN
        with st.form("bulk_import_form"):
            isbn_list = st.text_area(
                "Lista ISBN (uno per riga):",
                placeholder="9788804507451\n9788807881558\n9788804668237",
                help="Inserisci un ISBN per riga. Gli spazi e i caratteri speciali verranno rimossi automaticamente."
            )
            
            # Opzione per mostrare i dettagli di importazione
            show_details = st.checkbox("Mostra dettagli di importazione", value=True)
            
            submit_bulk = st.form_submit_button("Importa Libri")
        
        # Gestione dell'invio del form di importazione multipla
        if submit_bulk:
            if not isbn_list.strip():
                st.error("Inserisci almeno un ISBN.")
            else:
                # Pulisci e prepara la lista di ISBN
                isbn_items = []
                for line in isbn_list.strip().split("\n"):
                    # Rimuovi spazi e caratteri speciali, mantieni solo numeri e X (per ISBN-10)
                    clean_isbn = ''.join(c for c in line if c.isdigit() or c.upper() == 'X')
                    if clean_isbn:
                        isbn_items.append(clean_isbn)
                
                if not isbn_items:
                    st.error("Nessun ISBN valido trovato.")
                    return
                
                # Mostra il contatore di importazione
                progress_text = "Importazione in corso..."
                progress_bar = st.progress(0, text=progress_text)
                
                # Contatori per il report finale
                total_books = len(isbn_items)
                successful_imports = 0
                failed_imports = 0
                skipped_imports = 0
                imported_books = []
                failed_isbns = []
                
                # Crea un container espandibile per i dettagli se richiesto
                if show_details:
                    details_container = st.expander("Dettagli importazione", expanded=True)
                
                # Ottieni gli headers di autenticazione
                headers = get_auth_header()
                
                # Importa ciascun ISBN
                for i, isbn in enumerate(isbn_items):
                    # Aggiorna la progress bar
                    progress_percent = (i + 1) / total_books
                    progress_bar.progress(progress_percent, text=f"{progress_text} {i+1}/{total_books}")
                    
                    # Mostra quale ISBN stiamo elaborando
                    if show_details:
                        with details_container:
                            st.write(f"Elaborazione ISBN: {isbn}")
                    
                    try:
                        # Richiesta al backend
                        response = requests.post(
                            f"{API_URL}/books/", 
                            json={"isbn": isbn},
                            headers=headers
                        )
                        
                        if response.status_code == 200:
                            book = response.json()
                            successful_imports += 1
                            imported_books.append({
                                "id": book.get('id'),
                                "title": book.get('title', 'N/A'),
                                "author": book.get('author', 'N/A')
                            })
                            
                            if show_details:
                                with details_container:
                                    st.success(f"✓ Aggiunto: {book.get('title', 'N/A')} di {book.get('author', 'N/A')}")
                        elif response.status_code == 400 and "già un libro con lo stesso ISBN" in response.json().get('detail', ''):
                            skipped_imports += 1
                            if show_details:
                                with details_container:
                                    st.warning(f"⚠️ Saltato: ISBN {isbn} già presente nella tua libreria")
                        else:
                            failed_imports += 1
                            failed_isbns.append(isbn)
                            if show_details:
                                with details_container:
                                    st.error(f"❌ Fallito: ISBN {isbn} - {response.json().get('detail', 'Errore sconosciuto')}")
                        
                        # Breve pausa per evitare troppe richieste al backend
                        time.sleep(0.5)
                        
                    except Exception as e:
                        failed_imports += 1
                        failed_isbns.append(isbn)
                        if show_details:
                            with details_container:
                                st.error(f"❌ Errore: ISBN {isbn} - {str(e)}")
                
                # Completa la progress bar
                progress_bar.progress(1.0, text="Importazione completata!")
                
                # Mostra il riepilogo dell'importazione
                st.markdown("### Riepilogo importazione")
                st.write(f"📚 Totale ISBN elaborati: **{total_books}**")
                st.write(f"✅ Libri importati con successo: **{successful_imports}**")
                st.write(f"⚠️ ISBN saltati (già presenti): **{skipped_imports}**")
                st.write(f"❌ Importazioni fallite: **{failed_imports}**")
                
                # Se ci sono libri importati, mostra l'elenco
                if imported_books:
                    st.markdown("#### Libri importati:")
                    for book in imported_books:
                        st.markdown(f"- **{book['title']}** di {book['author']}")
                
                # Se ci sono ISBN falliti, mostra l'elenco
                if failed_isbns:
                    st.markdown("#### ISBN falliti:")
                    for isbn in failed_isbns:
                        st.markdown(f"- `{isbn}`")
                
                # Bottoni per le azioni successive
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Torna alla libreria"):
                        # Invalida le cache e torna alla griglia
                        invalidate_caches()
                        set_state('grid')
                        st.rerun()
                
                with col2:
                    if st.button("Importa altri libri"):
                        # Aggiorna solo la cache
                        invalidate_caches()
                        st.rerun()
    
    # Pulisci l'ISBN scansionato dopo averlo usato
    if 'scanned_isbn' in st.session_state:
        st.session_state.scanned_isbn = None