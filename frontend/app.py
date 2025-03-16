import streamlit as st

# Configurazione pagina DEVE essere la prima chiamata Streamlit
st.set_page_config(
    page_title="Biblioteca",
    layout="wide"
)

# Ora importa tutto il resto
from utils.state import initialize_state
from utils.api import invalidate_caches, check_auth_status, is_admin, load_auth_from_cookie
from utils.export import export_all_data
from views.book_grid import show_book_grid
from views.book_detail import show_book_detail
from views.add_book import show_add_book_page
from views.create_loan import show_create_loan_page
from views.edit_book import show_edit_book_page
from views.manage_users import show_manage_users_page
from views.login import show_login_page
from views.register import show_register_page
from static.styles import load_css
from static.scripts import load_scripts

# Inizializza lo state
initialize_state()

# Carica l'autenticazione dai cookie se necessario
if 'auth_token' not in st.session_state or not st.session_state.auth_token:
    load_auth_from_cookie()

# Verifica se l'utente è autenticato
is_authenticated = check_auth_status()

# Sidebar di navigazione
with st.sidebar:
    st.title("Menu")
    
    if is_authenticated:
        # Utente autenticato
        st.success(f"Benvenuto, {st.session_state.user_info['name']}")
        
        # Sezione Libri
        st.subheader("Libri")
        if st.sidebar.button("📚 I miei Libri", use_container_width=True):
            st.session_state.view = 'grid'
            invalidate_caches()
            st.rerun()
        
        if st.sidebar.button("➕ Aggiungi Libro", use_container_width=True):
            st.session_state.view = 'add_book'
            st.rerun()
        
        # Bottone per aggiornamento metadati libri
        if st.sidebar.button("🔄 Aggiorna Metadati Libri", use_container_width=True):
            from utils.api import refresh_missing_metadata
            
            # Usa un placeholder nella sidebar invece dello spinner
            status_placeholder = st.sidebar.empty()
            status_placeholder.info("Aggiornamento in corso...")
            
            # Esegui l'operazione - passando False per aggiornare TUTTI i libri dell'utente
            result = refresh_missing_metadata(only_missing=False)
            
            # Sostituisci il messaggio con il risultato
            status_placeholder.empty()
            
            if result["success"]:
                data = result["data"]
                st.sidebar.success(f"Aggiornamento completato: {data['updated']} libri aggiornati, {data['failed']} non aggiornati")
                
                # Aggiungi pulsante per visualizzare dettagli
                if st.sidebar.button("Vedi dettagli", key="show_metadata_details"):
                    st.session_state.metadata_update_result = data
                    st.session_state.view = 'grid'  # Resta nella vista grid ma mostrerà i dettagli
                    invalidate_caches()
                    st.rerun()
            else:
                st.sidebar.error(f"Errore: {result['error']}")
        
        # Gestione utenti - spostato qui per renderlo visibile a tutti
        st.subheader("Gestione")
        if st.sidebar.button("👥 Gestione Utenti", use_container_width=True):
            st.session_state.view = 'manage_users'
            st.rerun()
        
        # Sostituisci la parte dell'esportazione con questa versione semplificata
        # Sposta qui la sezione esportazione per renderla accessibile a tutti
        if st.sidebar.button("📊 Esporta dati", use_container_width=True):
            # Genera il file ZIP solo con i libri di proprietà dell'utente
            zip_data = export_all_data(only_owned_books=True)
            
            # Crea un link per il download
            st.sidebar.download_button(
                label="📥 Scarica dati (ZIP)",
                data=zip_data,
                file_name="miei_libri_export.zip",
                mime="application/zip",
                use_container_width=True
            )
            
            st.sidebar.success("File di esportazione generato con successo!")
        
        # Il resto della sezione admin solo per amministratori
        if is_admin():
            # Lascia vuoto o aggiungi altre funzionalità solo per admin
            pass
        
        # Sezione Account
        st.subheader("Account")
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            # Rimuovi i dati di autenticazione da session_state
            st.session_state.pop('auth_token', None)
            st.session_state.pop('user_info', None)
            # Elimina anche il cookie di autenticazione
            from utils.api import delete_auth_cookie
            delete_auth_cookie()
            # Imposta la vista su login e ricarica la pagina
            st.session_state.view = 'login'
            invalidate_caches()
            st.rerun()
    else:
        # Utente non autenticato
        st.info("Effettua il login per accedere.")
        
        if st.sidebar.button("🔑 Login", use_container_width=True):
            st.session_state.view = 'login'
            st.rerun()
            
        if st.sidebar.button("👤 Registrati", use_container_width=True):
            st.session_state.view = 'register'
            st.rerun()
    
    # Info
    st.markdown("---")
    st.caption("© 2023 Tommaso Minuto - v1.2")

# Header del contenuto principale
st.title("Book Manager")

# Routing principale
if st.session_state.view == 'login':
    show_login_page()
elif st.session_state.view == 'register':
    show_register_page()
elif not is_authenticated and st.session_state.view not in ['login', 'register']:
    # Reindirizza al login se non autenticato e non è già sulla pagina di login/registrazione
    show_login_page()
elif st.session_state.view == 'grid':
    show_book_grid()
elif st.session_state.view == 'detail':
    show_book_detail()
elif st.session_state.view == 'add_book':
    show_add_book_page()
elif st.session_state.view == 'create_loan':
    show_create_loan_page() 
elif st.session_state.view == 'edit_book':
    show_edit_book_page()
elif st.session_state.view == 'manage_users':
    show_manage_users_page()


# Carica stili CSS e scripts
load_css()
load_scripts()

# Gestione cookie dopo il rendering
if 'delete_auth_cookie_flag' in st.session_state and st.session_state.delete_auth_cookie_flag:
    with st.container():
        st.markdown('<div style="display:none">', unsafe_allow_html=True)
        cookie_manager = get_cookie_manager()  # Renderizza il cookie manager per eliminare il cookie
        st.markdown('</div>', unsafe_allow_html=True)
    del st.session_state.delete_auth_cookie_flag