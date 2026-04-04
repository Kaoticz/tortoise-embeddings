from __future__ import annotations
import os
import pytest
import numpy as np
from typing import Any
from tests.models import GeminiModel

try:
    import google.generativeai as genai
except ImportError:
    genai = None # type: ignore

GEMINI_KEY: str | None = os.getenv('GEMINI_API_KEY')


@pytest.mark.skipif(genai is None, reason='google-generativeai not installed')
@pytest.mark.skipif(not GEMINI_KEY, reason='GEMINI_API_KEY not set')
async def test_gemini_embeddings() -> None:
    """
    Test generating vectors using Gemini API and storing them.
    """
    if genai is None:
        return
        
    genai.configure(api_key=GEMINI_KEY)
    
    # Find an embedding model
    models: Any = genai.list_models() # type: ignore
    model_name: str | None = None
    for m in models:
        if 'embedContent' in m.supported_generation_methods:
             model_name = m.name
             if 'embedding-001' in m.name or 'embedding-004' in m.name:
                 break
    
    if not model_name:
        model_name = 'models/embedding-001'
            
    text: str = 'TortoiseORM is an easy-to-use asyncio ORM inspired by Django.'
    try:
        result: Any = genai.embed_content( # type: ignore
            model=model_name,
            content=text,
            task_type='retrieval_document',
            output_dimensionality=768
        )
    except Exception:
        # Retry without output_dimensionality
        try:
             result = genai.embed_content( # type: ignore
                model=model_name,
                content=text,
                task_type='retrieval_document'
            )
        except Exception:
            pytest.skip(f'Failed to get embeddings from {model_name}')
            return
    
    embedding: list[float] = result['embedding']
    
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
