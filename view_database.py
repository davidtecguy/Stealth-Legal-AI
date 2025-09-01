#!/usr/bin/env python3
"""
Database Viewer for Stealth Legal AI
Simple script to view database structure and data
"""

import sqlite3
import json
from datetime import datetime

def view_database():
    """View the database structure and data"""
    
    # Connect to database
    conn = sqlite3.connect('stealth_legal.db')
    cursor = conn.cursor()
    
    print("🗄️  STEALTH LEGAL AI DATABASE VIEWER")
    print("=" * 60)
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print(f"📋 Tables found: {len(tables)}")
    for table in tables:
        print(f"   - {table[0]}")
    print()
    
    # For each table, show structure and data
    for table in tables:
        table_name = table[0]
        print(f"📊 TABLE: {table_name.upper()}")
        print("-" * 40)
        
        # Show table structure
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        print("📋 Structure:")
        for col in columns:
            pk = "🔑" if col[5] else "  "
            nullable = "NULL" if col[3] else "NOT NULL"
            default = f"DEFAULT {col[4]}" if col[4] else ""
            print(f"   {pk} {col[1]} ({col[2]}) {nullable} {default}")
        
        print()
        
        # Show table data
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        print(f"📄 Data ({len(rows)} records):")
        if rows:
            # Get column names
            column_names = [col[1] for col in columns]
            print(f"   Columns: {', '.join(column_names)}")
            print()
            
            for i, row in enumerate(rows, 1):
                print(f"   Record {i}:")
                for j, value in enumerate(row):
                    col_name = column_names[j]
                    # Truncate long content
                    if col_name == 'content' and value and len(str(value)) > 100:
                        display_value = str(value)[:100] + "..."
                    else:
                        display_value = str(value) if value is not None else "NULL"
                    print(f"     {col_name}: {display_value}")
                print()
        else:
            print("   No data found")
        
        print("=" * 60)
        print()
    
    conn.close()

def view_database_stats():
    """Show database statistics"""
    
    conn = sqlite3.connect('stealth_legal.db')
    cursor = conn.cursor()
    
    print("📊 DATABASE STATISTICS")
    print("=" * 40)
    
    # Get file size
    import os
    file_size = os.path.getsize('stealth_legal.db')
    print(f"📁 Database file size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    
    # Get table counts
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"📋 {table_name}: {count} records")
    
    # Get database info
    cursor.execute("PRAGMA database_list")
    db_info = cursor.fetchone()
    print(f"🗄️  Database: {db_info[2]}")
    
    conn.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        view_database_stats()
    else:
        view_database()
        print("\n💡 Tip: Run 'python3 view_database.py stats' for database statistics")
