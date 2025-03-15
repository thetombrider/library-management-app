import streamlit as st
import requests
import base64
import datetime

# Configurazione
API_URL = "http://localhost:8000"

@st.cache_data(ttl=300)
def fetch_books():
    """Ottiene la lista dei libri con cache TTL di 5 minuti"""
    response = requests.get(f"{API_URL}/books/")
    return response.json() if response.status_code == 200 else []

@st.cache_data(ttl=300)
def fetch_book(book_id):
    """Ottiene un singolo libro con cache TTL di 5 minuti"""
    response = requests.get(f"{API_URL}/books/{book_id}")
    return response.json() if response.status_code == 200 else None

@st.cache_data(ttl=300)
def fetch_users():
    """Ottiene la lista degli utenti con cache TTL di 5 minuti"""
    response = requests.get(f"{API_URL}/users/")
    return response.json() if response.status_code == 200 else []

@st.cache_data(ttl=60)
def fetch_loans():
    """Ottiene la lista dei prestiti con cache TTL di 1 minuto"""
    response = requests.get(f"{API_URL}/loans/")
    return response.json() if response.status_code == 200 else []

# Cache per le immagini delle copertine
@st.cache_data(ttl=300)
def get_book_cover(book_id):
    """Carica e memorizza nella cache l'immagine della copertina"""
    try:
        response = requests.get(f"{API_URL}/books/{book_id}/cover")
        if response.status_code == 200:
            img_data = base64.b64encode(response.content).decode('utf-8')
            return f"data:image/jpeg;base64,{img_data}"
        return None
    except Exception:
        return None

def get_book_cover_url(book_id):
    """Restituisce l'URL della copertina o l'immagine cached"""
    cover = get_book_cover(book_id)
    if cover:
        return cover
    return f"{API_URL}/books/{book_id}/cover"

def get_user_name(user_id):
    """Recupera il nome dell'utente dato l'ID"""
    if not user_id:
        return None
    users = fetch_users()
    for user in users:
        if user.get('id') == user_id:
            return user.get('name', 'Sconosciuto')
    return f"Utente ID: {user_id}"

def get_active_loans_for_book(book_id):
    """Recupera i prestiti attivi per un libro specifico"""
    # Forza refresh dei prestiti
    fetch_loans.clear()
    loans = fetch_loans()
    
    # Converti book_id in stringa per confronto sicuro
    book_id_str = str(book_id)
    
    # Trova il prestito più recente per questo libro
    latest_loan = None
    for loan in loans:
        if str(loan.get('book_id')) == book_id_str:
            if latest_loan is None or loan.get('id', 0) > latest_loan.get('id', 0):
                latest_loan = loan
    
    # Se non c'è nessun prestito, il libro è disponibile
    if latest_loan is None:
        return []
    
    # Un libro è in prestito attivo SE:
    # 1. Non ha data di restituzione
    # 2. La data di restituzione è nel futuro
    
    # Caso 1: Nessuna data di restituzione
    if latest_loan.get('return_date') is None:
        return [latest_loan]
    
    # Caso 2: La data di restituzione è nel futuro
    now = datetime.datetime.now(datetime.timezone.utc)
    
    # Converti la data di stringa a datetime
    try:
        return_date_str = latest_loan.get('return_date')
        
        # Normalizza formato data
        if return_date_str.endswith('Z'):
            return_date_str = return_date_str.replace('Z', '+00:00')
        elif '+' not in return_date_str and 'T' in return_date_str:
            return_date_str = f"{return_date_str}+00:00"
            
        return_date = datetime.datetime.fromisoformat(return_date_str)
        
        if return_date > now:
            return [latest_loan]
        else:
            # Data nel passato, libro disponibile
            return []
    except Exception as e:
        # In caso di errore nella conversione, mostriamo il libro disponibile
        print(f"Errore nel parsing della data di restituzione: {e}")
        return []

def invalidate_caches():
    """Pulisce tutte le cache"""
    st.cache_data.clear()