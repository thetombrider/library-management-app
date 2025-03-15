import streamlit as st
import datetime
import requests
from utils.api import fetch_book, get_book_cover_url, get_user_name, get_active_loans_for_book, invalidate_caches, get_current_user_id
from utils.state import set_state
from components.ui import render_book_cover

# Configurazione
API_URL = "http://localhost:8000"

def show_book_detail():
    """Mostra i dettagli del libro"""
    book_id = st.session_state.selected_book
    book = fetch_book(book_id)
    
    if not book:
        st.error("Libro non trovato")
        return
    
    # Verifica se il libro appartiene all'utente corrente
    current_user_id = get_current_user_id()
    is_owner = book.get('owner_id') == current_user_id
    
    # Bottoni di azione
    col_back, col_edit, col_delete = st.columns([1, 1, 1])
    
    with col_back:
        if st.button("← Torna alla griglia"):
            set_state('grid', selected_book=None)
            st.rerun()
    
    with col_edit:
        if is_owner and st.button("✏️ Modifica libro"):
            set_state('edit_book')
            st.rerun()
            
    with col_delete:
        # Mostra il bottone elimina solo se l'utente è il proprietario
        if is_owner:
            # Aggiungiamo uno stato per la conferma di eliminazione
            if 'confirm_delete' not in st.session_state:
                st.session_state.confirm_delete = False
                
            # Gestione della conferma di eliminazione
            if st.session_state.confirm_delete:
                if st.button("⚠️ Conferma eliminazione", key="confirm_delete_btn"):
                    try:
                        # Richiesta al backend per eliminare il libro
                        response = requests.delete(f"{API_URL}/books/{book_id}")
                        
                        if response.status_code == 200:
                            st.success("Libro eliminato con successo!")
                            # Pulisci la cache e torna alla griglia
                            invalidate_caches()
                            # Usa session_state per evitare problemi di render
                            st.session_state.book_deleted = True
                            set_state('grid')
                            st.rerun()
                        else:
                            try:
                                error_detail = response.json().get("detail", "")
                                st.error(f"Errore nell'eliminazione: {error_detail}")
                            except:
                                st.error(f"Errore nell'eliminazione. Codice: {response.status_code}")
                    except Exception as e:
                        st.error(f"Errore di connessione: {str(e)}")
                
                if st.button("✖️ Annulla", key="cancel_delete_btn"):
                    st.session_state.confirm_delete = False
                    st.rerun()
            else:
                # Prima fase: mostra il bottone elimina
                if st.button("🗑️ Elimina libro"):
                    # Verifica se ci sono prestiti attivi
                    active_loans = get_active_loans_for_book(book_id)
                    if active_loans:
                        st.error("Non è possibile eliminare un libro attualmente in prestito.")
                    else:
                        # Mostra la conferma
                        st.session_state.confirm_delete = True
                        st.rerun()
    
    # Resto del codice per visualizzare i dettagli del libro
    col1, col2 = st.columns([1, 2])
    
    # Colonna 1: Copertina
    with col1:
        render_book_cover(book, width=250)
    
    # Colonna 2: Dettagli del libro
    with col2:
        st.title(book['title'])
        st.subheader(f"di {book['author']}")
        
        st.markdown("---")
        
        # Visualizza tutti i metadati disponibili
        metadata_items = [
            ("Editore", book.get('publisher')),
            ("Anno di pubblicazione", book.get('publish_year')),
            ("ISBN", book.get('isbn'))
        ]
        
        # Aggiungi il proprietario se presente
        if book.get('owner_id'):
            owner_name = get_user_name(book['owner_id'])
            metadata_items.append(("Proprietario", owner_name))
        
        # Visualizza i metadati in una tabella elegante
        for label, value in metadata_items:
            if value:
                st.markdown(f"**{label}:** {value}")
        
        st.markdown("---")
        
        if book.get('description'):
            st.markdown("### Descrizione")
            st.markdown(book['description'])
            
        st.markdown("---")

        # Prima della visualizzazione dello stato del libro, aggiungi:
        st.markdown("### Proprietario e stato")

        if is_owner:
            st.markdown("🧑‍💼 **Questo libro appartiene a te**")
        else:
            owner_name = get_user_name(book.get('owner_id'))
            st.markdown(f"👤 **Proprietario:** {owner_name}")

        # Verifica se il libro è preso in prestito dall'utente corrente
        active_loans = get_active_loans_for_book(book_id)
        is_borrower = any(loan.get('user_id') == current_user_id for loan in active_loans)

        # Mostra lo stato dei prestiti in modo più evidente
        if active_loans:
            if is_owner:
                # Il proprietario vede a chi ha prestato il libro
                for loan in active_loans:
                    borrower_name = get_user_name(loan.get('user_id'))
                    loan_date = loan.get('loan_date', '').split('T')[0]
                    return_date = loan.get('return_date', '').split('T')[0] if loan.get('return_date') else 'Non specificata'
                    
                    st.markdown("""
                        <div style="background-color: #ffecb3; padding: 10px; border-radius: 5px; border-left: 4px solid #ffa000;">
                            <h3 style="margin-top: 0; color: #b27500;">📚 Stato: Prestato</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"📖 Prestato a: **{borrower_name}**")
                    st.markdown(f"📅 Data prestito: **{loan_date}**")
                    if return_date and return_date != 'Non specificata':
                        st.markdown(f"🔙 Restituzione prevista: **{return_date}**")
                    
                    # Solo il proprietario può registrare la restituzione
                    if st.button("✓ Registra restituzione", key=f"return_{loan.get('id')}"):
                        with st.spinner("Registrazione della restituzione..."):
                            try:
                                # Crea dati per l'aggiornamento del prestito
                                return_data = {
                                    "return_date": datetime.datetime.now(datetime.timezone.utc).isoformat()
                                }
                                
                                # Invia richiesta al backend
                                response = requests.put(f"{API_URL}/loans/{loan.get('id')}", json=return_data)
                                
                                if response.status_code == 200:
                                    st.success("Restituzione registrata con successo!")
                                    invalidate_caches()
                                    st.rerun()
                                else:
                                    error_detail = response.json().get("detail", "Errore sconosciuto")
                                    st.error(f"Errore nella registrazione: {error_detail}")
                            except Exception as e:
                                st.error(f"Errore di connessione: {str(e)}")
            elif is_borrower:
                # Chi ha preso in prestito vede i dettagli del suo prestito
                for loan in active_loans:
                    if loan.get('user_id') == current_user_id:
                        loan_date = loan.get('loan_date', '').split('T')[0]
                        return_date = loan.get('return_date', '').split('T')[0] if loan.get('return_date') else 'Non specificata'
                        
                        st.markdown("""
                            <div style="background-color: #e3f2fd; padding: 10px; border-radius: 5px; border-left: 4px solid #2196f3;">
                                <h3 style="margin-top: 0; color: #0d47a1;">📘 Stato: Preso in prestito</h3>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown(f"📅 Data prestito: **{loan_date}**")
                        if return_date and return_date != 'Non specificata':
                            st.markdown(f"🔙 Restituzione prevista: **{return_date}**")
                        break
        else:
            # Libro disponibile con stile
            if is_owner:
                st.markdown("""
                    <div style="background-color: #e8f5e9; padding: 10px; border-radius: 5px; border-left: 4px solid #4caf50;">
                        <h3 style="margin-top: 0; color: #2e7d32;">📗 Stato: Disponibile</h3>
                    </div>
                """, unsafe_allow_html=True)
                
                # Pulsante per prestare il libro (solo per il proprietario)
                if st.button("📚 Presta questo libro"):
                    set_state('create_loan', selected_book_for_loan=book_id)
                    st.rerun()