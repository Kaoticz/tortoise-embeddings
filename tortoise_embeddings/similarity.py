from __future__ import annotations
from typing import Any, Callable
from pypika_tortoise.terms import Term, Criterion
from .vector_distance import VectorDistance
from .vector_threshold_criterion import VectorThresholdCriterion


def L2Distance(field: Any, value: Any, alias: str | None = None) -> VectorDistance:
    """
    L2 distance operator (<->).

    :param field: The vector field.
    :param value: The target vector.
    :param alias: Optional alias.
    :returns: A VectorDistance instance.
    """
    return VectorDistance(field, '<->', value, alias=alias)


def InnerProduct(field: Any, value: Any, alias: str | None = None) -> VectorDistance:
    """
    Inner product operator (<#>).

    :param field: The vector field.
    :param value: The target vector.
    :param alias: Optional alias.
    :returns: A VectorDistance instance.
    """
    return VectorDistance(field, '<#>', value, alias=alias)


def CosineDistance(field: Any, value: Any, alias: str | None = None) -> VectorDistance:
    """
    Cosine distance operator (<=>).

    :param field: The vector field.
    :param value: The target vector.
    :param alias: Optional alias.
    :returns: A VectorDistance instance.
    """
    return VectorDistance(field, '<=>', value, alias=alias)


def L1Distance(field: Any, value: Any, alias: str | None = None) -> VectorDistance:
    """
    L1 distance operator (<+>).

    :param field: The vector field.
    :param value: The target vector.
    :param alias: Optional alias.
    :returns: A VectorDistance instance.
    """
    return VectorDistance(field, '<+>', value, alias=alias)


def HammingDistance(field: Any, value: Any, alias: str | None = None) -> VectorDistance:
    """
    Hamming distance operator (<~>).

    :param field: The vector field.
    :param value: The target vector.
    :param alias: Optional alias.
    :returns: A VectorDistance instance.
    """
    return VectorDistance(field, '<~>', value, alias=alias, vector_type='bit')


def JaccardDistance(field: Any, value: Any, alias: str | None = None) -> VectorDistance:
    """
    Jaccard distance operator (%).

    :param field: The vector field.
    :param value: The target vector.
    :param alias: Optional alias.
    :returns: A VectorDistance instance.
    """
    return VectorDistance(field, '%', value, alias=alias)


def create_vector_operator(distance_op: str, compare_op: str, vector_type: str = 'vector') -> Callable[[Term, Any], Criterion]:
    """
    Create a filter operator for vector distance comparison.

    :param distance_op: The vector distance operator.
    :param compare_op: The comparison operator.
    :param vector_type: The pgvector type for casting.
    :returns: A function that takes a field and a value and returns a Criterion.
    """
    def operator(field: Term, value: Any) -> Criterion:
        if isinstance(value, (list, tuple)) and len(value) == 2:
            target, threshold = value
        else:
            target = value
            threshold = 0.0
        
        return VectorThresholdCriterion(field, distance_op, target, compare_op, threshold, vector_type=vector_type)
    return operator
