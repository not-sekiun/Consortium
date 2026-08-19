import functools

import sqlalchemy


@functools.cache
def get_engine(connection_string: str) -> sqlalchemy.engine.base.Engine:
    return sqlalchemy.create_engine(connection_string)
