import pandas as pd
import streamlit as st
import io
import zipfile
from utils.api import fetch_books, fetch_users, fetch_loans, fetch_book

def export_all_data():
    """Esporta tutti i dati in file CSV e restituisce un file ZIP"""
    try:
        # Crea un buffer in memoria per il file ZIP
        zip_buffer = io.BytesIO()
        
        # Crea un oggetto ZIP
        with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
            # Esporta libri
            books_csv = export_books_csv()
            zip_file.writestr('libri.csv', books_csv)
            
            # Esporta utenti
            users_csv = export_users_csv()
            zip_file.writestr('utenti.csv', users_csv)
            
            # Esporta prestiti
            loans_csv = export_loans_csv()
            zip_file.writestr('prestiti.csv', loans_csv)
            
            # Aggiungi un file README
            readme_text = """
# Export Biblioteca
Questo archivio contiene i dati esportati della biblioteca.

## File inclusi:
- libri.csv: L'elenco completo dei libri nella biblioteca
- utenti.csv: L'elenco degli utenti registrati
- prestiti.csv: Lo storico dei prestiti

Esportato il: {date}
            """.format(date=pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            zip_file.writestr('README.txt', readme_text)
        
        # Posiziona il puntatore all'inizio del file
        zip_buffer.seek(0)
        return zip_buffer
    
    except Exception as e:
        st.error(f"Errore durante l'esportazione: {str(e)}")
        return None

def export_books_csv():
    """Esporta i dati dei libri in formato CSV"""
    books = fetch_books()
    
    # Crea DataFrame con i dati dei libri
    df = pd.DataFrame(books)
    
    # Elimina colonne che non vogliamo esportare
    if 'has_cover' in df.columns:
        df = df.drop('has_cover', axis=1)
    
    # Aggiungi informazioni sul proprietario
    if 'owner_id' in df.columns and not df['owner_id'].isna().all():
        df['owner_name'] = df['owner_id'].apply(
            lambda x: fetch_users_dict().get(x, {}).get('name', 'Sconosciuto') if x else 'Nessuno'
        )
    
    # Converti il DataFrame in CSV
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue()

def export_users_csv():
    """Esporta i dati degli utenti in formato CSV"""
    users = fetch_users()
    
    # Crea DataFrame con i dati degli utenti
    df = pd.DataFrame(users)
    
    # Converti il DataFrame in CSV
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue()

def export_loans_csv():
    """Esporta i dati dei prestiti in formato CSV"""
    loans = fetch_loans()
    
    # Crea DataFrame con i dati dei prestiti
    df = pd.DataFrame(loans)
    
    # Aggiungi informazioni sul libro e utente
    if not df.empty:
        # Cache per i libri e gli utenti
        books_dict = fetch_books_dict()
        users_dict = fetch_users_dict()
        
        # Aggiungi titolo del libro
        df['book_title'] = df['book_id'].apply(
            lambda x: books_dict.get(x, {}).get('title', 'Libro sconosciuto')
        )
        
        # Aggiungi nome dell'utente
        df['user_name'] = df['user_id'].apply(
            lambda x: users_dict.get(x, {}).get('name', 'Utente sconosciuto')
        )
        
        # Formatta le date
        if 'loan_date' in df.columns:
            df['loan_date'] = pd.to_datetime(df['loan_date']).dt.strftime('%Y-%m-%d')
        if 'return_date' in df.columns:
            df['return_date'] = pd.to_datetime(df['return_date']).dt.strftime('%Y-%m-%d')
    
    # Converti il DataFrame in CSV
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue()

# Funzioni helper
@st.cache_data(ttl=300)
def fetch_books_dict():
    """Ottiene un dizionario di libri con ID come chiavi"""
    books = fetch_books()
    return {book['id']: book for book in books}

@st.cache_data(ttl=300)
def fetch_users_dict():
    """Ottiene un dizionario di utenti con ID come chiavi"""
    users = fetch_users()
    return {user['id']: user for user in users}