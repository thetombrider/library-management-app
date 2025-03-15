# Piano di Aggiornamento per la Gestione Utenti

## Obiettivi
- Implementare login e logout con password
- Associare automaticamente libri aggiunti all'utente loggato
- Filtrare i libri visualizzati in base all'utente loggato

## Piano di Lavoro

### Fase 1: Modifica del Backend

#### 1.1 Aggiornamento del Modello Utente
Modificare `user.py` per includere:
- Campo password (hash)
- Campo role (admin/user)
- Campo last_login

#### 1.2 Aggiornamento Schema Utente
Modificare `user.py`:
- Aggiungere schema per autenticazione
- Aggiungere campo password agli schemi appropriati
- Aggiungere schema per risposta login

#### 1.3 Implementazione Sistema di Autenticazione
Creare `backend/security.py`:
- Funzioni per hashing password
- Funzioni per verifica password
- Generazione e verifica token JWT

#### 1.4 Aggiungere Router per Autenticazione
Creare `backend/routers/auth.py`:
- Endpoint login
- Endpoint logout
- Endpoint verifica token

#### 1.5 Modificare CRUD Utenti
Aggiornare `user.py`:
- Implementare metodo per verificare credenziali
- Aggiungere gestione password durante creazione/modifica utenti
- Implementare aggiornamento ultimo accesso

#### 1.6 Middleware di Autorizzazione
Creare `backend/middleware/auth.py`:
- Verifica token in richieste
- Estrazione informazioni utente
- Applicazione permessi

#### 1.7 Modificare Router dei Libri
Aggiornare `books.py`:
- Aggiungere filtro per proprietario/prestiti
- Aggiungere dipendenza per autenticazione
- Implementare permessi basati sull'utente

### Fase 2: Modifica del Frontend

#### 2.1 Componenti di Autenticazione
Creare `frontend/views/login.py`:
- Form di login
- Gestione errori di autenticazione
- Redirezione post-login

Creare `frontend/views/register.py`:
- Form di registrazione
- Verifica password
- Validazione email

#### 2.2 Gestione Stato di Autenticazione
Modificare `state.py`:
- Aggiungere state per utente loggato
- Memorizzare token JWT
- Gestire scadenza token

#### 2.3 Servizio API per Autenticazione
Modificare `api.py`:
- Aggiungere funzioni per login/logout
- Includere token nelle chiamate API
- Gestire refresh token

#### 2.4 Aggiornare Barra Laterale
Modificare `app.py`:
- Aggiungere sezione login/logout
- Mostrare nome utente loggato
- Mostrare opzioni di admin se applicabile

#### 2.5 Aggiornare Aggiunta Libri
Modificare `add_book.py`:
- Impostare automaticamente owner_id
- Rimuovere selezione manuale proprietario

#### 2.6 Aggiornare Vista Griglia Libri
Modificare `book_grid.py`:
- Filtrare libri per utente loggato
- Aggiungere indicatori per libri in prestito

#### 2.7 Aggiornare Vista Dettaglio Libro
Modificare `book_detail.py`:
- Mostrare informazioni sul proprietario
- Gestire permessi di modifica

### Fase 3: Implementazione Database e Migrazione

#### 3.1 Aggiornare Schema DB
- Creare script di migrazione per nuovi campi utente
- Implementare hash password per utenti esistenti
- Aggiungere utente admin di default

#### 3.2 Test e Debug
- Testare sistema login/logout
- Verificare filtro libri
- Controllare gestione permessi

### Fase 4: Documentazione e Deployment

#### 4.1 Aggiornare Documentazione
- Aggiornare README con informazioni sul login
- Documentare funzionalità di permessi
- Creare guida per utenti

#### 4.2 Deployment
- Aggiornare `requirements.txt` con nuove dipendenze
- Implementare procedura di backup DB
- Eseguire deployment aggiornato

## Tempistiche Stimate
- **Fase 1:** 3-4 giorni
- **Fase 2:** 3-4 giorni
- **Fase 3:** 1-2 giorni
- **Fase 4:** 1 giorno

## Dipendenze Aggiuntive
- `passlib` - Per hashing password
- `python-jose` - Per JWT
- `python-multipart` - Per gestione form data

## Inizio Implementazione
Inizieremo con la Fase 1.1, modificando il modello utente e aggiungendo il supporto per le password.