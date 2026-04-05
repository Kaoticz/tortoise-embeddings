from __future__ import annotations
import numpy as np
from tortoise import fields, models
from tortoise_embeddings.fields import VectorField, HalfVectorField, BinaryVectorField, SparseVectorField


class VectorModel(models.Model):
    """
    Model for testing all vector field types with fixed dimensions.
    """
    id: int = fields.IntField(primary_key=True)  # pyright: ignore[reportAssignmentType]
    vec: np.ndarray = VectorField(dimensions=3)  # type: ignore # pyright: ignore[reportAssignmentType]
    hvec: np.ndarray = HalfVectorField(dimensions=3)  # type: ignore # pyright: ignore[reportAssignmentType]
    bvec: str = BinaryVectorField(dimensions=3)  # type: ignore # pyright: ignore[reportAssignmentType]
    svec: object = SparseVectorField(dimensions=3)  # pyright: ignore[reportAssignmentType]


    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        """
        Meta options for VectorModel.
        """
        table: str = 'vector_model'
