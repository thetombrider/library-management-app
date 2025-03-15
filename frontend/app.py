import streamlit as st
from utils.state import initialize_state
from utils.api import invalidate_caches
from views.book_grid import show_book_grid
from views.book_detail import show_book_detail
from views.add_book import show_add_book_page
from views.create_loan import show_create_loan_page
from views.edit_book import show_edit_book_page
from static.styles import load_css
from static.scripts import load_scripts

# Configurazione pagina
st.set_page_config(
    page_title="Biblioteca",
    layout="wide"
)

# Inizializza lo state
initialize_state()

# Header
st.title("La Mia Biblioteca")

# Menu di navigazione
menu = st.columns([1, 1, 3])
with menu[0]:
    if st.button("📚 Visualizza Libri"):
        st.session_state.view = 'grid'
        invalidate_caches()
        st.rerun()
with menu[1]:
    if st.button("➕ Aggiungi Libro"):
        st.session_state.view = 'add_book'
        st.rerun()

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

# Carica stili CSS e scripts
load_css()
load_scripts()