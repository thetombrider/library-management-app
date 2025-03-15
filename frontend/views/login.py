import streamlit as st
import requests
import json
from utils.state import set_state
from utils.api import invalidate_caches, API_URL

def show_login_page():
    """Mostra la pagina di login"""
    st.title("Accesso al sistema")
    
    # Se l'utente è già loggato, mostra un messaggio
    if 'auth_token' in st.session_state and st.session_state.auth_token:
        st.success(f"Hai già effettuato l'accesso come {st.session_state.user_info['name']}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🏠 Vai alla home"):
                set_state('grid')
                st.rerun()
        with col2:
            if st.button("🚪 Logout"):
                # Rimuovi i dati di autenticazione
                st.session_state.pop('auth_token', None)
                st.session_state.pop('user_info', None)
                st.session_state.pop('auth_expiry', None)
                invalidate_caches()
                st.rerun()
        return
    
    # Form di login
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Accedi")
    
    if submit:
        if not email or not password:
            st.error("Email e password sono richiesti")
        else:
            with st.spinner("Autenticazione in corso..."):
                try:
                    # Form data per il login
                    data = {
                        "username": email,  # FastAPI OAuth2 usa 'username'
                        "password": password
                    }
                    
                    # Esegui la richiesta al backend
                    response = requests.post(
                        f"{API_URL}/auth/token", 
                        data=data,  # Usa data invece di json per form
                        headers={"Content-Type": "application/x-www-form-urlencoded"}
                    )
                    
                    if response.status_code == 200:
                        # Login riuscito
                        auth_data = response.json()
                        
                        # Salva dati autenticazione in session_state
                        st.session_state.auth_token = auth_data["access_token"]
                        st.session_state.user_info = auth_data["user"]
                        
                        # Pulisci cache API
                        invalidate_caches()
                        
                        # Messaggio di successo
                        st.success(f"Benvenuto, {auth_data['user']['name']}!")
                        
                        # Opzioni dopo il login
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("🏠 Vai alla home"):
                                set_state('grid')
                                st.rerun()
                    else:
                        try:
                            error_detail = response.json().get("detail", "")
                            st.error(f"Errore di autenticazione: {error_detail}")
                        except:
                            st.error(f"Errore di autenticazione. Codice: {response.status_code}")
                except Exception as e:
                    st.error(f"Errore di connessione: {str(e)}")
    
    # Link per la registrazione
    st.markdown("---")
    st.write("Non hai un account?")
    if st.button("Registrati"):
        set_state('register')
        st.rerun()