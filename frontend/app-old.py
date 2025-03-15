import streamlit as st
import requests
import base64
import math
import datetime

# Configurazione
API_URL = "http://localhost:8000"
BOOKS_PER_ROW = 4  # Numero di libri per riga



def fetch_books():
    """Ottiene la lista dei libri con cache TTL di 5 minuti"""
    response = requests.get(f"{API_URL}/books/")
    return response.json() if response.status_code == 200 else []


def fetch_book(book_id):
    """Ottiene un singolo libro con cache TTL di 5 minuti"""
    response = requests.get(f"{API_URL}/books/{book_id}")
    return response.json() if response.status_code == 200 else None


def fetch_users():
    """Ottiene la lista degli utenti con cache TTL di 5 minuti"""
    response = requests.get(f"{API_URL}/users/")
    return response.json() if response.status_code == 200 else []


def fetch_loans():
    """Ottiene la lista dei prestiti con cache TTL"""
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

# Funzione per ottenere l'URL della copertina
def get_book_cover_url(book_id):
    """Restituisce l'URL della copertina o l'immagine cached"""
    cover = get_book_cover(book_id)
    if cover:
        return cover
    return f"{API_URL}/books/{book_id}/cover"

# Funzione utility per trovare il nome dell'utente dato l'ID
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
    loans = fetch_loans()
    active_loans = []
    now = datetime.datetime.now()
    
    for loan in loans:
        if loan.get('book_id') != book_id:
            continue
            
        # Converti le stringhe di date in oggetti datetime
        return_date = None
        if loan.get('return_date'):
            try:
                # Supporta sia formato con T che senza
                return_date_str = loan.get('return_date').replace('Z', '+00:00')
                return_date = datetime.datetime.fromisoformat(return_date_str)
            except ValueError:
                # Fallback meno preciso se fromisoformat fallisce
                try:
                    return_date = datetime.datetime.strptime(
                        loan.get('return_date').split('T')[0], 
                        '%Y-%m-%d'
                    )
                except:
                    pass
        
        # Un prestito è attivo se return_date è None o è nel futuro
        is_active = return_date is None or return_date > now
        if is_active:
            active_loans.append(loan)
            
    return active_loans

# Configurazione pagina
st.set_page_config(
    page_title="Biblioteca",
    layout="wide"
)

# Inizializza lo state
if 'view' not in st.session_state:
    st.session_state.view = 'grid'  # possibili valori: 'grid', 'detail', 'add_book'
if 'selected_book' not in st.session_state:
    st.session_state.selected_book = None
if 'scanned_isbn' not in st.session_state:
    st.session_state.scanned_isbn = None

# Da inserire subito dopo l'inizializzazione dello state
# Controlla se c'è un ISBN nei parametri dell'URL
if 'isbn' in st.query_params:
    st.session_state.scanned_isbn = st.query_params['isbn']
    st.session_state.view = 'add_book'
    # Pulisci l'URL dopo aver letto il parametro
    

# Header
st.title("La Mia Biblioteca")

# Menu di navigazione
menu = st.columns([1, 1, 3])
with menu[0]:
    if st.button("📚 Visualizza Libri"):
        st.session_state.view = 'grid'
        st.rerun()
with menu[1]:
    if st.button("➕ Aggiungi Libro"):
        st.session_state.view = 'add_book'
        st.rerun()

# Funzione per mostrare la griglia dei libri
def show_book_grid():
    books = fetch_books()
    
    if not books:
        st.info("Nessun libro disponibile nella biblioteca.")
        return
    
    # Calcola il numero di righe necessarie
    num_rows = math.ceil(len(books) / BOOKS_PER_ROW)
    
    for row_idx in range(num_rows):
        # Crea una riga di colonne
        cols = st.columns(BOOKS_PER_ROW)
        
        for col_idx in range(BOOKS_PER_ROW):
            book_idx = row_idx * BOOKS_PER_ROW + col_idx
            
            # Controlla se abbiamo ancora libri da mostrare
            if (book_idx < len(books)):
                book = books[book_idx]
                
                with cols[col_idx]:
                    # Container per il libro
                    with st.container():
                        # Mostra la copertina se disponibile
                        if book.get('has_cover', False):
                            st.image(get_book_cover_url(book['id']), width=150)
                        else:
                            # Copertina placeholder
                            st.markdown(
                                """
                                <div style="width: 150px; height: 200px; 
                                        background-color: #f0f0f0; 
                                        border-radius: 5px;
                                        display: flex; 
                                        align-items: center; 
                                        justify-content: center;
                                        margin: 0 auto;">
                                    <span style="color: #999;">No Cover</span>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                                
                        # Titolo e autore sotto la copertina
                        st.markdown(f"**{book['title'][:25]}**")
                        st.markdown(f"{book['author'][:25]}")
                        
                        # Bottone per vedere i dettagli
                        if st.button("Dettagli", key=f"btn_{book['id']}"):
                            st.session_state.view = 'detail'
                            st.session_state.selected_book = book['id']
                            st.rerun()

# Funzione per mostrare i dettagli del libro
def show_book_detail():
    book_id = st.session_state.selected_book
    book = fetch_book(book_id)
    
    if not book:
        st.error("Libro non trovato")
        return
    
    # Bottone per tornare alla griglia
    if st.button("← Torna alla griglia"):
        st.session_state.view = 'grid'
        st.session_state.selected_book = None
        st.rerun()
    
    col1, col2 = st.columns([1, 2])
    
    # Colonna 1: Copertina
    with col1:
        if book.get('has_cover', False):
            st.image(get_book_cover_url(book_id), width=250)
        else:
            st.markdown(
                """
                <div style="width: 200px; height: 300px; 
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
                st.session_state.view = 'create_loan'
                st.session_state.selected_book_for_loan = book_id
                st.rerun()

# Funzione semplificata per aggiungere un libro tramite ISBN
def show_add_book_page():
    st.title("Aggiungi un Nuovo Libro")
    st.subheader("Inserisci l'ISBN e lascia che il sistema recuperi automaticamente i dettagli")
    
    with st.form("isbn_entry"):
        isbn = st.text_input("ISBN del libro:", placeholder="Es. 9788804507451")
        submit = st.form_submit_button("Aggiungi Libro")
        
        if submit:
            if not isbn:
                st.error("È necessario inserire un ISBN.")
            else:
                with st.spinner("Recupero informazioni dal database Google Books..."):
                    try:
                        response = requests.post(f"{API_URL}/books/", json={"isbn": isbn})
                        
                        if response.status_code == 200:
                            book = response.json()
                            st.success("Libro aggiunto con successo!")
                            
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
                        else:
                            st.error(f"Errore: {response.json().get('detail', 'Errore sconosciuto')}")
                    except Exception as e:
                        st.error(f"Errore: {str(e)}")

# Funzione per creare un nuovo prestito
def show_create_loan_page():
    book_id = st.session_state.selected_book_for_loan
    book = fetch_book(book_id)
    
    if not book:
        st.error("Libro non trovato")
        st.button("Torna alla home", on_click=lambda: set_state('grid'))
        return
    
    st.title(f"Presta il libro: {book['title']}")
    
    # Visualizza le informazioni del libro
    col1, col2 = st.columns([1, 2])
    with col1:
        if book.get('has_cover', False):
            st.image(get_book_cover_url(book_id), width=150)
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
        st.warning("Non ci sono utenti disponibili a cui prestare il libro")
        if st.button("← Torna al libro"):
            st.session_state.view = 'detail'
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
            st.session_state.view = 'detail'
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
                        
                        # Invia richiesta al backend
                        response = requests.post(f"{API_URL}/loans/", json=loan_data)
                        
                        if response.status_code == 200:
                            st.success(f"Libro prestato con successo a {selected_user_display.split('(')[0].strip()}")
                            # Aggiungi pulsante per tornare alla home
                            if st.button("Torna alla home"):
                                st.session_state.view = 'grid'
                                # Forziamo l'aggiornamento della cache dei prestiti
                              
                                st.rerun()
                        else:
                            error_detail = response.json().get("detail", "Errore sconosciuto")
                            st.error(f"Errore nel prestito: {error_detail}")
                    except Exception as e:
                        st.error(f"Errore di connessione: {str(e)}")
            else:
                st.error("Seleziona un destinatario per il prestito")

# Funzione helper per impostare lo stato
def set_state(view_name, **kwargs):
    st.session_state.view = view_name
    for key, value in kwargs.items():
        st.session_state[key] = value

# JavaScript per intercettare i click sulle copertine
js = """
<script>
window.addEventListener('message', function(e) {
    if (e.data.type === 'book_click') {
        // Codice esistente
        document.querySelector('button[key="btn_' + e.data.bookId + '"]').click();
    } else if (e.data.type === 'isbn_scanned') {
        // Nuovo codice per la scansione ISBN
        console.log('ISBN scansionato:', e.data.isbn);
        
        // Invece di usare streamlit:setComponentValue, facciamo un rerun con parametro
        const currentUrl = new URL(window.location.href);
        currentUrl.searchParams.set('isbn', e.data.isbn);
        window.location.href = currentUrl.toString();
    }
});
</script>
"""
st.components.v1.html(js, height=0)

# Aggiungi il callback per gestire l'evento di scansione ISBN
def on_isbn_scanned(isbn):
    st.session_state.scanned_isbn = isbn
    # Non fare il rerun qui, verrà gestito dal componente JavaScript

# Routing
if st.session_state.view == 'grid':
    show_book_grid()
elif st.session_state.view == 'detail':
    show_book_detail()
elif st.session_state.view == 'add_book':
    show_add_book_page()
elif st.session_state.view == 'create_loan':
    show_create_loan_page()

# Stile CSS
st.markdown(
    """
    <style>
    .stButton>button {
        width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True
)