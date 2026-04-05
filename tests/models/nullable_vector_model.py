from __future__ import annotations
import numpy as np
from tortoise import fields, models
from tortoise_embeddings.fields import VectorField, HalfVectorField, BinaryVectorField, SparseVectorField


class NullableVectorModel(models.Model):
    """
    Model for testing all vector field types with fixed dimensions and nullability.
    """
    id: int = fields.IntField(primary_key=True)  # pyright: ignore[reportAssignmentType]
    vec: np.ndarray | None = VectorField(dimensions=3, null=True)  # type: ignore # pyright: ignore[reportAssignmentType]
    hvec: np.ndarray | None = HalfVectorField(dimensions=3, null=True)  # type: ignore # pyright: ignore[reportAssignmentType]
    bvec: str | None = BinaryVectorField(dimensions=3, null=True)  # type: ignore # pyright: ignore[reportAssignmentType]
    svec: object | None = SparseVectorField(dimensions=3, null=True)  # pyright: ignore[reportAssignmentType]


    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        """
        Meta options for NullableVectorModel.
        """
        table: str = 'nullable_vector_model'
