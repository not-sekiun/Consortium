from functools import cache

import sqlalchemy
from sqlalchemy import Engine

from consortium.server.database.models import Base

_engine = None


@cache
def get_engine(database_url: str) -> Engine:
    return sqlalchemy.create_engine(database_url)


def create_tables(engine: Engine) -> None:
    Base.metadata.create_all(engine)
