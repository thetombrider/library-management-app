import streamlit as st
from utils.state import initialize_state
from utils.api import invalidate_caches, check_auth_status, is_admin
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

# Configurazione pagina
st.set_page_config(
    page_title="Biblioteca",
    layout="wide"
)

# Inizializza lo state
initialize_state()

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
        
        # Sezione Utenti (solo per admin)
        if is_admin():
            st.subheader("Amministrazione")
            if st.sidebar.button("👥 Gestione Utenti", use_container_width=True):
                st.session_state.view = 'manage_users'
                st.rerun()
            
            # Sezione Esportazione
            if st.sidebar.button("📊 Esporta Dati (CSV)", use_container_width=True):
                # Genera il file ZIP con i CSV
                zip_data = export_all_data()
                
                # Crea un link per il download
                st.sidebar.download_button(
                    label="📥 Scarica dati (ZIP)",
                    data=zip_data,
                    file_name="biblioteca_export.zip",
                    mime="application/zip",
                    use_container_width=True
                )
                
                st.sidebar.success("File di esportazione generato con successo!")
        
        # Sezione Account
        st.subheader("Account")
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            # Rimuovi i dati di autenticazione
            st.session_state.pop('auth_token', None)
            st.session_state.pop('user_info', None)
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
    st.caption("© 2023 La Mia Biblioteca")

# Header del contenuto principale
st.title("La Mia Biblioteca")

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
    # Verifica se l'utente è admin
    if is_admin():
        show_manage_users_page()
    else:
        st.error("Non hai i permessi per accedere a questa pagina")

# Carica stili CSS e scripts
load_css()
load_scripts()