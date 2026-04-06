from __future__ import annotations
from typing import Any
from tortoise import Model
from tortoise.fields import IntField
from tortoise_embeddings.fields import VectorField


class ModelA(Model):
    """
    Test model A for successive migrations.
    """
    id: int = IntField(primary_key=True)  # pyright: ignore[reportAssignmentType]
    vec: Any = VectorField(dimensions=3)  # pyright: ignore[reportAssignmentType]

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        table: str = 'model_a'
        app: str = 'models'


class ModelB(Model):
    """
    Test model B for successive migrations.
    """
    id: int = IntField(primary_key=True)  # pyright: ignore[reportAssignmentType]
    vec: Any = VectorField(dimensions=3)  # pyright: ignore[reportAssignmentType]

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        table: str = 'model_b'
        app: str = 'models'
