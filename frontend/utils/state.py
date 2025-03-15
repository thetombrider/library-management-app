import streamlit as st

def initialize_state():
    """Inizializza lo stato dell'applicazione"""
    if 'view' not in st.session_state:
        st.session_state.view = 'grid'  # possibili valori: 'grid', 'detail', 'add_book'
    if 'selected_book' not in st.session_state:
        st.session_state.selected_book = None
    if 'selected_book_for_loan' not in st.session_state:
        st.session_state.selected_book_for_loan = None
    if 'scanned_isbn' not in st.session_state:
        st.session_state.scanned_isbn = None
    
    # Controlla se c'è un ISBN nei parametri dell'URL
    if 'isbn' in st.query_params:
        st.session_state.scanned_isbn = st.query_params['isbn']
        st.session_state.view = 'add_book'

def set_state(view_name, **kwargs):
    """Funzione helper per impostare lo stato"""
    st.session_state.view = view_name
    for key, value in kwargs.items():
        st.session_state[key] = value

def go_to_home():
    """Funzione callback per tornare alla home e pulire la cache"""
    from utils.api import invalidate_caches
    
    st.session_state.view = 'grid'
    st.session_state.selected_book = None
    st.session_state.selected_book_for_loan = None
    if 'loan_completed' in st.session_state:
        del st.session_state.loan_completed
        
    # Pulisci le cache
    invalidate_caches()