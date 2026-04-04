# Tortoise Embeddings

Tortoise Embeddings adds `pgvector` support to TortoiseORM, enabling efficient vector storage and similarity search in PostgreSQL.

## Features

- **Four Vector Field Types:**
    - `VectorField`: Supports `vector` type.
    - `HalfVectorField`: Supports `halfvec` type.
    - `BinaryVector`: Supports `bit` type.
    - `SparseVector`: Supports `sparsevec` type.
- **Aerich Migration Support:** Automatically includes `CREATE EXTENSION IF NOT EXISTS vector;` in migrations.
- **Similarity Operations:**
    - **Custom Functions:** `L2Distance`, `CosineDistance`, `InnerProduct`, `L1Distance`, `HammingDistance`, `JaccardDistance`.
    - **Custom Filters:** Convenient filter suffixes like `__l2`, `__cosine`, `__inner`, etc.
- **Seamless Integration:** Works with `numpy` arrays and standard Python types.

## Installation

```bash
pip install tortoise-embeddings
```

Make sure you have `pgvector` installed in your PostgreSQL database.

## Usage

### Define Your Models

```python
from tortoise import models, fields
from tortoise_embeddings import VectorField, HalfVectorField, BinaryVector, SparseVector

class Item(models.Model):
    id = fields.IntField(pk=True)
    # Define a vector field with 3 dimensions
    embedding = VectorField(dimensions=3)
    # Support for other pgvector types
    half_embedding = HalfVectorField(dimensions=3)
    binary_embedding = BinaryVector(dimensions=4)
    sparse_embedding = SparseVector(dimensions=3)
```

### Initialize with Custom Client

To enable binary codecs and migration support, use the provided `AsyncpgDBClient`:

```python
from tortoise import Tortoise
import tortoise.backends.asyncpg
from tortoise_embeddings import AsyncpgDBClient

# Override the client class for the asyncpg backend
tortoise.backends.asyncpg.client_class = AsyncpgDBClient

async def init():
    await Tortoise.init(
        db_url='postgres://user:pass@host:port/db',
        modules={'models': ['your_models_module']}
    )
    await Tortoise.generate_schemas()
```

### Similarity Search

#### Using Custom Filters (Recommended)

```python
import numpy as np

target_vector = np.array([1.0, 0.0, 0.0])

# Find items where L2 distance is less than 0.5
items = await Item.filter(embedding__l2=(target_vector, 0.5))

# Find items where Cosine distance is less than 0.1
items = await Item.filter(embedding__cosine=(target_vector, 0.1))
```

#### Using Custom Functions

```python
from tortoise_embeddings.similarity import L2Distance

target_vector = [1.0, 0.0, 0.0]

# Annotate results with distance and order by it
items = await Item.all().annotate(
    dist=L2Distance(Item._meta.fields_map['embedding'], target_vector, alias="dist")
).order_by("dist")

for item in items:
    print(f"Item {item.id} has distance {item.dist}")
```

### Aerich Migrations

If you use `aerich`, simply use the `AerichVectorPostgresDDL` to ensure the `vector` extension is created:

```python
# In your project configuration
from tortoise_embeddings import AerichVectorPostgresDDL
# This is usually handled automatically if you use the patched AsyncpgDBClient
```

## Running Tests

Tests require a PostgreSQL database with the `pgvector` extension.

```bash
export PSQL_CONNECTION_STRING="postgres://user:pass@host:port/db"
export GEMINI_API_KEY="your_api_key" # Optional for Gemini integration tests
pytest tests/
```

## License

MIT
