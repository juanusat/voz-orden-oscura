#!/usr/bin/env python3
import sqlite3
import os

db_path = "data.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Checking transcriptions table...")
    cursor.execute("PRAGMA table_info(transcriptions)")
    columns = cursor.fetchall()
    
    print("Transcriptions table columns:")
    for col in columns:
        print(f"  {col[1]} - {col[2]}")
    
    print(f"\nTotal columns: {len(columns)}")
    
    speaker_segments_found = any(col[1] == 'speaker_segments' for col in columns)
    print(f"speaker_segments column found: {speaker_segments_found}")
    
    conn.close()
else:
    print("Database file not found!")