from __future__ import annotations
from typing import Any, override, Callable, cast
from pypika_tortoise.terms import Term, Criterion, Field as PypikaField
from pypika_tortoise.context import SqlContext
from pypika_tortoise.utils import format_alias_sql

try:
    from asyncpg.pgproto.types import BitString
except ImportError:
    BitString = None

class VectorDistance(Term):
    """
    Term representing the distance between two vectors.
    """
    def __init__(self, left: Any, operator_symbol: str, right: Any, alias: str | None = None, vector_type: str = 'vector') -> None:
        """
        Initialize the VectorDistance term.

        :param left: The left vector (field or constant).
        :param operator_symbol: The pgvector operator symbol (e.g., <->).
        :param right: The right vector (field or constant).
        :param alias: Optional alias for the term.
        :param vector_type: The pgvector type for casting (default 'vector').
        """
        super().__init__(alias=alias)
        
        self._left: Term
        if isinstance(left, str):
            self._left = PypikaField(left)
        elif hasattr(left, 'model_field_name'):
            self._left = PypikaField(left.model_field_name)
        else:
            self._left = left if isinstance(left, Term) else Term.wrap_constant(left)
            
        self._right: Term
        if vector_type == 'bit' and isinstance(right, str) and BitString is not None:
             self._right = Term.wrap_constant(BitString(cast(Any, right)))
        else:
             self._right = right if isinstance(right, Term) else Term.wrap_constant(right)
             
        self._operator_symbol: str = operator_symbol
        self._vector_type: str = vector_type

    @override
    def get_sql(self, ctx: SqlContext) -> str:
        """
        Generate the SQL for the vector distance.

        :param ctx: The SQL context.
        :returns: The generated SQL string.
        """
        left_sql: str = self._left.get_sql(ctx)
        right_sql: str = self._right.get_sql(ctx)
        
        # Always cast if not a field to be safe
        if not isinstance(self._left, PypikaField):
             left_sql = f'({left_sql})::{self._vector_type}'
        if not isinstance(self._right, PypikaField):
             # Remove explicit cast for bit to avoid length mismatch issue
             if self._vector_type != 'bit':
                 right_sql = f'({right_sql})::{self._vector_type}'
             
        sql: str = f'({left_sql} {self._operator_symbol} {right_sql})'
        return format_alias_sql(sql, self.alias, ctx)

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

        if vector_type == 'bit' and isinstance(target, str) and BitString is not None:
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
             if self._vector_type != 'bit':
                 target_sql = f'({target_sql})::{self._vector_type}'
             
        return f'{field_sql} {self._distance_op} {target_sql} {self._compare_op} {threshold_sql}'

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
