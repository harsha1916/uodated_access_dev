import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.path.expanduser("~/camcap/camcap.db")

SCHEMA = """PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    source TEXT NOT NULL,
    epoch INTEGER NOT NULL,
    uploaded INTEGER NOT NULL DEFAULT 0,
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_images_uploaded ON images(uploaded, created_at);
"""

@contextmanager
def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.commit()
    conn.close()

def init_db():
    with get_conn() as c:
        for stmt in SCHEMA.strip().split(";"):
            if stmt.strip():
                c.execute(stmt)

def add_image(filename: str, source: str, epoch: int):
    with get_conn() as c:
        c.execute(
            "INSERT INTO images (filename, source, epoch, created_at) VALUES (?,?,?,?)",
            (filename, source, epoch, epoch)
        )

def list_recent(limit=100, offset=0):
    with get_conn() as c:
        cur = c.execute(
            "SELECT * FROM images ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        return [dict(r) for r in cur.fetchall()]

def get_pending_batch(limit=10):
    with get_conn() as c:
        cur = c.execute(
            "SELECT * FROM images WHERE uploaded=0 ORDER BY attempts ASC, created_at ASC LIMIT ?",
            (limit,)
        )
        return [dict(r) for r in cur.fetchall()]

def mark_uploaded(image_id: int):
    with get_conn() as c:
        c.execute("UPDATE images SET uploaded=1, last_error=NULL WHERE id=?", (image_id,))

def mark_failed(image_id: int, err: str):
    with get_conn() as c:
        c.execute("UPDATE images SET attempts=attempts+1, last_error=? WHERE id=?", (err[:500], image_id))

def delete_older_than(epoch_threshold: int):
    with get_conn() as c:
        cur = c.execute("SELECT id, filename FROM images WHERE created_at < ?", (epoch_threshold,))
        rows = cur.fetchall()
        for r in rows:
            try:
                if os.path.exists(r["filename"]):
                    os.remove(r["filename"])
            except Exception:
                pass
        c.execute("DELETE FROM images WHERE created_at < ?", (epoch_threshold,))

def get_storage_stats():
    """Get storage statistics."""
    with get_conn() as c:
        # Total images
        total = c.execute("SELECT COUNT(*) as cnt FROM images").fetchone()['cnt']
        
        # By source
        by_source = {}
        cur = c.execute("SELECT source, COUNT(*) as cnt FROM images GROUP BY source")
        for row in cur.fetchall():
            by_source[row['source']] = row['cnt']
        
        # Uploaded vs pending
        uploaded = c.execute("SELECT COUNT(*) as cnt FROM images WHERE uploaded=1").fetchone()['cnt']
        pending = c.execute("SELECT COUNT(*) as cnt FROM images WHERE uploaded=0").fetchone()['cnt']
        
        return {
            'total': total,
            'by_source': by_source,
            'uploaded': uploaded,
            'pending': pending
        }

def get_images_by_date(date_str: str, source_filter: str = None, limit: int = 50, offset: int = 0):
    """Get images for a specific date (YYYY-MM-DD format)."""
    from datetime import datetime
    
    # Convert date string to epoch range
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        start_epoch = int(date_obj.timestamp())
        end_epoch = start_epoch + 86400  # +24 hours
    except:
        return []
    
    with get_conn() as c:
        if source_filter:
            cur = c.execute(
                "SELECT * FROM images WHERE epoch >= ? AND epoch < ? AND source = ? ORDER BY epoch DESC LIMIT ? OFFSET ?",
                (start_epoch, end_epoch, source_filter, limit, offset)
            )
        else:
            cur = c.execute(
                "SELECT * FROM images WHERE epoch >= ? AND epoch < ? ORDER BY epoch DESC LIMIT ? OFFSET ?",
                (start_epoch, end_epoch, limit, offset)
            )
        return [dict(r) for r in cur.fetchall()]

def get_images_by_date_count(date_str: str, source_filter: str = None):
    """Get count of images for a specific date."""
    from datetime import datetime
    
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        start_epoch = int(date_obj.timestamp())
        end_epoch = start_epoch + 86400
    except:
        return 0
    
    with get_conn() as c:
        if source_filter:
            cnt = c.execute(
                "SELECT COUNT(*) as cnt FROM images WHERE epoch >= ? AND epoch < ? AND source = ?",
                (start_epoch, end_epoch, source_filter)
            ).fetchone()['cnt']
        else:
            cnt = c.execute(
                "SELECT COUNT(*) as cnt FROM images WHERE epoch >= ? AND epoch < ?",
                (start_epoch, end_epoch)
            ).fetchone()['cnt']
        return cnt

def get_date_list():
    """Get list of dates that have images."""
    from datetime import datetime
    with get_conn() as c:
        cur = c.execute("SELECT DISTINCT DATE(epoch, 'unixepoch', 'localtime') as date FROM images ORDER BY date DESC LIMIT 90")
        return [row['date'] for row in cur.fetchall()]
