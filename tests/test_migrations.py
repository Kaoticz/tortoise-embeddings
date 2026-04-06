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


@pytest.mark.asyncio
async def test_successive_migration_injection() -> None:
    """
    Test that CREATE EXTENSION IF NOT EXISTS vector; is injected only once in successive migrations.
    """
    from tests.conftest import DB_URL
    from tortoise.migrations.schema_generator.state import State, ModelState
    from tortoise.migrations.schema_generator.state_apps import StateApps
    from tortoise.migrations.schema_generator.operation_generator import OperationGenerator
    from tortoise.migrations.operations import RunSQL
    from tests.models import ModelA, ModelB

    config = {
        'connections': {'default': DB_URL},
        'apps': {
            'models': {
                'models': ['tests.models'],
                'default_connection': 'default',
            }
        },
    }

    await Tortoise.close_connections()
    await Tortoise.init(config=config)

    try:
        # 1. Initial migration: only ModelA
        empty_apps = StateApps()
        empty_state = State(models={}, apps=empty_apps)

        current_apps = StateApps()
        current_state = State(models={}, apps=current_apps)
        m1_state = ModelState.make_from_model('models', ModelA)
        current_state.models[('models', 'ModelA')] = m1_state
        current_state.reload_model('models', 'ModelA')

        op_gen1 = OperationGenerator(empty_state, current_state)
        ops1 = op_gen1.generate(app_labels=['models'])

        has_run_sql1 = any(isinstance(op, RunSQL) and 'CREATE EXTENSION IF NOT EXISTS vector' in op.sql for op in ops1)
        assert has_run_sql1, 'First migration should have CREATE EXTENSION'

        # 2. Second migration: adds ModelB
        next_state = current_state.clone()
        m2_state = ModelState.make_from_model('models', ModelB)
        next_state.models[('models', 'ModelB')] = m2_state
        next_state.reload_model('models', 'ModelB')

        op_gen2 = OperationGenerator(current_state, next_state)
        ops2 = op_gen2.generate(app_labels=['models'])

        has_run_sql2 = any(isinstance(op, RunSQL) and 'CREATE EXTENSION IF NOT EXISTS vector' in op.sql for op in ops2)
        assert not has_run_sql2, 'Second migration should NOT have CREATE EXTENSION'

    finally:
        await Tortoise.close_connections()
