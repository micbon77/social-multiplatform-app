#!/usr/bin/env python3
"""
Script per inizializzare il database dell'applicazione Social Multiplatform Publisher.
Questo script crea tutte le tabelle necessarie nel database.
"""

import sys
import os
from pathlib import Path

# Aggiungi la directory app al path Python
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from db.database import create_tables, engine
from models.models import Base

def init_database():
    """Inizializza il database creando tutte le tabelle."""
    try:
        print("🔄 Inizializzazione del database in corso...")
        
        # Crea tutte le tabelle
        create_tables()
        
        print("✅ Database inizializzato con successo!")
        print(f"📍 Database location: {engine.url}")
        
        # Mostra le tabelle create
        print("\n📋 Tabelle create:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")
            
    except Exception as e:
        print(f"❌ Errore durante l'inizializzazione del database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_database()

