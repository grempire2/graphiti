# How to View Facts in Neo4j Browser

The `fact` property is stored on the `RELATES_TO` relationships between Entity nodes.

## Method 1: Click on a Relationship

1. In Neo4j Browser, run a query to see relationships:
   ```cypher
   MATCH (n:Entity)-[r:RELATES_TO]->(m:Entity)
   RETURN n, r, m
   LIMIT 10
   ```

2. Click on any `RELATES_TO` relationship arrow in the graph visualization

3. In the details panel on the right, look for the **Properties** section

4. You should see properties including:
   - `fact` - The natural language description
   - `name` - The relation type (e.g., "CEO_OF")
   - `uuid` - The edge UUID
   - `episodes` - Array of episode UUIDs
   - etc.

## Method 2: Query Facts Directly

Run this query in Neo4j Browser to see all facts in a table:

```cypher
MATCH (n:Entity)-[e:RELATES_TO]->(m:Entity)
RETURN n.name AS source,
       m.name AS target,
       e.name AS relation,
       e.fact AS fact,
       e.uuid AS uuid
ORDER BY e.created_at DESC
LIMIT 20
```

## Method 3: View Facts for a Specific Entity

```cypher
MATCH (n:Entity {name: "Bob"})-[e:RELATES_TO]->(m:Entity)
RETURN n.name AS source,
       m.name AS target,
       e.name AS relation,
       e.fact AS fact
```

## Method 4: View All Properties of a Relationship

If the fact property isn't showing in the UI, you can view all properties:

```cypher
MATCH (n:Entity)-[e:RELATES_TO]->(m:Entity)
WHERE e.uuid = "3210729c-132b-4c22-b217-3a835d0f3265"
RETURN properties(e) AS all_properties
```

This will show you all properties including `fact`.

## Note

If you're using Neo4j Desktop or Neo4j Browser and the properties panel doesn't show `fact`, try:
- Expanding the relationship details panel
- Using the table view instead of graph view
- Running a query that explicitly returns `e.fact`

