import streamlit as st

def load_scripts():
    """Carica gli script JavaScript personalizzati"""
    st.components.v1.html(
        """
        <script>
        // Script per intercettare gli eventi
        window.addEventListener('message', function(e) {
            if (e.data.type === 'book_click') {
                // Quando l'utente clicca su una copertina
                document.querySelector('button[key="btn_' + e.data.bookId + '"]').click();
            } else if (e.data.type === 'isbn_scanned') {
                // Quando viene scansionato un ISBN
                console.log('ISBN scansionato:', e.data.isbn);
                
                // Aggiungi parametro ISBN all'URL e ricarica
                const currentUrl = new URL(window.location.href);
                currentUrl.searchParams.set('isbn', e.data.isbn);
                window.location.href = currentUrl.toString();
            }
        });
        
        // Funzione per il ridimensionamento dinamico
        function adjustLayout() {
            // Implementazione futura per migliorare il layout responsive
        }
        
        // Esegui al caricamento e al ridimensionamento
        window.addEventListener('load', adjustLayout);
        window.addEventListener('resize', adjustLayout);
        </script>
        """,
        height=0
    )