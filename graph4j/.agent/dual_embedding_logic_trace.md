# Dual Embedding Logic Trace - Verification

## Complete Flow Analysis

### Step 1: Fast Extraction & Save
```python
fast_result = await fast_embedding_client.add_episode(...)
```

**What happens:**
1. LLM extracts entities, relationships, attributes
2. Fast embeddings generated for nodes/edges
3. Saved to fast database
4. Returns `AddEpisodeResults` with:
   - `fast_result.nodes` → have fast embeddings ✅
   - `fast_result.edges` → have fast embeddings ✅
   - `fast_result.episode` → episode data
   - `fast_result.episodic_edges` → episodic edges

**State after Step 1:**
- Fast DB: Has nodes with fast embeddings ✅
- `fast_result` object: Nodes have fast embeddings ✅

---

### Step 2: Default Save with Different Embeddings
```python
default_result = await embedding_client.save_episode_results(
    episode=fast_result.episode,
    nodes=fast_result.nodes,  # Still have fast embeddings
    edges=fast_result.edges,  # Still have fast embeddings
    episodic_edges=fast_result.episodic_edges,
    embedder=embedding_client.embedder,
    clear_embeddings=True,  # KEY: Clear on COPIES
)
```

**What happens inside `save_episode_results()`:**

1. **Deep copy** (line 895-898):
   ```python
   nodes_copy = copy.deepcopy(nodes)  # Copies nodes WITH fast embeddings
   edges_copy = copy.deepcopy(edges)  # Copies edges WITH fast embeddings
   ```

2. **Clear embeddings on COPIES** (line 900-904):
   ```python
   if clear_embeddings:  # True
       for node in nodes_copy:  # Only affects COPIES!
           node.name_embedding = None
       for edge in edges_copy:  # Only affects COPIES!
           edge.fact_embedding = None
   ```

3. **Save to database** (line 907-914):
   ```python
   await add_nodes_and_edges_bulk(
       embedding_client.driver,
       [episode_copy],
       episodic_edges_copy,
       nodes_copy,  # Have None embeddings
       edges_copy,  # Have None embeddings
       embedding_client.embedder,  # Default embedder
   )
   ```

4. **Inside `add_nodes_and_edges_bulk()`** (bulk_utils.py line 168-169):
   ```python
   for node in entity_nodes:  # nodes_copy
       if node.name_embedding is None:  # True!
           await node.generate_name_embedding(embedder)  # Default embeddings!
   ```

5. **Return results**:
   ```python
   return AddEpisodeResults(
       nodes=nodes_copy,  # Now have default embeddings ✅
       edges=edges_copy,  # Now have default embeddings ✅
       ...
   )
   ```

**State after Step 2:**
- Fast DB: Still has nodes with fast embeddings ✅
- Default DB: Has nodes with default embeddings ✅
- `fast_result` object: Nodes STILL have fast embeddings ✅ (not mutated!)
- `default_result` object: Nodes have default embeddings ✅

---

## Final State Verification

### Fast Database
- Episode saved ✅
- Nodes with fast embeddings ✅
- Edges with fast embeddings ✅

### Default Database
- Same episode saved ✅
- Same nodes with default embeddings ✅
- Same edges with default embeddings ✅

### Return Values
- `fast_result.nodes[0].name_embedding` → Fast embedding vector ✅
- `default_result.nodes[0].name_embedding` → Default embedding vector ✅
- Both point to same logical entity, different embeddings ✅

---

## LLM Call Count

1. **Entity extraction**: 1× (in fast_embedding_client.add_episode)
2. **Relationship extraction**: 1× (in fast_embedding_client.add_episode)
3. **Attribute extraction**: 1× (in fast_embedding_client.add_episode)

**Total LLM calls**: 3 (all in Step 1)

**Embedding generation calls**:
- Fast embeddings: 1× (in Step 1)
- Default embeddings: 1× (in Step 2)

**Total**: 1× LLM extraction, 2× embedding generation

---

## Critical Success Factors

✅ **Deep copy before clearing**: Prevents mutation of `fast_result`
✅ **Clear on copies only**: `fast_result` remains intact
✅ **Automatic regeneration**: `add_nodes_and_edges_bulk` regenerates None embeddings
✅ **Separate return objects**: Each has correct embeddings for its database

---

## Potential Issues (None Found)

❌ ~~Mutation of fast_result~~ → Fixed with deep copy
❌ ~~Double LLM extraction~~ → Only happens once
❌ ~~Wrong embeddings in database~~ → Each DB gets correct embeddings
❌ ~~Wrong embeddings in return values~~ → Each result has correct embeddings

---

## Conclusion

**YES, THIS WORKS!** ✅

The logic is sound:
1. Extract once with fast client
2. Deep copy the results
3. Clear embeddings on the copies
4. Save copies to default database (embeddings regenerate automatically)
5. Return both results with correct embeddings

No mutation bugs, no double extraction, correct embeddings in both databases.
