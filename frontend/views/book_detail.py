import streamlit as st
import datetime
import requests
from utils.api import fetch_book, get_book_cover_url, get_user_name, get_active_loans_for_book, invalidate_caches
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
    
    # Bottoni di azione
    col_back, col_edit = st.columns([1, 1])
    with col_back:
        if st.button("← Torna alla griglia"):
            set_state('grid', selected_book=None)
            st.rerun()
    with col_edit:
        if st.button("✏️ Modifica libro"):
            set_state('edit_book')
            st.rerun()
    
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

        # Mostra lo stato dei prestiti in modo più evidente
        active_loans = get_active_loans_for_book(book_id)
        if active_loans:
            # Evidenzia visivamente lo stato di prestito
            st.markdown("""
                <div style="background-color: #ffecb3; padding: 10px; border-radius: 5px; border-left: 4px solid #ffa000;">
                    <h3 style="margin-top: 0; color: #b27500;">📚 Stato: In Prestito</h3>
                </div>
            """, unsafe_allow_html=True)
            
            for loan in active_loans:
                user_name = get_user_name(loan.get('user_id'))
                loan_date = loan.get('loan_date', '').split('T')[0]  # Estrae solo la data
                
                # Data di restituzione prevista (se disponibile)
                return_date = None
                if loan.get('return_date'):
                    return_date = loan.get('return_date').split('T')[0]
                    
                st.markdown(f"📖 Prestato a: **{user_name}**")
                st.markdown(f"📅 Data prestito: **{loan_date}**")
                if return_date:
                    st.markdown(f"🔙 Restituzione prevista: **{return_date}**")
                
                # Aggiungi pulsante per registrare la restituzione
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
                                # Aggiorna la cache dei prestiti E del libro specifico
                                invalidate_caches()
                                # Ricarica la pagina
                                st.rerun()
                            else:
                                error_detail = response.json().get("detail", "Errore sconosciuto")
                                st.error(f"Errore nella registrazione: {error_detail}")
                        except Exception as e:
                            st.error(f"Errore di connessione: {str(e)}")
        else:
            # Libro disponibile con stile
            st.markdown("""
                <div style="background-color: #e8f5e9; padding: 10px; border-radius: 5px; border-left: 4px solid #4caf50;">
                    <h3 style="margin-top: 0; color: #2e7d32;">📗 Stato: Disponibile</h3>
                </div>
            """, unsafe_allow_html=True)
            
            # Pulsante per prestare il libro
            if st.button("📚 Presta questo libro"):
                set_state('create_loan', selected_book_for_loan=book_id)
                st.rerun()