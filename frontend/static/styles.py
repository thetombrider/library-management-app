import streamlit as st

def load_css():
    """Carica gli stili CSS personalizzati"""
    st.markdown(
        """
        <style>
        /* Stile bottoni */
        .stButton>button {
            width: 100%;
            margin-bottom: 10px;
        }
        
        /* Stile per le schede libro nella griglia */
        .element-container {
            margin-bottom: 5px !important;
        }
        
        /* Riduci spazio tra paragrafi */
        p {
            margin-bottom: 0.3rem !important;
            margin-top: 0.3rem !important;
        }
        
        /* Rimuovi spazi tra righe */
        .row-widget {
            margin-bottom: 5px !important;
        }
        
        /* Stile per i titoli */
        h1 {
            color: #1E3A8A;
            margin-bottom: 0.5rem;
        }
        
        h2, h3 {
            color: #1E3A8A;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
        }
        
        /* Stile per i divisori */
        hr {
            margin-top: 0.5rem;
            margin-bottom: 0.5rem;
        }
        
        /* Stile per le box informative */
        .stAlert {
            padding: 10px !important;
            border-radius: 5px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )