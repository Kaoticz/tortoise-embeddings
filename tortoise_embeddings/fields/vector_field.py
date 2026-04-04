from __future__ import annotations
from typing import Any, override
from tortoise.fields import Field
from tortoise.models import Model
import numpy as np

class VectorField(Field[Any]):
    """
    Field for pgvector's `vector` type.

    :param dimensions: The number of dimensions for the vector.
    """
    def __init__(self, dimensions: int, **kwargs: Any) -> None:
        """
        Initialize the VectorField.

        :param dimensions: The number of dimensions for the vector.
        :param kwargs: Additional arguments for the base Field class.
        """
        self.dimensions: int = dimensions
        super().__init__(**kwargs)
        self.SQL_TYPE: str = f'vector({self.dimensions})'

    @override
    def get_db_field_types(self) -> dict[str, str]:
        """
        Return the database field types.

        :returns: A dictionary with the database dialect as key and the SQL type as value.
        """
        return {'postgres': f'vector({self.dimensions})'}

    @override
    def to_db_value(self, value: Any, instance: type[Model] | Model) -> Any | None:
        """
        Convert the Python value to a database-compatible value.

        :param value: The value to convert.
        :param instance: The model instance or class.
        :returns: The database-compatible value.
        """
        if value is None:
            return None
        if isinstance(value, np.ndarray):
            return value.tolist()
        return value

    @override
    def to_python_value(self, value: Any) -> np.ndarray | None:
        """
        Convert the database value to a Python-native value.

        :param value: The value from the database.
        :returns: The Python-native value (numpy array).
        """
        if value is None:
            return None
        return np.array(value)
