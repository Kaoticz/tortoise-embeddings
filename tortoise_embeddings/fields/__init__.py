from __future__ import annotations
from typing import Any, override, TYPE_CHECKING, Iterable
from tortoise import fields
from tortoise.models import MetaInfo, Model
from tortoise.filters import FilterInfoDict, get_filters_for_field as original_get_filters_for_field

from .vector_field import VectorField
from .half_vector_field import HalfVectorField
from .binary_vector_field import BinaryVectorField
from .sparse_vector_field import SparseVectorField
from ..similarity import create_vector_operator

if TYPE_CHECKING:
    from tortoise import Tortoise

__all__ = [
    'VectorField',
    'HalfVectorField',
    'BinaryVectorField',
    'SparseVectorField',
]


def get_vector_filters(field_name: str, source_field: str, field: fields.Field[Any]) -> dict[str, FilterInfoDict]:
    """
    Get custom similarity filters for a vector field.

    :param field_name: The name of the field.
    :param source_field: The database column name.
    :param field: The field instance.
    :returns: A dictionary of filters.
    """
    vector_type: str = 'vector'
    if isinstance(field, HalfVectorField):
        vector_type = 'halfvec'
    elif isinstance(field, BinaryVectorField):
        vector_type = 'bit' if field.dimensions is not None else 'varbit'
    elif isinstance(field, SparseVectorField):
        vector_type = 'sparsevec'

    return {
        f'{field_name}__l2': {
            'field': field_name,
            'source_field': source_field,
            'operator': create_vector_operator('<->', '<', vector_type=vector_type),
        },
        f'{field_name}__inner': {
            'field': field_name,
            'source_field': source_field,
            'operator': create_vector_operator('<#>', '<', vector_type=vector_type),
        },
        f'{field_name}__cosine': {
            'field': field_name,
            'source_field': source_field,
            'operator': create_vector_operator('<=>', '<', vector_type=vector_type),
        },
        f'{field_name}__l1': {
            'field': field_name,
            'source_field': source_field,
            'operator': create_vector_operator('<+>', '<', vector_type=vector_type),
        },
        f'{field_name}__hamming': {
            'field': field_name,
            'source_field': source_field,
            'operator': create_vector_operator('<~>', '<', vector_type=vector_type if 'bit' in vector_type else 'bit'),
        },
        f'{field_name}__jaccard': {
            'field': field_name,
            'source_field': source_field,
            'operator': create_vector_operator('%', '<', vector_type=vector_type),
        },
    }


def patched_get_filters_for_field(
    field_name: str, field: fields.Field[Any] | None, source_field: str
) -> dict[str, FilterInfoDict]:
    """
    Patched version of Tortoise's get_filters_for_field to include vector filters.

    :param field_name: The name of the field.
    :param field: The field instance.
    :param source_field: The database column name.
    :returns: A dictionary of filters.
    """
    res: dict[str, FilterInfoDict] = original_get_filters_for_field(field_name, field, source_field)
    if isinstance(field, (VectorField, BinaryVectorField, SparseVectorField)):
        res.update(get_vector_filters(field_name, source_field, field))
    return res


import tortoise.filters
tortoise.filters.get_filters_for_field = patched_get_filters_for_field 

original_add_field = MetaInfo.add_field


def patched_add_field(self: MetaInfo, name: str, value: fields.Field[Any]) -> None:
    """
    Patched version of MetaInfo.add_field to ensure vector filters are registered.

    :param self: The MetaInfo instance.
    :param name: The field name.
    :param value: The field instance.
    """
    original_add_field(self, name, value)
    if isinstance(value, (VectorField, BinaryVectorField, SparseVectorField)):
        field_filters: dict[str, FilterInfoDict] = get_vector_filters(
            field_name=name, source_field=value.source_field or name, field=value
        )
        self._filters.update(field_filters)
        if hasattr(self, 'filters'):
            self.filters.update(field_filters)


MetaInfo.add_field = patched_add_field  # type: ignore


def register_filters() -> None:
    """
    Register similarity filters for all existing models.
    """
    from tortoise import Tortoise
    for app in Tortoise.apps.values():
        for model in app.values():
            for name, field in model._meta.fields_map.items():
                if isinstance(field, (VectorField, BinaryVectorField, SparseVectorField)):
                    field_filters: dict[str, FilterInfoDict] = get_vector_filters(
                        field_name=name, source_field=field.source_field or name, field=field
                    )
                    model._meta._filters.update(field_filters)
                    model._meta.filters.update(field_filters)


from tortoise import Tortoise as OriginalTortoise
original_init = OriginalTortoise.init


async def patched_init(cls: type[OriginalTortoise], config: dict[str, Any] | None = None, config_file: str | None = None, _create_db: bool = False, db_url: str | None = None, modules: dict[str, Any] | None = None, use_tz: bool = False, timezone: str = 'UTC', routers: list[str | type] | None = None, **kwargs: Any) -> None:
    """
    Patched version of Tortoise.init to ensure filters are registered after initialization.

    :param cls: The Tortoise class.
    :param config: The configuration dictionary.
    :param config_file: Path to a configuration file.
    :param _create_db: Whether to create the database if it doesn't exist.
    :param db_url: The database URL.
    :param modules: Dictionary of model modules.
    :param use_tz: Whether to use timezone-aware datetimes.
    :param timezone: The timezone to use.
    :param routers: List of database routers.
    :param kwargs: Additional arguments for initialization.
    """
    await original_init(config=config, config_file=config_file, _create_db=_create_db, db_url=db_url, modules=modules, use_tz=use_tz, timezone=timezone, routers=routers, **kwargs)
    register_filters()

OriginalTortoise.init = classmethod(patched_init)  # type: ignore

# Migration support
try:
    from collections.abc import Sequence
    from tortoise.migrations.operations import RunSQL, CreateModel, AddField, AlterField
    from tortoise.migrations.schema_generator.operation_generator import OperationGenerator
    from tortoise.migrations.writer import ImportManager, MigrationWriter

    # 1. Patch OperationGenerator to inject the RunSQL operation
    original_generate = OperationGenerator.generate


    def patched_generate(self: OperationGenerator, app_labels: Sequence[str] | None = None) -> list[Any]:
        """
        Patched version of OperationGenerator.generate to inject CREATE EXTENSION vector.
        """
        operations: list[Any] = original_generate(self, app_labels=app_labels)

        has_vector: bool = False
        for op in operations:
            if isinstance(op, CreateModel):
                for _, field in op.fields:
                    if isinstance(field, (VectorField, HalfVectorField, BinaryVectorField, SparseVectorField)):
                        has_vector = True
                        break
            elif isinstance(op, (AddField, AlterField)):
                if isinstance(op.field, (VectorField, HalfVectorField, BinaryVectorField, SparseVectorField)):
                    has_vector = True
            if has_vector:
                break

        if has_vector:
            # Avoid duplicate if already present
            already_has: bool = False
            for op in operations:
                if (isinstance(op, RunSQL) and isinstance(
                    op.sql, str
                ) and 'CREATE EXTENSION IF NOT EXISTS vector' in op.sql):
                    already_has = True
                    break

            if not already_has:
                operations.insert(
                    0,
                    RunSQL(sql='CREATE EXTENSION IF NOT EXISTS vector;', reverse_sql='DROP EXTENSION IF EXISTS vector;')
                )

        return operations


    OperationGenerator.generate = patched_generate  # type: ignore

    # 2. Patch MigrationWriter to teach it how to write RunSQL to the file
    original_format_operation = MigrationWriter._format_operation


    def patched_format_operation(self: MigrationWriter, operation: Any, imports: ImportManager, indent: str) -> list[str]:
        """
        Patched version of MigrationWriter._format_operation to handle RunSQL.
        """
        if isinstance(operation, RunSQL):
            imports.add_from('tortoise.migrations.operations', 'RunSQL')

            sql = operation.sql
            rev = operation.reverse_sql
            # Format the line as it will appear in the migrations/models.py file
            return [f'{indent}RunSQL(sql={sql!r}, reverse_sql={rev!r}),']

        return original_format_operation(self, operation, imports, indent=indent)


    MigrationWriter._format_operation = patched_format_operation  # type: ignore

except (ImportError, AttributeError):
    pass
