from __future__ import annotations

from typing import TYPE_CHECKING, override, Any, final
from tortoise.backends.base_postgres.schema_generator import BasePostgresSchemaGenerator

if TYPE_CHECKING:  # pragma: nocoverage
    from tortoise import Model
    from tortoise.backends.base.schema_generator import BaseSchemaGenerator

class PostgresDDL(BasePostgresSchemaGenerator):
    """
    Postgres schema generator that injects vector extension creation.
    """
    @override
    def get_create_schema_sql(self, safe: bool = True) -> str:
        """
        Generate the SQL for creating the schema.

        :param safe: Whether to use IF NOT EXISTS.
        :returns: The generated SQL.
        """
        sql: str = super().get_create_schema_sql(safe)
        
        # Check if extension is already in the SQL (from _get_table_sql)
        if 'CREATE EXTENSION IF NOT EXISTS vector;' in sql:
            return sql

        # Check if any vector field is present
        from tortoise_embeddings.fields import VectorField, HalfVectorField, BinaryVector, SparseVector
        
        has_vector: bool = False
        from tortoise import Tortoise
        for app in Tortoise.apps.values():
            for model in app.values():
                if model._meta.db == self.client:
                    for field in model._meta.fields_map.values():
                        if isinstance(field, (VectorField, HalfVectorField, BinaryVector, SparseVector)):
                            has_vector = True
                            break
                if has_vector:
                    break
            if has_vector:
                break
        
        if has_vector:
            sql = 'CREATE EXTENSION IF NOT EXISTS vector;\n' + sql
        return sql

    @override
    def _get_table_sql(self, model: type[Model], safe: bool = True) -> dict[str, Any]:
        """
        Generate the SQL for creating a table.

        :param model: The model class.
        :param safe: Whether to use IF NOT EXISTS.
        :returns: A dictionary containing the generated SQL.
        """
        res: dict[str, Any] = super()._get_table_sql(model, safe)
        
        from tortoise_embeddings.fields import VectorField, HalfVectorField, BinaryVector, SparseVector
        has_vector: bool = False
        for field in model._meta.fields_map.values():
            if isinstance(field, (VectorField, HalfVectorField, BinaryVector, SparseVector)):
                has_vector = True
                break
        
        if has_vector:
            # We only add it if it's not there. 
            # Note: _get_table_sql is called for each table.
            # get_create_schema_sql combines these.
            if 'CREATE EXTENSION IF NOT EXISTS vector;' not in res['table_creation_string']:
                res['table_creation_string'] = 'CREATE EXTENSION IF NOT EXISTS vector;\n' + res['table_creation_string']
        
        return res

try:
    from aerich.ddl.postgres import PostgresDDL as AerichPostgresDDL
    
    @final
    class AerichVectorPostgresDDL(AerichPostgresDDL):
        """
        Aerich DDL class that supports pgvector.
        """
        schema_generator: BaseSchemaGenerator

        def __init__(self, client: Any) -> None:
            """
            Initialize the AerichVectorPostgresDDL.

            :param client: The database client.
            """
            super().__init__(client)
            # Ensure our schema generator is used
            self.schema_generator = PostgresDDL(client)

except ImportError:
    AerichVectorPostgresDDL = None # type: ignore
