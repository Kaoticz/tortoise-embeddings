from __future__ import annotations
from typing import Any, override, cast
from tortoise.fields import Field
from tortoise.models import Model


try:
    from asyncpg.pgproto.types import BitString
except ImportError:
    BitString = None


class BinaryVectorField(Field[Any]):
    """
    Field for pgvector's `bit` type.
    """
    dimensions: int | None
    SQL_TYPE: str

    def __init__(self, dimensions: int | None = None, **kwargs: Any) -> None:
        """
        Initialize the BinaryVector field.

        :param dimensions: The number of bits.
        :param kwargs: Additional arguments for the base Field class.
        """
        self.dimensions = dimensions
        super().__init__(**kwargs)
        if self.dimensions is not None:
            self.SQL_TYPE = f'bit({self.dimensions})'
        else:
            self.SQL_TYPE = 'varbit'

    @override
    def get_db_field_types(self) -> dict[str, str]:
        """
        Return the database field types.

        :returns: A dictionary with the database dialect as key and the SQL type as value.
        """
        if self.dimensions is not None:
            return {'postgres': f'bit({self.dimensions})'}
        return {'postgres': 'varbit'}

    @override
    def to_db_value(self, value: Any, instance: type[Model] | Model) -> Any | None:
        """
        Convert the Python value to a database-compatible value.

        :param value: The value to convert.
        :param instance: The model instance or class.
        :returns: The database-compatible value (BitString).
        """
        if value is None:
            return None
        if isinstance(value, str) and BitString is not None:
            # BitString expects bytes or None in some versions, but actually it accepts str.
            # Basedpyright might complain if it only sees bytes in the stub.
            return BitString(cast(Any, value))
        return value

    @override
    def to_python_value(self, value: Any) -> str | None:
        """
        Convert the database value to a Python-native value.

        :param value: The value from the database.
        :returns: The Python-native value (bit string).
        """
        if value is None:
            return None
        if hasattr(value, 'as_string'):
            return cast(str, value.as_string()).replace(' ', '')
        return str(value).replace(' ', '')
