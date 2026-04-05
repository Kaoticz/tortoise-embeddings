from __future__ import annotations
import asyncio
import os
import shutil
from dotenv import load_dotenv

load_dotenv()

from asyncio import AbstractEventLoop
from collections.abc import AsyncGenerator, Generator
from typing import Any
import pytest
from aerich import Command
from tortoise import Tortoise
import tortoise.backends.asyncpg
from tortoise_embeddings.vector_asyncpg_db_client import VectorAsyncpgDBClient

# Override the client class for the asyncpg backend
tortoise.backends.asyncpg.client_class = VectorAsyncpgDBClient


def get_db_url() -> str | None:
    """
    Get the database URL from environment variables.

    :returns: The database URL or None if not set.
    """
    return os.getenv('PSQL_CONNECTION_STRING')


DB_URL: str | None = get_db_url()
TORTOISE_CONFIG: dict[str, Any] = {
    'connections': {'default': DB_URL},
    'apps': {
        'models': {
            'models': ['tests.models', 'aerich.models'],
            'default_connection': 'default',
        }
    },
}

@pytest.fixture(autouse=True)
async def initialize_tests() -> AsyncGenerator[None, None]:
    """
    Initialize Tortoise ORM and apply Aerich migrations for tests.

    :raises RuntimeError: If PSQL_CONNECTION_STRING is not set.
    """
    db_url: str | None = get_db_url()
    if not db_url:
        pytest.fail('PSQL_CONNECTION_STRING environment variable is not set')

    config: dict[str, Any] = TORTOISE_CONFIG.copy()
    config['connections']['default'] = db_url

    # Initial cleanup
    await Tortoise.init(config=config)
    conn: Any = Tortoise.get_connection('default')
    try:
        await conn.execute_query('DROP TABLE IF EXISTS aerich CASCADE;')
        await conn.execute_query('DROP TABLE IF EXISTS vector_model CASCADE;')
        await conn.execute_query('DROP TABLE IF EXISTS variable_vector_model CASCADE;')
        await conn.execute_query('DROP TABLE IF EXISTS nullable_vector_model CASCADE;')
        await conn.execute_query('DROP TABLE IF EXISTS nullable_variable_vector_model CASCADE;')
        await conn.execute_query('DROP TABLE IF EXISTS gemini_model CASCADE;')
    except Exception:
        pass
    await Tortoise.close_connections()

    # Aerich migration logic
    migrations_dir: str = 'tests/migrations'
    if os.path.exists(migrations_dir):
        shutil.rmtree(migrations_dir)

    command: Command = Command(tortoise_config=config, location=migrations_dir)
    await command.init()
    await command.init_db(safe=True)

    await Tortoise.init(config=config)
    yield
    await Tortoise.close_connections()

@pytest.fixture(scope='session', autouse=True)
async def cleanup_db() -> AsyncGenerator[None, None]:
    """
    Clean up the database and migration files after the session.
    """
    yield
    db_url: str | None = get_db_url()
    if not db_url:
        return

    config: dict[str, Any] = TORTOISE_CONFIG.copy()
    config['connections']['default'] = db_url

    # Final cleanup after all tests
    await Tortoise.init(config=config)
    conn: Any = Tortoise.get_connection('default')
    try:
        # Get all tables in the current schema
        _, tables = await conn.execute_query('''
            SELECT tablename FROM pg_catalog.pg_tables 
            WHERE schemaname = 'public'
        ''')
        for table in tables:
            await conn.execute_query(f'DROP TABLE IF EXISTS "{table["tablename"]}" CASCADE;')
    except Exception:
        pass
    await Tortoise.close_connections()

    migrations_dir: str = 'tests/migrations'
    if os.path.exists(migrations_dir):
        shutil.rmtree(migrations_dir)

@pytest.fixture(scope='session')
def event_loop() -> Generator[AbstractEventLoop, None, None]:
    """
    Create an instance of the default event loop for each test case.
    """
    res: AbstractEventLoop = asyncio.new_event_loop()
    asyncio.set_event_loop(res)
    yield res
    res.close()
