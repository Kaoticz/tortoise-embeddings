from __future__ import annotations
import os
import pytest
import numpy as np
from typing import Any, cast
from tests.models import GeminiModel

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None  # type: ignore
    types = None  # type: ignore


GEMINI_KEY: str | None = os.getenv('GEMINI_API_KEY')


@pytest.mark.skipif(genai is None, reason='google-genai not installed')
@pytest.mark.skipif(not GEMINI_KEY, reason='GEMINI_API_KEY not set')
async def test_gemini_embeddings() -> None:
    """
    Test generating vectors using Gemini API and storing them.
    """
    if genai is None or types is None:
        return
        
    client: Any = genai.Client(api_key=GEMINI_KEY)
    
    # Find an embedding model
    models: Any = client.models.list()
    model_name: str | None = None
    for m in models:
        # The new SDK has different attribute names, let's just try to find a known one or first one
        if 'embedding' in m.name:
             model_name = m.name
             if 'embedding-001' in m.name or 'embedding-004' in m.name:
                 break
    
    if not model_name:
        model_name = 'models/embedding-001'
            
    text: str = 'TortoiseORM is an easy-to-use asyncio ORM inspired by Django.'
    try:
        result: Any = client.models.embed_content(
            model=model_name,
            contents=text,
            config=types.EmbedContentConfig(
                task_type='RETRIEVAL_DOCUMENT',
                output_dimensionality=768
            )
        )
    except Exception:
        # Retry without output_dimensionality
        try:
             result = client.models.embed_content(
                model=model_name,
                contents=text,
                config=types.EmbedContentConfig(
                    task_type='RETRIEVAL_DOCUMENT'
                )
            )
        except Exception:
            pytest.skip(f'Failed to get embeddings from {model_name}')
            return
    
    # In google-genai, result is an EmbedContentResponse object
    embedding_values: Any = result.embeddings[0].values
    embedding: list[float] = cast(list[float], embedding_values)
    
    # Check dimensions
    if len(embedding) != 768:
        if len(embedding) > 768:
            embedding = embedding[:768]
        else:
            pytest.skip(f'Model {model_name} returned {len(embedding)} dimensions, expected 768')
            return
    
    # Save to database
    obj: GeminiModel = await GeminiModel.create(vec=embedding)
    
    # Retrieve and check
    retrieved: GeminiModel | None = await GeminiModel.get(id=obj.id)
    assert retrieved is not None
    assert isinstance(retrieved.vec, np.ndarray)
    assert retrieved.vec.shape == (768,)
    
    # Check similarity with itself
    results: list[GeminiModel] = await GeminiModel.filter(
        vec__cosine=(embedding, 0.1)
    )
    assert len(results) >= 1
    assert any(r.id == obj.id for r in results)
