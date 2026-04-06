from __future__ import annotations
from typing import Any
from tortoise import fields, models
from tortoise_embeddings.fields import VectorField


class MigrationTestModel(models.Model):
    """
    Model for testing migration injection logic.
    """
    id: int = fields.IntField(primary_key=True)  # pyright: ignore[reportAssignmentType]
    vec: Any = VectorField(dimensions=3)  # pyright: ignore[reportAssignmentType]

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        """
        Meta options for MigrationTestModel.
        """
        table: str = 'migration_test_model'
        app: str = 'models'
