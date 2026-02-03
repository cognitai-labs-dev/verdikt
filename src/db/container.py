from contextlib import contextmanager
from collections.abc import Iterator

from sqlalchemy import Connection, Engine, create_engine


class DbContainer:
    _engine: Engine

    def init(self, connection_string: str) -> None:
        self._engine = create_engine(connection_string)

    @contextmanager
    def connection(self) -> Iterator[Connection]:
        """Per-request connection. Commits on success, rolls back on exception."""
        with self._engine.connect() as conn:
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def dispose(self) -> None:
        self._engine.dispose()


db = DbContainer()
