from __future__ import annotations
import pytest
import numpy as np
from typing import Any
from tests.models import VectorModel
from tortoise_embeddings.similarity import L2Distance, InnerProduct, CosineDistance, L1Distance, HammingDistance, JaccardDistance

@pytest.mark.asyncio
async def test_vector_crud() -> None:
    """
    Test basic CRUD operations for all vector field types.
    """
    # Create
    vec1: list[float] = [1.0, 0.0, 0.0]
    hvec1: list[float] = [0.0, 1.0, 0.0]
    bvec1: str = '101'
    svec1: str = '{0:1}/3'
    
    obj: VectorModel = await VectorModel.create(
        vec=vec1,
        hvec=hvec1,
        bvec=bvec1,
        svec=svec1
    )
    assert obj.id is not None
    
    # Retrieve
    retrieved: VectorModel | None = await VectorModel.get(id=obj.id)
    assert retrieved is not None
    assert isinstance(retrieved.vec, np.ndarray)
    assert np.array_equal(retrieved.vec, np.array(vec1, dtype=np.float32))
    assert isinstance(retrieved.hvec, np.ndarray)
    assert np.array_equal(retrieved.hvec, np.array(hvec1, dtype=np.float32))
    assert retrieved.bvec == bvec1
    # SparseVector returns a SparseVector object
    assert '0: 1.0' in str(retrieved.svec)

@pytest.mark.asyncio
async def test_similarity_functions() -> None:
    """
    Test similarity operations using custom functions (annotate).
    """
    vec1: list[float] = [1.0, 0.0, 0.0]
    await VectorModel.create(vec=vec1, hvec=vec1, bvec='100', svec='{0:1}/3')
    
    # L2 Distance
    target: list[float] = [0.0, 1.0, 0.0]
    results: Any = await VectorModel.all().annotate(
        dist=L2Distance('vec', target)
    ).values('id', 'dist')
    assert results[0]['dist'] == pytest.approx(np.sqrt(2.0))
    
    # Cosine Distance
    results = await VectorModel.all().annotate(
        dist=CosineDistance('vec', target)
    ).values('id', 'dist')
    assert results[0]['dist'] == pytest.approx(1.0)
    
    # Hamming Distance (bit vectors)
    results = await VectorModel.all().annotate(
        dist=HammingDistance('bvec', '000')
    ).values('id', 'dist')
    assert results[0]['dist'] == 1.0

@pytest.mark.asyncio
async def test_similarity_filters() -> None:
    """
    Test similarity operations using custom filters.
    """
    vec1: list[float] = [1.0, 0.0, 0.0]
    await VectorModel.create(vec=vec1, hvec=vec1, bvec='100', svec='{0:1}/3')
    
    # Filter by L2 distance
    target: list[float] = [1.0, 0.1, 0.0]
    # threshold = 0.2, distance is 0.1
    results: list[VectorModel] = await VectorModel.filter(
        vec__l2=(target, 0.2)
    )
    assert len(results) >= 1
    
    # Filter by Cosine distance
    results = await VectorModel.filter(
        vec__cosine=(target, 0.05)
    )
    assert len(results) >= 1
    
    # Hamming distance
    results = await VectorModel.filter(
        bvec__hamming=('110', 1.5)
    )
    assert len(results) >= 1
