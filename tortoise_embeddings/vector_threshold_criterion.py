from __future__ import annotations
from typing import Any, override, cast
from pypika_tortoise.terms import Term, Criterion, Field as PypikaField
from pypika_tortoise.context import SqlContext

try:
    from asyncpg.pgproto.types import BitString
except ImportError:
    BitString = None


class VectorThresholdCriterion(Criterion):
    """
    Criterion representing a vector distance compared against a threshold.
    """
    _target: Term
    _field: Term
    _distance_op: str
    _compare_op: str
    _threshold: Term
    _vector_type: str

    def __init__(self, field: Any, distance_op: str, target: Any, compare_op: str, threshold: Any, alias: str | None = None, vector_type: str = 'vector') -> None:
        """
        Initialize the VectorThresholdCriterion.

        :param field: The vector field.
        :param distance_op: The vector distance operator.
        :param target: The target vector.
        :param compare_op: The comparison operator (e.g., <).
        :param threshold: The distance threshold.
        :param alias: Optional alias.
        :param vector_type: The pgvector type for casting.
        """
        super().__init__(alias=alias)
        if isinstance(field, str):
            self._field = PypikaField(field)
        elif hasattr(field, 'model_field_name'):
            self._field = PypikaField(field.model_field_name)
        else:
            self._field = field if isinstance(field, Term) else Term.wrap_constant(field)

        if 'bit' in vector_type and isinstance(target, str) and BitString is not None:
            self._target = Term.wrap_constant(BitString(cast(Any, target)))
        else:
            self._target = target if isinstance(target, Term) else Term.wrap_constant(target)

        self._distance_op = distance_op
        self._compare_op = compare_op
        self._threshold = threshold if isinstance(threshold, Term) else Term.wrap_constant(threshold)
        self._vector_type = vector_type

    @override
    def get_sql(self, ctx: SqlContext) -> str:
        """
        Generate the SQL for the criterion.

        :param ctx: The SQL context.
        :returns: The generated SQL string.
        """
        field_sql: str = self._field.get_sql(ctx)
        target_sql: str = self._target.get_sql(ctx)
        threshold_sql: str = self._threshold.get_sql(ctx)

        if not isinstance(self._target, PypikaField):
            # Remove explicit cast for bit to avoid length mismatch issue
            if 'bit' not in self._vector_type:
                target_sql = f'({target_sql})::{self._vector_type}'

        return f'{field_sql} {self._distance_op} {target_sql} {self._compare_op} {threshold_sql}'
