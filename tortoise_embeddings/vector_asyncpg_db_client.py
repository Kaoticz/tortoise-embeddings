from __future__ import annotations

import logging
from asyncio import get_running_loop
from typing import Any, override, TYPE_CHECKING, cast

from asyncpg import Connection, Pool, Record
try:
    from pgvector import Vector, HalfVector, SparseVector
except ImportError:
    Vector = HalfVector = SparseVector = None

from tortoise.backends.asyncpg.client import AsyncpgDBClient
from .postgres_ddl import PostgresDDL


logger: logging.Logger = logging.getLogger(__name__)


class VectorAsyncpgDBClient(AsyncpgDBClient):
    """
    Custom AsyncpgDBClient that supports pgvector binary codecs.
    """

    @staticmethod
    async def setup_pgvector(conn: Connection) -> None:
        """
        Setup pgvector binary codecs for the given connection.

        :param conn: The asyncpg connection to configure.
        """
        if Vector is None:
            return
        # Discover OIDs for pgvector types
        try:
            # Check if extension is installed
            exists: Any = await conn.fetchval('SELECT 1 FROM pg_extension WHERE extname = \'vector\'')
            if not exists:
                return

            types: list[Record] = await conn.fetch(
                'SELECT n.nspname, t.typname FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace WHERE t.typname IN (\'vector\', \'halfvec\', \'sparsevec\')'
            )

            for row in types:
                schema: str = row['nspname']
                typname: str = row['typname']
                if typname == 'vector' and Vector is not None:
                    await conn.set_type_codec(
                        'vector',
                        encoder=Vector._to_db_binary,
                        decoder=Vector._from_db_binary,
                        format='binary',
                        schema=schema
                    )
                elif typname == 'halfvec' and HalfVector is not None:
                    await conn.set_type_codec(
                        'halfvec',
                        encoder=HalfVector._to_db_binary,
                        decoder=HalfVector._from_db_binary,
                        format='binary',
                        schema=schema
                    )
                elif typname == 'sparsevec' and SparseVector is not None:
                    await conn.set_type_codec(
                        'sparsevec',
                        encoder=SparseVector._to_db_binary,
                        decoder=SparseVector._from_db_binary,
                        format='binary',
                        schema=schema
                    )
        except Exception as e:
            logger.warning(f'Failed to setup pgvector codecs: {e}')

    @override
    async def create_pool(self, **kwargs: Any) -> Pool:
        """
        Create a connection pool with pgvector support.

        :param kwargs: Arguments for creating the pool.
        :returns: The created connection pool.
        :raises RuntimeError: If pool creation fails.
        """
        user_setup: Any = kwargs.get('setup')

        async def setup(conn: Connection) -> None:
            await self.setup_pgvector(conn)
            if user_setup:
                if callable(user_setup):
                    res: Any = user_setup(conn)
                    if hasattr(res, '__await__'):
                        await res

        kwargs['setup'] = setup
        # We need to make sure 'loop' is in kwargs for asyncpg
        if 'loop' not in kwargs:
            kwargs['loop'] = get_running_loop()
            
        # Call the parent class's create_pool method.
        # It's an async method in Tortoise, returning a Pool (or something like it).
        # We use Any to bypass basedpyright's confusion about awaitability.
        # We use cast(Any, super()) to avoid basedpyright confusion.
        pool: Pool = await super().create_pool(**kwargs)
        if pool is None:
            raise RuntimeError('Failed to create pool')
        return pool


# We set the schema_generator on the class after definition to avoid some type check issues
VectorAsyncpgDBClient.schema_generator = PostgresDDL # type: ignore
