#!/usr/bin/env python3
import os
import sys
import sqlite3
from pathlib import Path

def reset_database():
    here = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(here)
    project_root = os.path.dirname(backend_dir)
    
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    try:
        from backend.config import Config
        from backend import create_app, db
        
        config = Config()
        db_path = config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
        
        if db_path.startswith('sqlite:///'):
            db_path = db_path[10:]
        
        db_file = Path(db_path)
        
        print(f"Database path: {db_file.absolute()}")
        
        if db_file.exists():
            print("Removing existing database...")
            db_file.unlink()
            print("Database removed successfully.")
        else:
            print("Database file does not exist.")
        
        print("Creating new database with updated schema...")
        app = create_app()
        
        with app.app_context():
            db.create_all()
            print("Database created successfully with new schema.")
            
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA table_info(transcriptions)")
            columns = cursor.fetchall()
            
            print("\nTranscriptions table columns:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            cursor.execute("PRAGMA table_info(uploads)")
            uploads_columns = cursor.fetchall()
            
            print("\nUploads table columns:")
            for col in uploads_columns:
                print(f"  {col[1]} ({col[2]})")
            
            conn.close()
            
        print("\nDatabase reset completed successfully!")
        
    except Exception as e:
        print(f"Error resetting database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    reset_database()