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
    """
    await original_init(config=config, config_file=config_file, _create_db=_create_db, db_url=db_url, modules=modules, use_tz=use_tz, timezone=timezone, routers=routers, **kwargs)
    register_filters()

OriginalTortoise.init = classmethod(patched_init)  # type: ignore


# Aerich support
try:
    import aerich.ddl.postgres
    from ..aerich_vector_postgres_ddl import AerichVectorPostgresDDL
    if AerichVectorPostgresDDL is not None:
        aerich.ddl.postgres.PostgresDDL = AerichVectorPostgresDDL  # type: ignore
except (ImportError, AttributeError):
    pass
