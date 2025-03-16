import streamlit as st
from utils.api import fetch_books, invalidate_caches, API_URL, get_auth_header
from utils.state import set_state
import requests
import pandas as pd

def show_bulk_edit_page():
    """Pagina per la modifica in batch dei metadati dei libri"""
    st.title("Modifica in batch dei libri")
    
    # Recupera tutti i libri
    books = fetch_books()
    
    if not books:
        st.warning("Non ci sono libri da modificare.")
        return
    
    # Crea un dataframe per visualizzare e selezionare i libri
    df = pd.DataFrame([
        {
            "id": book["id"],
            "Selezionato": False,
            "Titolo": book["title"],
            "Autore": book["author"],
            "ISBN": book.get("isbn", ""),
            "Editore": book.get("publisher", ""),
            "Anno": book.get("publish_year", "")
        } for book in books
    ])
    
    # Aggiungi una colonna di checkbox per la selezione
    df = st.data_editor(
        df,
        column_config={
            "id": st.column_config.Column("ID", disabled=True, width="small"),
            "Selezionato": st.column_config.CheckboxColumn("Seleziona", width="small"),
            "Titolo": st.column_config.TextColumn("Titolo", disabled=True),
            "Autore": st.column_config.TextColumn("Autore", disabled=True),
            "ISBN": st.column_config.TextColumn("ISBN", disabled=True),
            "Editore": st.column_config.TextColumn("Editore", disabled=True),
            "Anno": st.column_config.NumberColumn("Anno", disabled=True),
        },
        hide_index=True,
        key="book_table",
    )
    
    # Filtra i libri selezionati
    selected_books = df[df["Selezionato"] == True]
    selected_count = len(selected_books)
    
    if selected_count == 0:
        st.info("Seleziona i libri da modificare nella tabella sopra.")
        # Bottone per tornare alla griglia con chiave unica
        if st.button("Torna alla libreria", key="return_to_grid_empty"):
            set_state("grid")
            st.rerun()
    else:
        st.success(f"{selected_count} libri selezionati per la modifica.")
        
        # Crea una struttura a tab per modificare o eliminare
        tab1, tab2 = st.tabs(["📝 Modifica metadati", "🗑️ Elimina libri"])
        
        # Tab 1: Modifica metadati (codice esistente)
        with tab1:
            st.subheader("Modifica in batch dei libri selezionati")
            
            with st.form("bulk_edit_form"):
                # Campo Editore
                edit_publisher = st.checkbox("Modifica Editore")
                new_publisher = ""
                if edit_publisher:
                    new_publisher = st.text_input("Nuovo editore", key="new_publisher")
                
                # Campo Autore
                edit_author = st.checkbox("Modifica Autore")
                new_author = ""
                if edit_author:
                    new_author = st.text_input("Nuovo autore", key="new_author")
                
                # Campo Anno
                edit_year = st.checkbox("Modifica Anno")
                new_year = 0
                if edit_year:
                    new_year = st.number_input("Nuovo anno", min_value=0, max_value=2100, step=1, key="new_year")
                
                # Bottoni
                col1, col2 = st.columns(2)
                with col1:
                    cancel = st.form_submit_button("Annulla")
                with col2:
                    submit = st.form_submit_button("Applica modifiche")
                
                if cancel:
                    set_state("grid")
                    st.rerun()
                
                if submit:
                    # Prepara i dati da inviare
                    updated_data = {}
                    if edit_publisher and new_publisher:
                        updated_data["publisher"] = new_publisher
                    if edit_author and new_author:
                        updated_data["author"] = new_author
                    if edit_year and new_year > 0:
                        updated_data["publish_year"] = new_year
                    
                    if updated_data:
                        # Ottieni la lista di ID dei libri selezionati
                        book_ids = selected_books["id"].tolist()
                        
                        # Dati da inviare
                        payload = {
                            "book_ids": book_ids,
                            "updates": updated_data
                        }
                        
                        try:
                            headers = get_auth_header()
                            
                            with st.spinner("Aggiornamento in corso..."):
                                response = requests.post(
                                    f"{API_URL}/books/bulk-update",
                                    json=payload,
                                    headers=headers
                                )
                                
                                if response.status_code == 200:
                                    result = response.json()
                                    st.success(f"Aggiornamento completato: {result['updated']} libri aggiornati")
                                    
                                    # Pulisci le cache
                                    invalidate_caches()
                                    
                                    # Torna alla griglia dopo qualche secondo
                                    import time
                                    time.sleep(2)
                                    set_state("grid")
                                    st.rerun()
                                else:
                                    st.error(f"Errore durante l'aggiornamento: {response.json().get('detail', 'Errore sconosciuto')}")
                        except Exception as e:
                            st.error(f"Errore di connessione: {str(e)}")
        
        # Tab 2: Elimina libri (nuova funzionalità)
        with tab2:
            st.subheader("Elimina libri selezionati")
            
            st.warning(f"⚠️ Stai per eliminare {selected_count} libri. Questa operazione è irreversibile.")
            
            # Visualizza i titoli dei libri selezionati
            if selected_count > 0:
                st.markdown("### Libri selezionati per l'eliminazione:")
                for i, book in enumerate(selected_books.itertuples(), 1):
                    st.markdown(f"{i}. **{book.Titolo}** di {book.Autore}")
            
            # Form per conferma eliminazione
            with st.form("bulk_delete_form"):
                confirm = st.checkbox("Confermo di voler eliminare i libri selezionati")
                
                col1, col2 = st.columns(2)
                with col1:
                    cancel_delete = st.form_submit_button("Annulla")
                with col2:
                    submit_delete = st.form_submit_button("Elimina definitivamente")
                
                if cancel_delete:
                    set_state("grid")
                    st.rerun()
                
                if submit_delete:
                    if not confirm:
                        st.error("Devi confermare l'eliminazione selezionando la casella.")
                    else:
                        # Ottieni la lista di ID dei libri selezionati
                        book_ids = selected_books["id"].tolist()
                        
                        try:
                            headers = get_auth_header()
                            
                            with st.spinner("Eliminazione in corso..."):
                                response = requests.post(
                                    f"{API_URL}/books/bulk-delete",
                                    json={"book_ids": book_ids},
                                    headers=headers
                                )
                                
                                if response.status_code == 200:
                                    result = response.json()
                                    
                                    # Salva il risultato nello stato della sessione per mostrarlo dopo il form
                                    st.session_state.bulk_delete_result = result
                                    # Aggiungi un flag per indicare che l'operazione è completata
                                    st.session_state.bulk_delete_completed = True
                                    
                                    # Pulisci le cache
                                    invalidate_caches()
                                    
                                    # Rerun per uscire dal form e mostrare il risultato
                                    st.rerun()
                                else:
                                    st.error(f"Errore durante l'eliminazione: {response.json().get('detail', 'Errore sconosciuto')}")
                        except Exception as e:
                            st.error(f"Errore di connessione: {str(e)}")

    # Gestione risultato eliminazione dopo il form
    if 'bulk_delete_completed' in st.session_state and st.session_state.bulk_delete_completed:
        result = st.session_state.bulk_delete_result
        
        # Crea un riepilogo più dettagliato
        with st.container():
            st.success(f"✅ Eliminazione completata: {result['deleted']} libri eliminati")
            
            # Aggiungi informazioni aggiuntive se ci sono stati problemi
            if result.get('loaned', 0) > 0:
                st.warning(f"⚠️ {result['loaned']} libri non sono stati eliminati perché attualmente in prestito")
                
            if result.get('not_owned', 0) > 0:
                st.warning(f"⚠️ {result['not_owned']} libri non sono stati eliminati perché non di tua proprietà")
                
            if result.get('failed', 0) > 0:
                st.error(f"❌ {result['failed']} libri non sono stati eliminati a causa di errori")
