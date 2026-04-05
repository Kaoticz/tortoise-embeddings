from __future__ import annotations
import numpy as np
from tortoise import fields, models
from tortoise_embeddings.fields import VectorField


class GeminiModel(models.Model):
    """
    Model for testing Gemini embeddings.
    """
    id: int = fields.IntField(primary_key=True)  # pyright: ignore[reportAssignmentType]
    vec: np.ndarray = VectorField(dimensions=768)  # type: ignore # pyright: ignore[reportAssignmentType]


    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        """
        Meta options for GeminiModel.
        """
        table: str = 'gemini_model'
