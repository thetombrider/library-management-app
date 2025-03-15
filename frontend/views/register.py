import streamlit as st
import requests
import re
from utils.state import set_state
from utils.api import invalidate_caches, API_URL

def validate_email(email):
    """Validazione semplice dell'email"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validazione semplice della password (minimo 8 caratteri)"""
    return len(password) >= 8

def show_register_page():
    """Mostra la pagina di registrazione"""
    st.title("Registrazione Nuovo Utente")
    
    with st.form("register_form"):
        name = st.text_input("Nome completo")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password", 
                               help="La password deve essere di almeno 8 caratteri")
        confirm_password = st.text_input("Conferma password", type="password")
        
        submit = st.form_submit_button("Registrati")
    
    if submit:
        # Validazione
        errors = []
        
        if not name:
            errors.append("Il nome è obbligatorio")
        
        if not email:
            errors.append("L'email è obbligatoria")
        elif not validate_email(email):
            errors.append("L'email non è valida")
        
        if not password:
            errors.append("La password è obbligatoria")
        elif not validate_password(password):
            errors.append("La password deve essere di almeno 8 caratteri")
        
        if password != confirm_password:
            errors.append("Le password non coincidono")
        
        # Mostra errori se presenti
        if errors:
            for error in errors:
                st.error(error)
        else:
            # Invia richiesta di registrazione
            with st.spinner("Registrazione in corso..."):
                try:
                    # Prepara dati utente
                    user_data = {
                        "name": name,
                        "email": email,
                        "password": password
                    }
                    
                    # Invia richiesta al backend
                    response = requests.post(f"{API_URL}/auth/register", json=user_data)
                    
                    if response.status_code == 200:
                        st.success(f"Registrazione completata con successo! Benvenuto {name}.")
                        
                        # Pulisci le cache
                        invalidate_caches()
                        
                        # Opzioni dopo la registrazione
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Accedi ora"):
                                set_state('login')
                                st.rerun()
                                
                        with col2:
                            if st.button("Torna alla home"):
                                set_state('grid')
                                st.rerun()
                    else:
                        try:
                            error_detail = response.json().get("detail", "")
                            st.error(f"Errore nella registrazione: {error_detail}")
                        except:
                            st.error(f"Errore nella registrazione. Codice: {response.status_code}")
                except Exception as e:
                    st.error(f"Errore di connessione: {str(e)}")
    
    # Link per il login
    st.markdown("---")
    st.write("Hai già un account?")
    if st.button("Accedi"):
        set_state('login')
        st.rerun()