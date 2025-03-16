import os
import streamlit as st
import requests
import base64
import datetime
import json
import extra_streamlit_components as stx
from streamlit_cookies_manager import EncryptedCookieManager

# Usa variabile d'ambiente, con fallback su localhost
API_URL = os.environ.get("API_URL", "http://localhost:8000")
COOKIE_NAME = "book_manager_auth"
COOKIE_EXPIRY = 30  # giorni

# NON usare cache_resource qui, ma definisci la funzione senza decoratore
_cookie_manager = None

def get_cookie_manager():
    """Ottiene il cookie manager con un singleton"""
    global _cookie_manager
    if (_cookie_manager is None):
        _cookie_manager = stx.CookieManager()
    return _cookie_manager

def save_auth_to_cookie(token, user_info):
    """Salva il token di autenticazione in un cookie"""
    cookie_manager = get_cookie_manager()
    
    # Prepara i dati da salvare
    auth_data = {
        "token": token,
        "user_info": user_info,
        "expiry": (datetime.datetime.now() + datetime.timedelta(days=COOKIE_EXPIRY)).isoformat()
    }
    
    # Converti in JSON
    auth_json = json.dumps(auth_data)
    
    # Imposta il cookie
    cookie_manager.set(
        COOKIE_NAME,
        auth_json,
        expires_at=datetime.datetime.now() + datetime.timedelta(days=COOKIE_EXPIRY)
    )
    
    # Visualizza lo script per impostare il cookie
    st.markdown(cookie_manager.get_script(), unsafe_allow_html=True)

def load_auth_from_cookie():
    """Carica i dati di autenticazione dal cookie"""
    try:
        cookie_manager = get_cookie_manager()
        cookie_value = cookie_manager.get(COOKIE_NAME)
        
        if cookie_value:
            try:
                auth_data = json.loads(cookie_value)
                
                # Verifica se il cookie è scaduto
                expiry = datetime.datetime.fromisoformat(auth_data["expiry"])
                if datetime.datetime.now() < expiry:
                    # Aggiorna lo stato Streamlit con i dati di autenticazione
                    st.session_state.auth_token = auth_data["token"]
                    st.session_state.user_info = auth_data["user_info"]
                    return True
                else:
                    # Cookie scaduto, rimuovilo
                    delete_auth_cookie()
            except Exception as e:
                print(f"Errore nel parsing del cookie: {e}")
                delete_auth_cookie()
        
        return False
    except Exception as e:
        print(f"Errore nel caricamento del cookie: {e}")
        return False

def delete_auth_cookie():
    """Cancella il cookie di autenticazione"""
    try:
        cookie_manager = get_cookie_manager()
        cookie_manager.delete(COOKIE_NAME)
        # Imposta il flag per far rendirizzare il cookie manager dopo
        st.session_state.delete_auth_cookie_flag = True
    except Exception as e:
        print(f"Errore durante l'eliminazione del cookie: {str(e)}")

def get_auth_header():
    """Ottiene l'header di autenticazione se disponibile"""
    if 'auth_token' in st.session_state and st.session_state.auth_token:
        return {"Authorization": f"Bearer {st.session_state.auth_token}"}
    return {}

# Modifica la decorazione della funzione per controllare problemi di cache
@st.cache_data(ttl=60)  # Ridotta a 1 minuto per debug
def fetch_books(limit=10000):  # Imposta un limite molto alto
    """Ottiene la lista dei libri con cache TTL di 1 minuto"""
    headers = get_auth_header()
    try:
        # Passa il parametro limit nella query string
        response = requests.get(f"{API_URL}/books/", headers=headers, params={"limit": limit})
        if response.status_code == 200:
            data = response.json()
            # Aggiungi debug info
            print(f"fetch_books: ricevuti {len(data)} libri")
            return data
        else:
            print(f"Error fetching books: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error connecting to API: {str(e)}")
        return []

@st.cache_data(ttl=300)
def fetch_book(book_id):
    """Ottiene un singolo libro con cache TTL di 5 minuti"""
    headers = get_auth_header()
    response = requests.get(f"{API_URL}/books/{book_id}", headers=headers)
    return response.json() if response.status_code == 200 else None

@st.cache_data(ttl=300)
def fetch_users():
    """Ottiene la lista degli utenti con cache TTL di 5 minuti"""
    headers = get_auth_header()
    response = requests.get(f"{API_URL}/users/", headers=headers)
    return response.json() if response.status_code == 200 else []

@st.cache_data(ttl=60)
def fetch_loans():
    """Ottiene la lista dei prestiti con cache TTL di 1 minuto"""
    headers = get_auth_header()
    response = requests.get(f"{API_URL}/loans/", headers=headers)
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

# Aggiungi funzioni di autenticazione
def check_auth_status():
    """Verifica lo stato di autenticazione dell'utente"""
    return 'auth_token' in st.session_state and st.session_state.auth_token is not None

def get_current_user_id():
    """Ottiene l'ID dell'utente corrente se autenticato"""
    if 'user_info' in st.session_state and st.session_state.user_info:
        return st.session_state.user_info.get('id')
    return None

def is_admin():
    """Verifica se l'utente corrente è un amministratore"""
    if 'user_info' in st.session_state and st.session_state.user_info:
        return st.session_state.user_info.get('role') == 'admin'
    return False

def refresh_missing_metadata(only_missing=False):
    """
    Richiede l'aggiornamento dei metadati per libri.
    
    Args:
        only_missing: Se True, aggiorna solo libri con informazioni mancanti
                     Se False, aggiorna tutti i libri di proprietà dell'utente
    """
    headers = get_auth_header()
    try:
        params = {"only_missing": "true" if only_missing else "false"}
        response = requests.post(
            f"{API_URL}/books/refresh-metadata", 
            headers=headers,
            params=params
        )
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            error_detail = response.json().get("detail", "Errore sconosciuto")
            return {"success": False, "error": error_detail}
    except Exception as e:
        return {"success": False, "error": str(e)}

def search_books(query="", filter_by="all"):
    """
    Cerca libri nel database in base a filtri e una query testuale.
    
    Args:
        query: Testo da cercare in titolo, autore, ISBN
        filter_by: Filtro per stato (all, available, loaned)
    """
    headers = get_auth_header()
    
    # Se non ci sono filtri attivi, usa la funzione standard fetch_books
    # per garantire la retrocompatibilità e evitare problemi
    if query == "" and filter_by == "all":
        return fetch_books()
    
    # Altrimenti usa l'endpoint di ricerca specializzato
    params = {
        "query": query,
        "filter_by": filter_by
    }
    
    try:
        response = requests.get(f"{API_URL}/books/search/", headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error searching books: {response.status_code}")
            # In caso di errore, ritorna alla lista completa
            return fetch_books()
    except Exception as e:
        print(f"Error connecting to API: {str(e)}")
        # In caso di eccezione, ritorna alla lista completa
        return fetch_books()