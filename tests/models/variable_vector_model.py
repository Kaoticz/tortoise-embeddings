from __future__ import annotations
import numpy as np
from tortoise import fields, models
from tortoise_embeddings.fields import VectorField, HalfVectorField, BinaryVectorField, SparseVectorField


class VariableVectorModel(models.Model):
    """
    Model for testing all vector field types without fixed dimensions.
    """
    id: int = fields.IntField(primary_key=True)  # pyright: ignore[reportAssignmentType]
    vec: np.ndarray = VectorField()  # type: ignore # pyright: ignore[reportAssignmentType]
    hvec: np.ndarray = HalfVectorField()  # type: ignore # pyright: ignore[reportAssignmentType]
    bvec: str = BinaryVectorField()  # type: ignore # pyright: ignore[reportAssignmentType]
    svec: object = SparseVectorField()  # pyright: ignore[reportAssignmentType]


    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        """
        Meta options for VariableVectorModel.
        """
        table: str = 'variable_vector_model'
