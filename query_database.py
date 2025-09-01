#!/usr/bin/env python3
"""
Database Query Tool for Stealth Legal AI
Run custom SQL queries on the database
"""

import sqlite3
import sys

def run_query(query):
    """Run a SQL query and display results"""
    
    conn = sqlite3.connect('stealth_legal.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute(query)
        
        # Check if it's a SELECT query
        if query.strip().upper().startswith('SELECT'):
            rows = cursor.fetchall()
            
            if rows:
                # Get column names
                column_names = [description[0] for description in cursor.description]
                
                print(f"🔍 Query: {query}")
                print(f"📊 Results: {len(rows)} rows")
                print("-" * 80)
                
                # Print column headers
                print(" | ".join(column_names))
                print("-" * 80)
                
                # Print data
                for row in rows:
                    formatted_row = []
                    for value in row:
                        if value is None:
                            formatted_row.append("NULL")
                        elif isinstance(value, str) and len(value) > 50:
                            formatted_row.append(f"{value[:50]}...")
                        else:
                            formatted_row.append(str(value))
                    print(" | ".join(formatted_row))
            else:
                print("📭 No results found")
        else:
            # For non-SELECT queries (INSERT, UPDATE, DELETE, etc.)
            conn.commit()
            print(f"✅ Query executed successfully: {query}")
            print(f"📊 Rows affected: {cursor.rowcount}")
            
    except sqlite3.Error as e:
        print(f"❌ SQL Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

def show_common_queries():
    """Show some useful queries"""
    
    queries = {
        "1": "SELECT * FROM documents",
        "2": "SELECT id, title, LENGTH(content) as content_length, created_at FROM documents",
        "3": "SELECT COUNT(*) as total_documents FROM documents",
        "4": "SELECT id, title, SUBSTR(content, 1, 100) as content_preview FROM documents",
        "5": "SELECT * FROM documents WHERE title LIKE '%test%'",
        "6": "SELECT * FROM documents ORDER BY created_at DESC",
        "7": "SELECT id, title, etag, created_at, updated_at FROM documents"
    }
    
    print("🔍 COMMON QUERIES:")
    print("=" * 50)
    for key, query in queries.items():
        print(f"{key}. {query}")
    print()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run the provided query
        query = " ".join(sys.argv[1:])
        run_query(query)
    else:
        # Show common queries
        show_common_queries()
        print("💡 Usage: python3 query_database.py 'SELECT * FROM documents'")
        print("💡 Or run one of the common queries above")
