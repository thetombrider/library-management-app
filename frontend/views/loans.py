import streamlit as st
import pandas as pd
import datetime
import requests
from utils.api import fetch_loans, fetch_books, fetch_users, get_auth_header, API_URL, invalidate_caches, get_book_owner_name
from utils.state import set_state

def show_loans_page():
    """Mostra la pagina di monitoraggio dei prestiti"""
    st.title("Monitoraggio Prestiti")
    
    # Recupera i dati necessari
    loans = fetch_loans()
    books = {book['id']: book for book in fetch_books()}
    users = {user['id']: user for user in fetch_users()}
    
    if not loans:
        st.info("Non hai prestiti attivi o passati da visualizzare.")
        return
    
    # Ottieni l'ID dell'utente corrente
    current_user_id = st.session_state.user_info['id']
    
    # Prepara i dati per il dataframe
    loans_data = []
    now = datetime.datetime.now(datetime.timezone.utc)
    
    for loan in loans:
        book_id = loan.get('book_id')
        user_id = loan.get('user_id')
        
        # Salta se il libro o l'utente non esiste nei dati recuperati
        if book_id not in books or user_id not in users:
            continue
        
        book = books[book_id]
        user = users[user_id]
        
        # Determina il ruolo dell'utente corrente in questo prestito
        if book.get('owner_id') == current_user_id:
            role = "prestatore"  # Ho prestato un mio libro
        elif user_id == current_user_id:
            role = "destinatario"  # Ho preso in prestito un libro
        else:
            continue  # Prestito non collegato all'utente corrente
        
        # Formatta le date
        loan_date = loan.get('loan_date', '').split('T')[0] if loan.get('loan_date') else ""
        return_date = loan.get('return_date', '').split('T')[0] if loan.get('return_date') else ""
        
        # Determina lo stato del prestito
        if not return_date:
            status = "In corso"
        else:
            # Prova a convertire la data di restituzione
            try:
                # Rimuovi la parte dell'ora per un confronto basato solo sulla data
                return_date_parts = return_date.split('-')
                now_date = datetime.datetime.now().date()
                
                if len(return_date_parts) == 3:
                    return_date_obj = datetime.date(
                        year=int(return_date_parts[0]),
                        month=int(return_date_parts[1]),
                        day=int(return_date_parts[2])
                    )
                    
                    # Confronta solo le date senza considerare l'ora
                    if return_date_obj >= now_date:
                        status = "In corso"
                    else:
                        status = "Restituito"
                else:
                    status = "In corso"  # Fallback se il formato della data non è valido
            except Exception as e:
                print(f"Errore nella conversione della data: {e}")
                status = "In corso"  # Fallback
        
        # Aggiungi alla lista dei dati
        loans_data.append({
            "id": loan.get('id'),
            "Titolo": book.get('title'),
            "Autore": book.get('author'),
            "Prestato a": user.get('name') if role == "prestatore" else "Me",
            "Prestato da": "Me" if role == "prestatore" else get_book_owner_name(book),
            "Data prestito": loan_date,
            "Data restituzione": return_date if return_date else "Non restituito",
            "Stato": status,
            "Ruolo": role,
            "book_id": book_id,
            "user_id": user_id
        })
    
    if not loans_data:
        st.info("Non ci sono prestiti collegati al tuo account.")
        return
    
    # Filtri
    st.subheader("Filtri")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        role_filter = st.selectbox(
            "Mostra prestiti:",
            ["Tutti", "Prestati da me", "Presi in prestito da me"]
        )
    
    with col2:
        status_filter = st.selectbox(
            "Stato:",
            ["Tutti", "In corso", "Restituiti"]
        )
    
    # Filtra i dati in base alle selezioni
    filtered_data = loans_data
    
    if role_filter == "Prestati da me":
        filtered_data = [loan for loan in filtered_data if loan["Ruolo"] == "prestatore"]
    elif role_filter == "Presi in prestito da me":
        filtered_data = [loan for loan in filtered_data if loan["Ruolo"] == "destinatario"]
    
    if status_filter == "In corso":
        filtered_data = [loan for loan in filtered_data if loan["Stato"] == "In corso"]
    elif status_filter == "Restituiti":
        filtered_data = [loan for loan in filtered_data if loan["Stato"] == "Restituito"]
    
    # Visualizza i dati in una tabella interattiva
    if filtered_data:
        # Crea un DataFrame per la visualizzazione
        df = pd.DataFrame(filtered_data)
        
        # Rimuovi colonne non necessarie per la visualizzazione
        display_df = df[["Titolo", "Autore", "Prestato a", "Prestato da", "Data prestito", "Data restituzione", "Stato"]]
        
        # Visualizza la tabella
        st.dataframe(display_df, hide_index=True)
        
    else:
        st.info("Nessun prestito corrisponde ai filtri selezionati.")