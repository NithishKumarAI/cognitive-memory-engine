"""Explicit demo-only cleanup; never import from application startup."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.db.database import SessionLocal
from app.services.demo_service import purge_expired

if __name__ == "__main__":
    with SessionLocal() as db:
        count = purge_expired(db)
    print(f"Removed {count} expired demo sessions; unrelated accounts were not selected.")
