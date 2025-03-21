# library-management-app

Library Management App

Un'applicazione completa per la gestione di biblioteche personali o condivise, con interfaccia web intuitiva, gestione prestiti, e integrazione con API di metadati per libri.

## Funzionalità principali

### Gestione completa dei libri:

- Aggiunta automatica tramite ISBN
- Recupero automatico di metadati (titolo, autore, copertina, ecc.)
- Upload manuale delle copertine
- Visualizzazione in griglia o dettaglio
- Modifica e cancellazione

### Sistema di prestiti:

- Registrazione prestiti con data di scadenza
- Monitoraggio prestiti attivi
- Gestione restituzioni

### Ricerca e filtri avanzati:

- Ricerca per titolo, autore, ISBN
- Filtri per stato (disponibile, in prestito)
- Navigazione rapida della collezione

### Gestione utenti:

- Registrazione e autenticazione
- Profili utente
- Permessi differenziati

### Esportazione dati:

- Export completo in formato CSV
- Backup delle copertine
- Generazione archivi ZIP

### Persistenza dei dati:
- Database SQLite su volume Docker

## Requisiti

- Docker e Docker Compose
- Accesso a internet (per recupero metadati)
- Opzionale: Account Backblaze B2 per backup remoto

## Deployment con Docker

### Setup di base

1. Clona il repository:
2. Crea il file `docker-compose.yml`:
3. Avvia l'applicazione:
4. Accedi all'applicazione: Apri il browser all'indirizzo [http://tuoip:8501](http://localhost:8501)

## Licenza
MIT License
© 2023 Tommaso Minuto

---

Progetto sviluppato con Python, FastAPI, SQLite, e Streamlit.