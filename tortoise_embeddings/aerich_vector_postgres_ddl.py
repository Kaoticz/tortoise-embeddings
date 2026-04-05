from __future__ import annotations

from typing import TYPE_CHECKING, Any, final
from .postgres_ddl import PostgresDDL

try:
    from aerich.ddl.postgres import PostgresDDL as AerichPostgresDDL
    
    if TYPE_CHECKING:
        from tortoise.backends.base.schema_generator import BaseSchemaGenerator
        from tortoise.backends.base_postgres.client import BasePostgresClient

    @final
    class AerichVectorPostgresDDL(AerichPostgresDDL):
        """
        Aerich DDL class that supports pgvector.
        """
        schema_generator: BaseSchemaGenerator

        def __init__(self, client: BasePostgresClient) -> None:
            """
            Initialize the AerichVectorPostgresDDL.

            :param client: The database client.
            """
            super().__init__(client)
            # Ensure our schema generator is used
            self.schema_generator = PostgresDDL(client)

except ImportError:
    AerichVectorPostgresDDL = None  # type: ignore
