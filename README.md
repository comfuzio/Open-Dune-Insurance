# Open Dune Insurance 🏜️🪱

**Open Dune Insurance** is a standalone, open-source gear backup and recovery tool for **Dune: Awakening** dedicated servers. Built specifically to interface with the native PostgreSQL database provided by the Funcom Dune VM, this tool allows server admins to save player inventories and restore them after catastrophic events (like a Shai-Hulud attack).

To keep the cutthroat spirit of Arrakis alive, this tool features an optional **"Dune Pro"** mode that introduces a restorative **Spice Tax** and **Durability Penalty** when recovering lost gear.

## Features

* **Gear Snapshots:** Export full player inventory/gear BLOBs to a lightweight local `.json` backup file.
* **Seamless Restoration:** Inject saved gear back into the live database instantly.
* **Dune Pro Mode (Hardcore Recovery):** * **Spice Tax:** Deducts a configurable amount of Spice Melange from the player's database entry before allowing a restore.
    * **Durability Damage:** Automatically degrades the durability/health of all restored items by a defined percentage (e.g., 15%).
* **Topology Agnostic:** Can be run via native Linux CLI, inside a Docker container, or executed via `kubectl` into the DB pod.

---

## Prerequisites

* A running Dune: Awakening dedicated server (Funcom VM / Native environment).
* Access to the server's PostgreSQL database.
* **Python 3.8+**

## Installation

1. Clone the repository directly to your server host machine:
   ```bash
   git clone https://github.com/comfuzio/Open-Dune-Insurance.git
   cd Open-Dune-Insurance
   ```
   Install the required Python dependencies:

```Bash
pip install -r requirements.txt
```
Copy the example configuration file and input your database credentials:

```Bash
cp config.example.yaml config.yaml
nano config.yaml
```
Usage
Run the script from the command line, passing the desired action and the target player's exact character name.

1. Backup Player Gear
Takes a snapshot of the player's current database inventory and saves it to the backups/ directory.

```Bash
python3 dune_insurance.py --backup "Paul Atreides"
```
2. Standard Restore
Overwrites the player's current inventory with the saved .json snapshot. No penalties applied.

```Bash
python3 dune_insurance.py --restore "Paul Atreides"
```
3. Dune Pro Restore (Spice Tax & Durability Loss)
Applies a Spice Melange cost and a percentage-based durability drop to the gear before injecting it back into the database. (Note: If the player lacks the required Spice, the transaction is aborted).

```Bash
python3 dune_insurance.py --restore-pro "Paul Atreides"
```

Configuration (config.yaml)
Define your database connection parameters here so the script can reach the game's data.

```YAML
database:
  host: "127.0.0.1"      # Change if DB is on a different pod/container
  port: 5432
  user: "postgres"
  password: "your_db_password"
  name: "dune"

insurance_rules:
  spice_tax: 100         # Amount of Spice Melange required for a Pro Restore
  penalty_pct: 0.15      # Durability loss (15%) applied to gear during Pro Restore
```

License
This project is proudly licensed under the GNU AGPLv3.

We believe that tools extending server functionality should remain fully open. If you modify this tool, incorporate it into a web panel, or host it over a network, you must make your modified source code available to your users.

Long live the fighters.
