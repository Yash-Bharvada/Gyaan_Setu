"""Database & Storage Reset Script for Gyaan Setu.

Wipes all existing sources, units, knowledge DAGs, flashcards, chat sessions,
local vector indexes, and file uploads to provide a completely clean slate.
Initializes a clean schema and creates an active student profile (ID: 1).
"""
import os
import shutil
import sys

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.core.db import SessionLocal, init_db, engine
from app.models import Student


def reset_all():
    print("=" * 60)
    print("🧹 RESETTING GYAAN SETU DATABASE & STORAGE")
    print("=" * 60)

    # 1. Close engine connections
    engine.dispose()

    # 2. Paths to clear
    data_dir = settings.DATA_DIR
    db_file = os.path.join(data_dir, "studycompanion.db")
    shm_file = os.path.join(data_dir, "studycompanion.db-shm")
    wal_file = os.path.join(data_dir, "studycompanion.db-wal")

    file_removed = False
    try:
        if os.path.exists(db_file):
            os.remove(db_file)
            file_removed = True
            print(f"✓ Removed SQLite file: {os.path.basename(db_file)}")
        for f in [shm_file, wal_file]:
            if os.path.exists(f):
                os.remove(f)
                print(f"✓ Removed SQLite file: {os.path.basename(f)}")
    except Exception as e:
        print(f"ℹ SQLite file is currently locked by active server: {e}")
        print("  Dropping all tables via SQL connection instead...")

    # If SQLite file could not be deleted from disk due to lock, drop all tables via SQL
    if not file_removed and os.path.exists(db_file):
        from sqlalchemy import text
        with engine.begin() as conn:
            conn.execute(text("PRAGMA foreign_keys = OFF;"))
            tables = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            ).fetchall()
            for (t_name,) in tables:
                conn.execute(text(f'DROP TABLE IF EXISTS "{t_name}";'))
                print(f"  ✓ Dropped table: {t_name}")
            conn.execute(text("PRAGMA foreign_keys = ON;"))
        with engine.connect() as conn:
            conn.execute(text("VACUUM;"))
        print("✓ All database tables successfully dropped and database vacuumed.")

    # 3. Clean local Chroma vector store
    chroma_path = os.path.join(data_dir, "local_vectors")
    if os.path.exists(chroma_path):
        try:
            import chromadb
            client = chromadb.PersistentClient(path=chroma_path)
            collections = client.list_collections()
            for col in collections:
                client.delete_collection(col.name)
                print(f"✓ Cleared Chroma vector collection: {col.name}")
        except Exception as e:
            print(f"ℹ Chroma collection reset notice: {e}")

        # Clean orphaned vector segment directories if unlocked
        for item in os.listdir(chroma_path):
            if item in ["chroma.sqlite3", ".gitkeep"]:
                continue
            item_path = os.path.join(chroma_path, item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            except Exception:
                pass

    # 4. Clear LLM diskcache
    cache_path = os.path.join(data_dir, "llm_cache")
    if os.path.exists(cache_path):
        try:
            from diskcache import Cache
            with Cache(cache_path) as c:
                c.clear()
            print("✓ Cleared diskcache in data/llm_cache")
        except Exception as e:
            print(f"ℹ LLM cache clear notice: {e}")

    # 5. Clean asset subdirectories (uploads, audio, audio_cache, eval)
    for sub in ["uploads", "audio", "audio_cache", "eval"]:
        path = os.path.join(data_dir, sub)
        if os.path.exists(path):
            count = 0
            for item in os.listdir(path):
                if item == ".gitkeep":
                    continue
                item_path = os.path.join(path, item)
                try:
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
                    count += 1
                except Exception as e:
                    print(f"⚠ Could not remove {item_path}: {e}")
            print(f"✓ Cleared {count} item(s) from data/{sub}")
        else:
            os.makedirs(path, exist_ok=True)
            print(f"✓ Created fresh directory: data/{sub}")

    # 6. Reinitialize database tables
    print("\n[+] Creating fresh database schema...")
    init_db()
    print("✓ All tables created successfully.")

    # 7. Create default active student profile (ID: 1)
    db = SessionLocal()
    try:
        student = Student(
            id=1,
            name="Alex Chen",
            lang="en",
            daily_minutes=30,
        )
        db.add(student)
        db.commit()
        db.refresh(student)
        print(f"✓ Created fresh default student profile: {student.name} (ID: {student.id})")
    finally:
        db.close()

    print("\n" + "=" * 60)
    print("🎉 FRESH SLATE READY! Database is completely empty.")
    print("   - Ingested Sources: 0")
    print("   - Knowledge Graph Topics: 0")
    print("   - Flashcards: 0")
    print("   - Assessments / Quizzes: 0")
    print("   - Chat History: 0")
    print("   - Uploaded Files & YouTube Transcripts: 0")
    print("   - Active Student: Alex Chen (ID: 1)")
    print("=" * 60)


if __name__ == "__main__":
    reset_all()
