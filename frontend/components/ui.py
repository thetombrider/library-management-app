import streamlit as st
from utils.api import get_book_cover_url

def render_book_cover(book, width=150):
    """Renderizza la copertina di un libro"""
    if book.get('has_cover', False):
        st.image(get_book_cover_url(book['id']), width=width)
    else:
        # Copertina placeholder
        st.markdown(
            f"""
            <div style="width: {width}px; height: {int(width * 1.5)}px; 
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

def show_message_box(message, type="info"):
    """Mostra una box con messaggio stilizzata"""
    if type == "success":
        color_bg = "#e8f5e9"
        color_border = "#4caf50"
        color_text = "#2e7d32"
        icon = "✓"
    elif type == "warning":
        color_bg = "#fff8e1"
        color_border = "#ffc107"
        color_text = "#ff8f00"
        icon = "⚠️"
    elif type == "error":
        color_bg = "#ffebee"
        color_border = "#f44336"
        color_text = "#c62828"
        icon = "❌"
    else:  # info
        color_bg = "#e3f2fd"
        color_border = "#2196f3"
        color_text = "#0d47a1"
        icon = "ℹ️"
        
    st.markdown(
        f"""
        <div style="background-color: {color_bg}; 
                   padding: 10px; 
                   border-radius: 5px; 
                   border-left: 4px solid {color_border};">
            <span style="color: {color_text};">{icon} {message}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_metadata_list(metadata_items):
    """Renderizza una lista di metadati in formato chiave-valore"""
    for label, value in metadata_items:
        if value:
            st.markdown(f"**{label}:** {value}")