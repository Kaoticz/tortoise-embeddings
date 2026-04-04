from __future__ import annotations
from typing import Any
from tortoise import fields, models
from tortoise_embeddings.fields import VectorField, HalfVectorField, BinaryVector, SparseVector

class VectorModel(models.Model):
    """
    Model for testing all vector field types.
    """
    id: Any = fields.IntField(pk=True)
    vec: Any = VectorField(dimensions=3)
    hvec: Any = HalfVectorField(dimensions=3)
    bvec: Any = BinaryVector(dimensions=3)
    svec: Any = SparseVector(dimensions=3)

    class Meta: # type: ignore
        """
        Meta options for VectorModel.
        """
        table: str = 'vector_model'

class GeminiModel(models.Model):
    """
    Model for testing Gemini embeddings.
    """
    id: Any = fields.IntField(primary_key=True)
    vec: Any = VectorField(dimensions=768)

    class Meta: # type: ignore
        """
        Meta options for GeminiModel.
        """
        table: str = 'gemini_model'
