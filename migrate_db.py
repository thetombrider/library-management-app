import sqlite3
import os
import shutil
from datetime import datetime
from backend.security import get_password_hash

def backup_db():
    """Crea un backup del database attuale."""
    if os.path.exists("books.db"):
        backup_dir = "old_dbs"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{backup_dir}/books_db_{timestamp}.db"
        
        shutil.copy2("books.db", backup_path)
        print(f"Backup creato: {backup_path}")
        return True
    
    return False

def migrate_users():
    """Aggiorna la tabella degli utenti con i nuovi campi."""
    conn = sqlite3.connect("books.db")
    cursor = conn.cursor()
    
    # Verifica se i nuovi campi esistono già
    cursor.execute("PRAGMA table_info(users)")
    columns = [info[1] for info in cursor.fetchall()]
    
    # Modifica la tabella se necessario
    if "hashed_password" not in columns:
        print("Aggiunta colonna 'hashed_password'...")
        cursor.execute("ALTER TABLE users ADD COLUMN hashed_password TEXT")
    
    if "role" not in columns:
        print("Aggiunta colonna 'role'...")
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
    
    if "last_login" not in columns:
        print("Aggiunta colonna 'last_login'...")
        cursor.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP")
    
    if "created_at" not in columns:
        print("Aggiunta colonna 'created_at'...")
        cursor.execute("ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    
    if "is_active" not in columns:
        print("Aggiunta colonna 'is_active'...")
        cursor.execute("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1")
    
    # Imposta password temporanea per gli utenti esistenti
    temp_password = "biblioteca2023"
    hashed_temp_password = get_password_hash(temp_password)
    
    cursor.execute("UPDATE users SET hashed_password = ?, role = 'user', is_active = 1 WHERE hashed_password IS NULL", (hashed_temp_password,))
    
    conn.commit()
    conn.close()

def run_migration():
    """Esegue tutte le migrazioni necessarie."""
    print("Inizio migrazione database...")
    
    # Crea backup
    if backup_db():
        print("Backup database creato con successo.")
    else:
        print("Nessun database trovato. Verrà creato uno nuovo.")
    
    # Migrazione tabella utenti
    migrate_users()
    
    print("Migrazione completata con successo!")

if __name__ == "__main__":
    run_migration()
    
    # Creazione utente admin
    print("\nCreazione utente amministratore...")
    import create_admin
    create_admin.create_admin_user()