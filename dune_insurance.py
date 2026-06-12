#!/usr/bin/env python3
"""
Dune: Awakening - Sandworm Insurance & Gear Recovery Tool
License: GNU AGPLv3 (Copyleft)
"""

import os
import sys
import json
import yaml
import psycopg2
from datetime import datetime

CONFIG_PATH = os.path.expanduser("~/.dune-admin/config.yaml")
BACKUP_DIR = "./dune_gear_backups"

def load_db_config():
    """Reads the database credentials from dune-admin config."""
    if not os.path.exists(CONFIG_PATH):
        print(f"[-] Error: dune-admin config not found at {CONFIG_PATH}")
        sys.exit(1)
    
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
    
    # Adapt this mapping based on exact fields in dune-admin's config.yaml
    db_opts = config.get('database', {})
    return {
        "dbname": db_opts.get('name', 'dune'),
        "user": db_opts.get('user', 'postgres'),
        "password": db_opts.get('password', ''),
        "host": db_opts.get('host', 'localhost'),
        "port": db_opts.get('port', 5432)
    }

def get_db_connection():
    creds = load_db_config()
    return psycopg2.connect(**creds)

def backup_player_gear(player_name):
    """Fetches inventory/equipment blocks from DB and saves to a local JSON."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # NOTE: Exact table/column names depend on Dune's internal DB schema.
        # Typically maps a character name to their inventory BLOB/JSON data.
        query = "SELECT character_id, inventory_data, currency_data FROM characters WHERE character_name = %s;"
        cursor.execute(query, (player_name,))
        result = cursor.fetchone()
        
        if not result:
            print(f"[-] Player '{player_name}' not found in database.")
            return False
            
        char_id, inventory, currency = result
        
        backup_data = {
            "player_name": player_name,
            "character_id": char_id,
            "timestamp": datetime.utcnow().isoformat(),
            "inventory_snapshot": inventory # JSON or string block
        }
        
        filename = f"{BACKUP_DIR}/{player_name}_gear_bak.json"
        with open(filename, 'w') as f:
            json.dump(backup_data, f, indent=4)
            
        print(f"[+] Successfully saved gear backup for {player_name} to {filename}")
        return True

    except Exception as e:
        print(f"[-] DB Error during backup: {e}")
    finally:
        cursor.close()
        conn.close()

def restore_player_gear(player_name, apply_pro_rules=False, penalty_pct=0.15, spice_tax=50):
    """Restores items, applying a durability penalty and charging Spice if requested."""
    filename = f"{BACKUP_DIR}/{player_name}_gear_bak.json"
    if not os.path.exists(filename):
        print(f"[-] No backup file found for {player_name}")
        return False
        
    with open(filename, 'r') as f:
        backup = json.load(f)
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # --- ONLINE SAFETY CHECK ---
        # Checks if the player is currently in-game to prevent RAM desync overwrites.
        # Note: 'is_online' might be named differently depending on Funcom's exact schema updates.
        cursor.execute("SELECT is_online FROM characters WHERE character_name = %s;", (player_name,))
        status_result = cursor.fetchone()
        
        if status_result and status_result[0] == True:
            print(f"[-] Restore Aborted: '{player_name}' is currently ONLINE.")
            print("[!] The player must log out to the main menu before you can safely restore their gear.")
            return False

        # --- DUNE PRO RULES ENGINE ---
        if apply_pro_rules:
            # 1. Check & Deduct Spice Melange Tax
            cursor.execute("SELECT spice_melange FROM characters WHERE character_name = %s;", (player_name,))
            current_spice = cursor.fetchone()[0]
            
            if current_spice < spice_tax:
                print(f"[-] Restore Aborted: {player_name} only has {current_spice} Spice. Costs {spice_tax}.")
                return False
                
            # Deduct the spice tax
            cursor.execute("UPDATE characters SET spice_melange = spice_melange - %s WHERE character_name = %s;", (spice_tax, player_name))
            print(f"[❖] Taxed {spice_tax} Spice Melange from {player_name}.")

            # 2. Apply Durability Penalty to the backup data
            inventory = backup["inventory_snapshot"]
            
            if isinstance(inventory, list):
                for item in inventory:
                    if "durability" in item:
                        item["durability"] = max(0, int(item["durability"] * (1.0 - penalty_pct)))
                    if "health" in item:
                        item["health"] = max(0, int(item["health"] * (1.0 - penalty_pct)))
            
            backup["inventory_snapshot"] = inventory
            print(f"[❖] Applied {int(penalty_pct*100)}% durability damage to items.")
        
        # --- INJECT BACK INTO THE DATABASE ---
        update_query = "UPDATE characters SET inventory_data = %s WHERE character_name = %s;"
        cursor.execute(update_query, (json.dumps(backup["inventory_snapshot"]), player_name))
        
        conn.commit()
        print(f"[+] Successfully restored gear for {player_name}! They can now log back in.")
        return True

    except Exception as e:
        conn.rollback()
        print(f"[-] DB Error during restore: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # Quick CLI parsing for testing
    if len(sys.argv) < 3:
        print("Usage: python dune_insurance.py [--backup | --restore | --restore-pro] [PlayerName]")
        sys.exit(1)
        
    action = sys.argv[1]
    player = sys.argv[2]
    
    if action == "--backup":
        backup_player_gear(player)
    elif action == "--restore":
        restore_player_gear(player, apply_pro_rules=False)
    elif action == "--restore-pro":
        # Pass True to activate durability loss and spice charging
        restore_player_gear(player, apply_pro_rules=True, penalty_pct=0.15, spice_tax=100)
