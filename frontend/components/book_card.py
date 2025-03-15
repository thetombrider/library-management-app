import streamlit as st
from utils.api import get_book_cover_url
from utils.state import set_state

def render_book_card(book, show_button=True, additional_info=None):
    """Renderizza una card di libro"""
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
                
        # Titolo e autore sotto la copertina con gestione valori null
        title = book.get('title') or 'Titolo mancante'
        author = book.get('author') or 'Autore sconosciuto'
        
        st.markdown(f"**{title[:25]}**")
        st.markdown(f"{author[:25]}")
        
        # Informazioni aggiuntive (es. proprietario per i libri presi in prestito)
        if additional_info:
            st.markdown(f"*{additional_info}*")
        
        # Bottone per vedere i dettagli
        if show_button and st.button("Dettagli", key=f"btn_{book.get('id')}"):
            set_state('detail', selected_book=book.get('id'))
            st.rerun()