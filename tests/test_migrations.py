from __future__ import annotations
import os
import shutil
from typing import cast, Any
import pytest
from tortoise import Tortoise
from tortoise.migrations.autodetector import MigrationAutodetector
from tortoise.migrations.operations import RunSQL
from tortoise.migrations.writer import MigrationWriter


@pytest.mark.asyncio
async def test_migration_injection() -> None:
    """
    Test that CREATE EXTENSION IF NOT EXISTS vector; is injected into migrations.
    """
    # Use the connection URL from environment or fallback
    from tests.conftest import DB_URL
    
    # Initialize Tortoise with our model and explicit migration module
    config = {
        'connections': {'default': DB_URL},
        'apps': {
            'models': {
                'models': ['tests.models'],
                'default_connection': 'default',
                'migrations': 'tests.migrations_test',
            }
        },
    }
    
    # We close connections because initialize_tests might have already opened them
    await Tortoise.close_connections()
    await Tortoise.init(config=config)
    
    try:
        # Create migrations_test directory if it doesn't exist
        os.makedirs('tests/migrations_test', exist_ok=True)
        with open('tests/migrations_test/__init__.py', 'w') as f:
            pass

        autodetector: MigrationAutodetector = MigrationAutodetector(
            apps=Tortoise.apps,
            apps_config=cast(Any, config['apps'])
        )
        
        # We want to check the 'changes' method result
        writers: list[MigrationWriter] = await autodetector.changes()
        
        assert len(writers) > 0
        initial_migration = writers[0]
        
        has_extension_op: bool = False
        for op in initial_migration.operations:
            if isinstance(op, RunSQL) and 'CREATE EXTENSION IF NOT EXISTS vector;' in op.sql:
                has_extension_op = True
                break
        
        assert has_extension_op, 'CREATE EXTENSION IF NOT EXISTS vector; was not injected into migration'
        
    finally:
        await Tortoise.close_connections()
        if os.path.exists('tests/migrations_test'):
            shutil.rmtree('tests/migrations_test')
