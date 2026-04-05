from __future__ import annotations
from typing import Any, override, cast
from pypika_tortoise.terms import Term, Field as PypikaField
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
        if 'bit' in vector_type and isinstance(right, str) and BitString is not None:
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
            if 'bit' not in self._vector_type:
                right_sql = f'({right_sql})::{self._vector_type}'

        sql: str = f'({left_sql} {self._operator_symbol} {right_sql})'
        return format_alias_sql(sql, self.alias, ctx)
