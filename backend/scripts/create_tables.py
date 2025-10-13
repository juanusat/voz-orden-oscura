#!/usr/bin/env python3
import os
import sys
from pathlib import Path

def create_tables_directly():
    here = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(here)
    project_root = os.path.dirname(backend_dir)
    
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    try:
        import backend
        from backend import create_app, db
        from backend.models import Upload, Transcription
        
        db_path = "data.db"
        
        if os.path.exists(db_path):
            print("Removing existing database...")
            os.remove(db_path)
            print("Database removed.")
        
        print("Creating Flask app...")
        app = create_app()
        
        print("Creating tables...")
        with app.app_context():
            # Drop all tables first (in case any exist)
            db.drop_all()
            
            # Create all tables
            db.create_all()
            
            print("Tables created successfully!")
            
            # Verify the tables were created
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Tables created: {tables}")
            
            # Check transcriptions table columns
            if 'transcriptions' in tables:
                columns = inspector.get_columns('transcriptions')
                print("\nTranscriptions table columns:")
                for col in columns:
                    print(f"  {col['name']} - {col['type']}")
                
                speaker_segments_found = any(col['name'] == 'speaker_segments' for col in columns)
                print(f"\nspeaker_segments column present: {speaker_segments_found}")
            
            # Check uploads table columns
            if 'uploads' in tables:
                columns = inspector.get_columns('uploads')
                print("\nUploads table columns:")
                for col in columns:
                    print(f"  {col['name']} - {col['type']}")
        
        print("\nDatabase setup completed successfully!")
        
    except Exception as e:
        print(f"Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    create_tables_directly()