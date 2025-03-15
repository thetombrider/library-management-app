import streamlit as st
import requests
from utils.api import fetch_users, fetch_loans, invalidate_caches
from utils.state import set_state
from components.ui import show_message_box

# Configurazione
API_URL = "http://localhost:8000"

def get_active_loans_for_user(user_id):
    """Recupera i prestiti attivi per un utente specifico"""
    # Forza aggiornamento dei prestiti ogni volta per evitare cache stale
    fetch_loans.clear()
    loans = fetch_loans()
    active_loans = []
    
    # Debug
    print(f"Cercando prestiti per utente ID: {user_id}")
    print(f"Totale prestiti trovati: {len(loans)}")
    
    # Converti user_id in stringa per confronto sicuro
    user_id_str = str(user_id)
    
    for loan in loans:
        loan_user_id = str(loan.get('user_id'))
        
        # Debug
        print(f"Confronto: {loan_user_id} == {user_id_str} -> {loan_user_id == user_id_str}")
        
        if loan_user_id == user_id_str:
            print(f"Trovato prestito per utente {user_id}: {loan}")
            
            # Caso 1: Se non c'è data di restituzione, il prestito è attivo
            if loan.get('return_date') is None:
                print("Prestito attivo (nessuna data di restituzione)")
                active_loans.append(loan)
                continue
                
            # Caso 2: Verifica se la data di restituzione è nel futuro
            try:
                return_date_str = loan.get('return_date')
                
                # Normalizza formato data
                if return_date_str.endswith('Z'):
                    return_date_str = return_date_str.replace('Z', '+00:00')
                elif '+' not in return_date_str and 'T' in return_date_str:
                    return_date_str = f"{return_date_str}+00:00"
                
                # Converti le stringhe in datetime
                import datetime
                return_date = datetime.datetime.fromisoformat(return_date_str)
                now = datetime.datetime.now(datetime.timezone.utc)
                
                print(f"Data restituzione: {return_date}, Ora attuale: {now}")
                print(f"È nel futuro? {return_date > now}")
                
                if return_date > now:
                    active_loans.append(loan)
                    print("Prestito attivo (data restituzione nel futuro)")
            except Exception as e:
                print(f"Errore parsing data: {e}")
                # In caso di problemi nel parsing della data, non includiamo il prestito
    
    print(f"Totale prestiti attivi trovati: {len(active_loans)}")
    return active_loans

def show_manage_users_page():
    """Pagina per la gestione degli utenti"""
    st.title("Gestione Utenti")
    
    # Aggiungiamo uno stato locale per tenere traccia dell'eliminazione
    if 'user_to_delete' not in st.session_state:
        st.session_state.user_to_delete = None
    if 'show_confirm_delete' not in st.session_state:
        st.session_state.show_confirm_delete = False
    
    # Tab per visualizzare o aggiungere utenti
    tab1, tab2 = st.tabs(["Lista Utenti", "Aggiungi Utente"])
    
    # Tab 1: Lista utenti esistenti
    with tab1:
        # Pulsante per aggiornare la lista
        if st.button("🔄 Aggiorna lista"):
            invalidate_caches()
            # Resetta anche lo stato di eliminazione
            st.session_state.user_to_delete = None
            st.session_state.show_confirm_delete = False
            st.rerun()
            
        users = fetch_users()
        if not users:
            st.info("Nessun utente registrato nel sistema.")
        else:
            # Mostra il numero totale di utenti
            st.write(f"Trovati {len(users)} utenti registrati:")
            
            # Visualizza ogni utente in una card
            for user in users:
                with st.container():
                    user_id = user['id']
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.subheader(user['name'])
                        st.write(f"📧 {user['email']}")
                    
                    with col2:
                        # Ottieni prestiti attivi
                        active_loans = get_active_loans_for_user(user_id)
                        
                        if active_loans:
                            num_loans = len(active_loans)
                            st.markdown(f"📚 **{num_loans} {('prestito attivo' if num_loans == 1 else 'prestiti attivi')}**")
                            
                            # Mostra dettagli del primo prestito attivo
                            if len(active_loans) > 0:
                                first_loan = active_loans[0]
                                from utils.api import fetch_book
                                book = fetch_book(first_loan.get('book_id'))
                                if book:
                                    with st.expander("Dettagli prestiti"):
                                        for loan in active_loans:
                                            book = fetch_book(loan.get('book_id'))
                                            if book:
                                                st.write(f"- **{book.get('title')}** di {book.get('author')}")
                                                loan_date = loan.get('loan_date', '').split('T')[0]
                                                return_date = loan.get('return_date', '').split('T')[0] if loan.get('return_date') else 'Non specificata'
                                                st.write(f"  Prestato il: {loan_date}, Restituzione: {return_date}")
                        else:
                            st.write("📚 Nessun prestito attivo")
                    
                    with col3:
                        # Se è in modalità conferma per questo utente, mostra i bottoni di conferma
                        if st.session_state.user_to_delete == user_id and st.session_state.show_confirm_delete:
                            st.warning(f"Sei sicuro di voler eliminare {user['name']}?")
                            
                            # Bottone "Sì"
                            if st.button("Sì", key=f"confirm_yes_{user_id}"):
                                try:
                                    # Invia la richiesta di eliminazione al backend
                                    response = requests.delete(f"{API_URL}/users/{user_id}")
                                    
                                    if response.status_code == 200:
                                        # Operazione riuscita
                                        st.success(f"Utente {user['name']} eliminato con successo!")
                                        # Resetta lo stato e aggiorna la cache
                                        st.session_state.user_to_delete = None
                                        st.session_state.show_confirm_delete = False
                                        invalidate_caches()
                                        st.rerun()
                                    else:
                                        # Gestisci errori
                                        try:
                                            error_detail = response.json().get("detail", "Errore sconosciuto")
                                            st.error(f"Errore nell'eliminazione: {error_detail}")
                                        except:
                                            st.error(f"Errore nell'eliminazione: Status code {response.status_code}")
                                except Exception as e:
                                    st.error(f"Errore di connessione: {str(e)}")
                            
                            # Bottone "No"
                            if st.button("No", key=f"confirm_no_{user_id}"):
                                # Resetta lo stato di eliminazione
                                st.session_state.user_to_delete = None
                                st.session_state.show_confirm_delete = False
                                st.rerun()
                        else:
                            # Mostra il bottone "Elimina" normalmente
                            if st.button("🗑️ Elimina", key=f"delete_{user_id}"):
                                # Verifica se l'utente ha prestiti attivi
                                active_loans = get_active_loans_for_user(user_id)
                                if active_loans:
                                    show_message_box(
                                        f"Impossibile eliminare {user['name']} perché ha dei prestiti attivi.",
                                        "error"
                                    )
                                else:
                                    # Imposta lo stato per mostrare la conferma
                                    st.session_state.user_to_delete = user_id
                                    st.session_state.show_confirm_delete = True
                                    st.rerun()
                    
                    st.markdown("---")
    
    # Tab 2: Aggiungi nuovo utente
    with tab2:
        st.subheader("Aggiungi un nuovo utente")
        
        # Form per aggiungere un nuovo utente
        with st.form("add_user_form"):
            name = st.text_input("Nome completo", placeholder="Es. Mario Rossi")
            email = st.text_input("Email", placeholder="Es. mario.rossi@email.com")
            
            # Bottone di invio
            submitted = st.form_submit_button("Aggiungi Utente")
            
            if submitted:
                if not name or not email:
                    st.error("Nome e email sono campi obbligatori.")
                else:
                    try:
                        # Prepara i dati dell'utente
                        user_data = {
                            "name": name,
                            "email": email
                        }
                        
                        # Gestione più robusta della risposta
                        with st.spinner("Creazione utente in corso..."):
                            # Invia la richiesta al backend
                            response = requests.post(f"{API_URL}/users/", json=user_data, timeout=10)
                            
                            if response.status_code == 200:
                                # Verifica che la risposta contenga dati JSON validi
                                try:
                                    user_created = response.json()
                                    
                                    # Pulisci la cache degli utenti
                                    invalidate_caches()
                                    
                                    # Mostra messaggio di successo
                                    st.success(f"Utente {name} aggiunto con successo!")
                                    
                                    # Mostra i dati dell'utente creato
                                    st.write(f"**ID:** {user_created['id']}")
                                    st.write(f"**Nome:** {user_created['name']}")
                                    st.write(f"**Email:** {user_created['email']}")
                                except ValueError:
                                    # Se la risposta non è JSON valido
                                    st.warning("Utente creato ma i dettagli non sono disponibili. Prova a ricaricare la pagina.")
                                    invalidate_caches()
                            else:
                                # Gestisci gli errori comuni
                                try:
                                    error_data = response.json()
                                    error_detail = error_data.get("detail", "Errore sconosciuto")
                                    if "already exists" in error_detail.lower():
                                        st.error(f"Un utente con questa email esiste già nel sistema.")
                                    else:
                                        st.error(f"Errore nella creazione dell'utente: {error_detail}")
                                except ValueError:
                                    # Se la risposta di errore non è JSON valido
                                    st.error(f"Errore nella creazione dell'utente. Status code: {response.status_code}")
                    except requests.exceptions.Timeout:
                        st.error("Timeout della richiesta. Il server potrebbe essere sovraccarico.")
                    except requests.exceptions.ConnectionError:
                        st.error("Impossibile connettersi al server. Verifica che il backend sia in esecuzione.")
                    except Exception as e:
                        st.error(f"Errore imprevisto: {str(e)}")