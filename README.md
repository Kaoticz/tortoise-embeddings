# Tortoise Embeddings

Tortoise Embeddings adds `pgvector` support to TortoiseORM, enabling efficient vector storage and similarity search in PostgreSQL.

## Features

- **Four Vector Field Types:**
    - `VectorField`: Supports `vector` type.
    - `HalfVectorField`: Supports `halfvec` type.
    - `BinaryVector`: Supports `bit` type.
    - `SparseVector`: Supports `sparsevec` type.
- **Aerich Migration Support:** Automatically includes vector-based types from your models into the migration scripts.
- **Similarity Operations:**
    - **Custom Functions:** `L2Distance`, `CosineDistance`, `InnerProduct`, `L1Distance`, `HammingDistance`, `JaccardDistance`.
    - **Custom Filters:** Convenient filter suffixes -  `__l2`, `__cosine`, `__inner`, `__l1`, `__hamming`, and `__jaccard`.
- Works with `numpy` arrays and standard Python types.

## Installation

```bash
pip install tortoise-embeddings
```

Make sure you have `pgvector` installed in your PostgreSQL database.

## Usage

### Define Your Models

```python
from tortoise.models import Model
from tortoise.fields import IntField
from tortoise_embeddings import VectorField, HalfVectorField, BinaryVectorField, SparseVectorField

class Item(Model):
    id = IntField(primary_key=True)
    # Define a vector field with 3 dimensions
    embedding = VectorField(dimensions=3)
    # Support for other pgvector types
    half_embedding = HalfVectorField(dimensions=3)
    binary_embedding = BinaryVectorField(dimensions=4)
    sparse_embedding = SparseVectorField(dimensions=3)
```

### Initialize with Custom Client

To enable binary codecs and migration support, use the provided `AsyncpgDBClient`:

```python
from tortoise import Tortoise
import tortoise.backends.asyncpg
from tortoise_embeddings import VectorAsyncpgDBClient

# Override the client class for the asyncpg backend
tortoise.backends.asyncpg.client_class = VectorAsyncpgDBClient

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
import numpy

target_vector = numpy.array([1.0, 0.0, 0.0])

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
# This is usually handled automatically if you use the VectorAsyncpgDBClient
```
# Development setup

Set the following environment variables:

| Variable                       | Description                                   | How to get?                                                             |
|--------------------------------|-----------------------------------------------|-------------------------------------------------------------------------|
| PSQL_CONNECTION_STRING         | A connection string to a PostgreSQL database. | `postgres://user:password@host:port/database`                           |
| GEMINI_API_KEY                 | An API key to Google GenAI. (optional)        | Go to [aistudio.google.com](aistudio.google.com) and create an API key. |

## Dependencies:

### Internal

- None

### External

- tortoise-orm>=0.25.0,<1.0.0
- aerich>=0.9.0 
- asyncpg>=0.31.0
- pgvector>=0.4.0
- numpy>=2.4.0

## Running Tests

Tests require a PostgreSQL database with the `pgvector` extension.

```bash
export PSQL_CONNECTION_STRING="postgres://user:password@host:port/database"
export GEMINI_API_KEY="your_api_key" # Optional for Gemini integration tests
pytest tests/
```