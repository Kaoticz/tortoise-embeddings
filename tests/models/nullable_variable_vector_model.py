from __future__ import annotations
import numpy as np
from tortoise import fields, models
from tortoise_embeddings.fields import VectorField, HalfVectorField, BinaryVectorField, SparseVectorField


class NullableVariableVectorModel(models.Model):
    """
    Model for testing all vector field types without fixed dimensions and nullability.
    """
    id: int = fields.IntField(primary_key=True)  # pyright: ignore[reportAssignmentType]
    vec: np.ndarray | None = VectorField(null=True)  # type: ignore # pyright: ignore[reportAssignmentType]
    hvec: np.ndarray | None = HalfVectorField(null=True)  # type: ignore # pyright: ignore[reportAssignmentType]
    bvec: str | None = BinaryVectorField(null=True)  # type: ignore # pyright: ignore[reportAssignmentType]
    svec: object | None = SparseVectorField(null=True)  # pyright: ignore[reportAssignmentType]


    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        """
        Meta options for NullableVariableVectorModel.
        """
        table: str = 'nullable_variable_vector_model'
