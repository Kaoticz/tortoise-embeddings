from __future__ import annotations
from typing import Any, override
from .vector_field import VectorField
import numpy as np


try:
    from pgvector import HalfVector
except ImportError:
    HalfVector = None

class HalfVectorField(VectorField):
    """
    Field for pgvector's `halfvec` type.
    """

    def __init__(self, dimensions: int | None = None, **kwargs: Any) -> None:
        """
        Initialize the HalfVectorField.

        :param dimensions: The number of dimensions for the vector.
        :param kwargs: Additional arguments for the base Field class.
        """
        super().__init__(dimensions, **kwargs)
        if self.dimensions is not None:
            self.SQL_TYPE: str = f'halfvec({self.dimensions})'
        else:
            self.SQL_TYPE = 'halfvec'


    @override
    def get_db_field_types(self) -> dict[str, str]:
        """
        Return the database field types.

        :returns: A dictionary with the database dialect as key and the SQL type as value.
        """
        if self.dimensions is not None:
            return {'postgres': f'halfvec({self.dimensions})'}
        return {'postgres': 'halfvec'}

    @override
    def to_python_value(self, value: Any) -> np.ndarray | None:
        """
        Convert the database value to a Python-native value.

        :param value: The value from the database.
        :returns: The Python-native value (numpy array).
        """
        if value is None:
            return None
        if HalfVector is not None and isinstance(value, HalfVector):
            return np.array(value.to_numpy(), dtype=np.float32)
        return np.array(value, dtype=np.float32)
