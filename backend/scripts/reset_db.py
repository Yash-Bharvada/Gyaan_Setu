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

    for f in [db_file, shm_file, wal_file]:
        if os.path.exists(f):
            try:
                os.remove(f)
                print(f"✓ Removed SQLite file: {os.path.basename(f)}")
            except Exception as e:
                print(f"⚠ Could not remove {f}: {e}")

    # 3. Clean subdirectories
    subdirs = ["local_vectors", "uploads", "audio", "llm_cache", "eval"]
    for sub in subdirs:
        path = os.path.join(data_dir, sub)
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
                os.makedirs(path, exist_ok=True)
                print(f"✓ Cleared and recreated directory: data/{sub}")
            except Exception as e:
                print(f"⚠ Could not clear data/{sub}: {e}")
        else:
            os.makedirs(path, exist_ok=True)
            print(f"✓ Created fresh directory: data/{sub}")

    # 4. Reinitialize database tables
    print("\n[+] Creating fresh database schema...")
    init_db()
    print("✓ All tables created successfully.")

    # 5. Create default active student profile (ID: 1)
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
    print("   - Chat History: 0")
    print("   - Active Student: Alex Chen (ID: 1)")
    print("=" * 60)


if __name__ == "__main__":
    reset_all()
