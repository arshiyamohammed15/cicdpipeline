"""
ZEROUI Database Access Tool
Following Rule 5: Keep Good Records + Keep Good Logs
"""

import sqlite3
import os
import json
from datetime import datetime

class ZEROUIDatabaseAccess:
    def __init__(self):
        self.db_path = os.path.expanduser('~/.zeroui/config/extension_config.db')
        
    def connect(self):
        """Connect to the database"""
        if not os.path.exists(self.db_path):
            print(f"Database not found at: {self.db_path}")
            return None
        return sqlite3.connect(self.db_path)
    
    def show_tables(self):
        """Show all tables in the database"""
        conn = self.connect()
        if not conn:
            return
            
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("=== DATABASE TABLES ===")
        for table in tables:
            print(f"[TABLE] {table[0]}")
        conn.close()
    
    def show_configs(self, table_name=None):
        """Show configuration data"""
        conn = self.connect()
        if not conn:
            return
            
        cursor = conn.cursor()
        
        if table_name:
            tables = [table_name]
        else:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_config'")
            tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            print(f"\n=== {table.upper()} ===")
            cursor.execute(f"SELECT key, value, created_at, updated_at FROM {table} ORDER BY key")
            configs = cursor.fetchall()
            
            for config in configs:
                print(f"[CONFIG] {config[0]}: {config[1]}")
                print(f"   Created: {config[2]}, Updated: {config[3]}")
        
        conn.close()
    
    def show_change_log(self, limit=20):
        """Show configuration change history"""
        conn = self.connect()
        if not conn:
            return
            
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name, key_name, old_value, new_value, change_type, timestamp, reason 
            FROM config_change_log 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        
        changes = cursor.fetchall()
        
        print(f"\n=== CONFIGURATION CHANGE LOG (Last {limit}) ===")
        for change in changes:
            table, key, old_val, new_val, change_type, timestamp, reason = change
            print(f"[CHANGE] {timestamp} | {table}.{key}")
            print(f"   Type: {change_type}")
            if old_val:
                print(f"   Old: {old_val}")
            print(f"   New: {new_val}")
            if reason:
                print(f"   Reason: {reason}")
            print()
        
        conn.close()
    
    def show_backups(self):
        """Show available backups"""
        conn = self.connect()
        if not conn:
            return
            
        cursor = conn.cursor()
        cursor.execute("SELECT backup_name, created_at, description FROM config_backup ORDER BY created_at DESC")
        backups = cursor.fetchall()
        
        print("\n=== AVAILABLE BACKUPS ===")
        if not backups:
            print("No backups found")
        else:
            for backup in backups:
                print(f"[BACKUP] {backup[0]} (Created: {backup[1]})")
                if backup[2]:
                    print(f"   Description: {backup[2]}")
        
        conn.close()
    
    def export_config(self, table_name, output_file=None):
        """Export configuration to JSON file"""
        conn = self.connect()
        if not conn:
            return
            
        cursor = conn.cursor()
        cursor.execute(f"SELECT key, value FROM {table_name}")
        configs = cursor.fetchall()
        
        config_dict = {key: value for key, value in configs}
        
        if not output_file:
            output_file = f"{table_name}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_file, 'w') as f:
            json.dump(config_dict, f, indent=2)
        
        print(f"[SUCCESS] Configuration exported to: {output_file}")
        conn.close()
    
    def search_config(self, search_term):
        """Search for configuration keys or values"""
        conn = self.connect()
        if not conn:
            return
            
        cursor = conn.cursor()
        
        # Search in all config tables
        config_tables = ['extension_config', 'typescript_config', 'build_config', 'runtime_config']
        
        print(f"\n=== SEARCH RESULTS for '{search_term}' ===")
        found = False
        
        for table in config_tables:
            cursor.execute(f"SELECT key, value FROM {table} WHERE key LIKE ? OR value LIKE ?", 
                          (f'%{search_term}%', f'%{search_term}%'))
            results = cursor.fetchall()
            
            if results:
                print(f"\n[TABLE] {table}:")
                for key, value in results:
                    print(f"   {key}: {value}")
                    found = True
        
        if not found:
            print("No matches found")
        
        conn.close()
    
    def interactive_mode(self):
        """Interactive database browser"""
        while True:
            print("\n" + "="*50)
            print("ZEROUI DATABASE ACCESS TOOL")
            print("="*50)
            print("1. Show all tables")
            print("2. Show all configurations")
            print("3. Show specific table")
            print("4. Show change log")
            print("5. Show backups")
            print("6. Search configurations")
            print("7. Export configuration")
            print("8. Exit")
            
            choice = input("\nEnter your choice (1-8): ").strip()
            
            if choice == '1':
                self.show_tables()
            elif choice == '2':
                self.show_configs()
            elif choice == '3':
                table = input("Enter table name: ").strip()
                self.show_configs(table)
            elif choice == '4':
                limit = input("Number of recent changes to show (default 20): ").strip()
                limit = int(limit) if limit.isdigit() else 20
                self.show_change_log(limit)
            elif choice == '5':
                self.show_backups()
            elif choice == '6':
                term = input("Enter search term: ").strip()
                self.search_config(term)
            elif choice == '7':
                table = input("Enter table name to export: ").strip()
                self.export_config(table)
            elif choice == '8':
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")

def main():
    """Main function"""
    db_access = ZEROUIDatabaseAccess()
    
    if len(os.sys.argv) > 1:
        command = os.sys.argv[1].lower()
        
        if command == 'tables':
            db_access.show_tables()
        elif command == 'configs':
            db_access.show_configs()
        elif command == 'changes':
            limit = int(os.sys.argv[2]) if len(os.sys.argv) > 2 else 20
            db_access.show_change_log(limit)
        elif command == 'backups':
            db_access.show_backups()
        elif command == 'search':
            if len(os.sys.argv) > 2:
                db_access.search_config(os.sys.argv[2])
            else:
                print("Usage: python access_database.py search <term>")
        elif command == 'export':
            if len(os.sys.argv) > 2:
                db_access.export_config(os.sys.argv[2])
            else:
                print("Usage: python access_database.py export <table_name>")
        else:
            print("Available commands: tables, configs, changes, backups, search, export")
    else:
        # Interactive mode
        db_access.interactive_mode()

if __name__ == "__main__":
    main()
