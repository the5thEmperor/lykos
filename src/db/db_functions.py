import sqlite3
from typing import Tuple


def check_table(cursor: sqlite3.Cursor):
    result = cursor.execute("SELECT count(name) FROM sqlite_master WHERE type= 'table' AND name='player'")
    if len(result.fetchall()) > 0:
        return 1
    return 0

def open_db(filename: str) -> Tuple[sqlite3.Connection, sqlite3.Cursor]:
    db_conn = sqlite3.connect(filename)
    cursor = db_conn.cursor()
    return db_conn, cursor


def close_db(connection: sqlite3.Connection):
    connection.commit()
    connection.close()


def create_player_table(cursor: sqlite3.Cursor):
    cursor.execute('''CREATE TABLE IF NOT EXISTS player (
                   id INTEGER PRIMARY KEY,
                   -- What person this player record belongs to
                   person INTEGER REFERENCES person(id) DEFERRABLE INITIALLY DEFERRED,
                   -- NickServ account name, or NULL if this player is based on a hostmask
                   account TEXT COLLATE NOCASE,
                   -- Hostmask for the player, if not based on an account (NULL otherwise)
                   hostmask TEXT COLLATE NOCASE,
                   -- If a player entry needs to be retired (for example, an account expired),
                   -- setting this to 0 allows for that entry to be re-used without corrupting old stats/logs
                   active BOOLEAN NOT NULL DEFAULT 1
                   );''')


def drop_table_player(cursor: sqlite3.Cursor):
    cursor.execute('''DROP TABLE player''')
