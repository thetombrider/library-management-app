import streamlit as st
from utils.state import initialize_state
from utils.api import invalidate_caches
from utils.export import export_all_data
from views.book_grid import show_book_grid
from views.book_detail import show_book_detail
from views.add_book import show_add_book_page
from views.create_loan import show_create_loan_page
from views.edit_book import show_edit_book_page
from views.manage_users import show_manage_users_page
from static.styles import load_css
from static.scripts import load_scripts

# Configurazione pagina
st.set_page_config(
    page_title="Biblioteca",
    layout="wide"
)

# Inizializza lo state
initialize_state()

# Sidebar di navigazione
with st.sidebar:
    st.title("Menu")
    
    # Sezione Libri
    st.subheader("Libri")
    if st.sidebar.button("📚 Visualizza Libri", use_container_width=True):
        st.session_state.view = 'grid'
        invalidate_caches()
        st.rerun()
    
    if st.sidebar.button("➕ Aggiungi Libro", use_container_width=True):
        st.session_state.view = 'add_book'
        st.rerun()
    
    # Sezione Utenti
    st.subheader("Utenti")
    if st.sidebar.button("👥 Gestione Utenti", use_container_width=True):
        st.session_state.view = 'manage_users'
        st.rerun()
    
    # Sezione Esportazione
    st.subheader("Utilità")
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
    
    # Info
    st.markdown("---")
    st.caption("© 2023 La Mia Biblioteca")

# Header del contenuto principale
st.title("La Mia Biblioteca")

# Routing
if st.session_state.view == 'grid':
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