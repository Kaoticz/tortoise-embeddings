from __future__ import annotations
import re
from typing import Any, override
from tortoise.fields import Field
from tortoise.models import Model


try:
    from pgvector import SparseVector as PGSparseVector
except ImportError:
    PGSparseVector = None

class SparseVectorField(Field[Any]):
    """
    Field for pgvector's `sparsevec` type.
    """

    def __init__(self, dimensions: int | None = None, **kwargs: Any) -> None:
        """
        Initialize the SparseVector field.

        :param dimensions: The number of dimensions.
        :param kwargs: Additional arguments for the base Field class.
        """
        self.dimensions: int | None = dimensions
        super().__init__(**kwargs)
        if self.dimensions is not None:
            self.SQL_TYPE: str = f'sparsevec({self.dimensions})'
        else:
            self.SQL_TYPE = 'sparsevec'


    @override
    def get_db_field_types(self) -> dict[str, str]:
        """
        Return the database field types.

        :returns: A dictionary with the database dialect as key and the SQL type as value.
        """
        if self.dimensions is not None:
            return {'postgres': f'sparsevec({self.dimensions})'}
        return {'postgres': 'sparsevec'}

    @override
    def to_db_value(self, value: Any, instance: type[Model] | Model) -> Any | None:
        """
        Convert the Python value to a database-compatible value.

        :param value: The value to convert.
        :param instance: The model instance or class.
        :returns: The database-compatible value (PGSparseVector).
        """
        if value is None:
            return None
        if isinstance(value, str) and PGSparseVector is not None:
            # Try to parse '{index:value,...}/dim'
            match: re.Match[str] | None = re.match(r'\{(.*)\}/(\d+)', value)
            if match:
                elements_str: str = match.group(1)
                dim: int = int(match.group(2))
                elements: dict[int, float] = {}
                if elements_str:
                    for pair in elements_str.split(','):
                        k, v = pair.split(':')
                        elements[int(k)] = float(v)
                return PGSparseVector(elements, dim)
            elif value.startswith('{') and ':' in value:
                # Just elements, use field dimensions
                elements_str = value.strip('{}')
                elements = {}
                for pair in elements_str.split(','):
                    k, v = pair.split(':')
                    elements[int(k)] = float(v)
                return PGSparseVector(elements, self.dimensions) if self.dimensions is not None else PGSparseVector(elements)
        return value

    @override
    def to_python_value(self, value: Any) -> Any | None:
        """
        Convert the database value to a Python-native value.

        :param value: The value from the database.
        :returns: The Python-native value.
        """
        return value
