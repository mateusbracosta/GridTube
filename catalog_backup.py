import json
import sqlite3
from contextlib import closing


FORMAT = {"format": "gridtube-catalog", "version": 1}
STYLE_TABLES = {"channel_style", "playlist_style"}
TABLES = ("settings", "channel", "channel_description", "playlist", "channel_style", "playlist_style",
          "video", "playlist_item", "seen", "track_job")
CACHE_TABLES = ("playlist_entry", "source_playlist", "entry", "scan", "channel_profile", "system_event")
LINE_LIMIT = 1024 * 1024


def export_lines(db):
    db.execute("BEGIN")
    yield json.dumps(FORMAT) + "\n"
    for table in TABLES:
        for row in db.execute(f"SELECT * FROM {table} ORDER BY rowid"):
            yield json.dumps({"table": table, "row": dict(row)}, ensure_ascii=False) + "\n"
    yield '{"end":true}\n'


def load_backup(upload, target, schema, validate):
    counts = {"channel": 0, "playlist": 0, "video": 0, "missing": 0}
    with closing(sqlite3.connect(target)) as db, db:
        db.execute("PRAGMA foreign_keys=ON")
        db.executescript(schema)
        columns = {table: [row[1] for row in db.execute(f"PRAGMA table_info({table})")] for table in TABLES}
        commands = {table: f"INSERT INTO {table} ({','.join(names)}) VALUES ({','.join('?' for _ in names)})"
                    for table, names in columns.items()}
        if json.loads(upload.readline(LINE_LIMIT + 1)) != FORMAT:
            raise ValueError("backup_invalid")
        while line := upload.readline(LINE_LIMIT + 1):
            if len(line) > LINE_LIMIT:
                raise ValueError("backup_invalid")
            record = json.loads(line)
            if record == {"end": True}:
                if upload.read(1) or db.execute("SELECT count(*) FROM settings").fetchone()[0] != 1:
                    raise ValueError("backup_invalid")
                if db.execute("""SELECT 1 FROM channel_style s JOIN channel c ON s.id=c.id
                    WHERE c.source IS NOT NULL LIMIT 1""").fetchone():
                    raise ValueError("backup_invalid")
                return counts
            table, row = record["table"], record["row"]
            # Backups from before the automatic-download badge remain restorable.
            if table == "video" and isinstance(row, dict):
                row.setdefault("unopened_auto", 0)
            if table not in columns or not isinstance(row, dict) or set(row) != set(columns[table]):
                raise ValueError("backup_invalid")
            if validate(table, row):
                counts["missing"] += 1
            db.execute(commands[table], [row[name] for name in columns[table]])
            if table in counts:
                counts[table] += 1
        raise ValueError("backup_invalid")


def replace_catalog(db, candidate=None):
    if candidate is not None:
        db.execute("ATTACH DATABASE ? AS restored", (str(candidate),))
    db.execute("BEGIN IMMEDIATE")
    for table in (*CACHE_TABLES, *reversed(TABLES)):
        if candidate is not None and table == "channel_profile":
            continue
        db.execute(f"DELETE FROM {table}")
    if candidate is not None:
        available = {row[0] for row in db.execute("SELECT name FROM restored.sqlite_master WHERE type='table'")}
        for table in TABLES:
            if table in STYLE_TABLES and table not in available:
                continue
            columns = ",".join(row[1] for row in db.execute(f"PRAGMA main.table_info({table})"))
            db.execute(f"INSERT INTO main.{table} ({columns}) SELECT {columns} FROM restored.{table}")


def verify_restored_catalog(db):
    if db.execute("PRAGMA main.quick_check").fetchone()[0] != "ok" or db.execute("PRAGMA main.foreign_key_check").fetchone():
        raise ValueError("backup_verification_failed")
    available = {row[0] for row in db.execute("SELECT name FROM restored.sqlite_master WHERE type='table'")}
    for table in TABLES:
        if table in STYLE_TABLES and table not in available:
            if db.execute(f"SELECT 1 FROM main.{table} LIMIT 1").fetchone():
                raise ValueError("backup_verification_failed")
            continue
        if (db.execute(f"SELECT * FROM main.{table} EXCEPT SELECT * FROM restored.{table} LIMIT 1").fetchone()
                or db.execute(f"SELECT * FROM restored.{table} EXCEPT SELECT * FROM main.{table} LIMIT 1").fetchone()):
            raise ValueError("backup_verification_failed")
