"""SQLite cache for fetched neurons.

Schema lives in models/neuron.py. The cache stores the full upstream JSON record
plus the raw SWC text, so we never have to refetch identical data and so the
inspector can show the exact source bytes.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "neurons.sqlite"

_engine = None
_SessionLocal = None


def _get_engine(db_path: Path | None = None):
    global _engine, _SessionLocal
    if _engine is None:
        path = db_path or DEFAULT_DB_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(f"sqlite:///{path}", future=True)
        _SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False, future=True)
    return _engine


def init_db(db_path: Path | None = None) -> None:
    """Create tables if missing. Safe to call repeatedly."""
    from neuroforge_api.models.neuron import Base

    engine = _get_engine(db_path)
    Base.metadata.create_all(engine)


@contextmanager
def session_scope() -> Iterator[Session]:
    if _SessionLocal is None:
        _get_engine()
    assert _SessionLocal is not None
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def reset_for_tests(db_path: Path) -> None:
    """Reset the global engine to point at a test DB. Test-only."""
    global _engine, _SessionLocal
    _engine = None
    _SessionLocal = None
    _get_engine(db_path)
