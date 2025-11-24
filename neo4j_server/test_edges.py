"""
Extract facts from Graphiti knowledge graph.

This script extracts all facts (relationships between entities) from the graph.
Facts can be retrieved:
1. All facts in the database
2. Facts for a specific entity
3. Facts matching a search query
"""

import asyncio
import os
from dotenv import load_dotenv

from graphiti_core.driver.neo4j_driver import Neo4jDriver
from graphiti_core.graphiti import Graphiti
from graphiti_core.edges import EntityEdge
from graphiti_core.nodes import EpisodicNode, EpisodeType

load_dotenv()

# Get connection details from environment
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")


async def find_actor_for_fact(
    driver: Neo4jDriver, fact_text: str, episode_uuids: list[str]
) -> dict[str, str] | None:
    """
    Find which actor said a fact by searching through episode content.
    
    Returns a dict with 'actor' and 'message' if found, None otherwise.
    """
    if not episode_uuids:
        return None
    
    # Get episodes
    episodes = await EpisodicNode.get_by_uuids(driver, episode_uuids)
    
    for episode in episodes:
        # Only process message format episodes
        if episode.source != EpisodeType.message:
            continue
        
        # Parse message format: "actor: content"
        lines = episode.content.split('\n')
        for line in lines:
            # Extract actor and message
            parts = line.split(':', 1)
            if len(parts) != 2:
                continue
            
            actor = parts[0].strip()
            message = parts[1].strip()
            
            # Try multiple matching strategies:
            # 1. Exact fact text in message (case-insensitive)
            if fact_text.lower() in message.lower():
                return {'actor': actor, 'message': message, 'episode_uuid': episode.uuid}
            
            # 2. Extract key words from fact (non-stop words) and check if they're in message
            fact_words = set(word.lower() for word in fact_text.split() if len(word) > 3)
            message_words = set(word.lower() for word in message.split())
            # If most key words from fact are in message, it's likely a match
            if fact_words and len(fact_words.intersection(message_words)) >= len(fact_words) * 0.5:
                return {'actor': actor, 'message': message, 'episode_uuid': episode.uuid}
    
    # If no match found, return the first message from the episode as fallback
    for episode in episodes:
        if episode.source == EpisodeType.message:
            lines = episode.content.split('\n')
            for line in lines:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    actor = parts[0].strip()
                    message = parts[1].strip()
                    return {'actor': actor, 'message': message, 'episode_uuid': episode.uuid}
    
    return None


async def get_all_facts(driver: Neo4jDriver, limit: int | None = None) -> list[dict]:
    """
    Extract all facts from the database.

    Returns a list of dictionaries containing fact information.
    """
    if limit:
        query = """
        MATCH (n:Entity)-[e:RELATES_TO]->(m:Entity)
        RETURN n.name as source_name, 
               m.name as target_name,
               e.name as relation_type,
               e.fact as fact,
               e.uuid as uuid,
               e.episodes as episodes,
               e.valid_at as valid_at,
               e.invalid_at as invalid_at,
               e.created_at as created_at
        ORDER BY e.created_at DESC, e.uuid
        LIMIT $limit
        """
        records, _, _ = await driver.execute_query(query, limit=limit)
    else:
        query = """
        MATCH (n:Entity)-[e:RELATES_TO]->(m:Entity)
        RETURN n.name as source_name, 
               m.name as target_name,
               e.name as relation_type,
               e.fact as fact,
               e.uuid as uuid,
               e.episodes as episodes,
               e.valid_at as valid_at,
               e.invalid_at as invalid_at,
               e.created_at as created_at
        ORDER BY e.created_at DESC, e.uuid
        """
        records, _, _ = await driver.execute_query(query)

    facts = []
    for record in records:
        facts.append(
            {
                "source": record.get("source_name", "Unknown"),
                "target": record.get("target_name", "Unknown"),
                "relation": record.get("relation_type", "UNKNOWN"),
                "fact": record.get("fact", ""),
                "uuid": record.get("uuid", ""),
                "episodes": record.get("episodes", []),
                "valid_at": record.get("valid_at"),
                "invalid_at": record.get("invalid_at"),
                "created_at": record.get("created_at"),
            }
        )

    return facts


async def get_facts_for_entity(
    driver: Neo4jDriver, entity_uuid: str | None = None, entity_name: str | None = None
) -> list[EntityEdge]:
    """
    Get all facts (edges) connected to a specific entity.

    Either entity_uuid or entity_name must be provided.
    """
    if not entity_uuid and not entity_name:
        raise ValueError("Either entity_uuid or entity_name must be provided")

    # If entity_name is provided, find the entity first
    if entity_name and not entity_uuid:
        # Query database directly to find entity by name
        query = """
        MATCH (n:Entity {name: $name})
        RETURN n.uuid as uuid
        LIMIT 1
        """
        records, _, _ = await driver.execute_query(query, name=entity_name)
        if not records:
            return []
        entity_uuid = records[0]["uuid"]

    # Ensure we have a valid UUID
    if not entity_uuid:
        return []

    # Get all edges connected to this entity
    edges = await EntityEdge.get_by_node_uuid(driver, entity_uuid)
    return edges


async def search_facts(
    graphiti: Graphiti,
    query: str,
    num_results: int = 10,
    center_node_uuid: str | None = None,
) -> list[EntityEdge]:
    """
    Search for facts using a query string.

    Uses Graphiti's hybrid search to find relevant facts.
    """
    edges = await graphiti.search(
        query=query,
        center_node_uuid=center_node_uuid,
        num_results=num_results,
    )
    return edges


async def display_facts(
    facts: list[dict] | list[EntityEdge],
    title: str = "FACTS",
    driver: Neo4jDriver | None = None,
    show_actor: bool = True,  # Default to True to show who said each fact
    filter_actor: str | None = None,  # Filter facts by actor (e.g., "user")
):
    """Display facts in a readable format."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

    if not facts:
        print("\nNo facts found.")
        return

    # Filter facts by actor if requested
    filtered_facts = []
    if filter_actor and driver:
        print(f"\nFiltering facts said by: {filter_actor}...")
        for fact_data in facts:
            # Handle both dict and EntityEdge formats
            if isinstance(fact_data, EntityEdge):
                fact_text = fact_data.fact
                episodes = fact_data.episodes or []
            else:
                fact_text = fact_data.get("fact", "")
                episodes = fact_data.get("episodes", [])
            
            # Check if this fact was said by the specified actor
            if episodes:
                actor_info = await find_actor_for_fact(driver, fact_text, episodes)
                if actor_info and actor_info['actor'].lower() == filter_actor.lower():
                    filtered_facts.append(fact_data)
        facts = filtered_facts
    
    if not facts:
        print(f"\nNo facts found{' said by ' + filter_actor if filter_actor else ''}.")
        return

    print(f"\nFound {len(facts)} fact(s):\n")

    for idx, fact_data in enumerate(facts, 1):
        # Handle both dict and EntityEdge formats
        if isinstance(fact_data, EntityEdge):
            source = "Unknown"
            target = "Unknown"
            relation = fact_data.name
            fact_text = fact_data.fact
            uuid = fact_data.uuid
            episodes = fact_data.episodes or []
        else:
            source = fact_data.get("source", "Unknown")
            target = fact_data.get("target", "Unknown")
            relation = fact_data.get("relation", "UNKNOWN")
            fact_text = fact_data.get("fact", "")
            uuid = fact_data.get("uuid", "")
            episodes = fact_data.get("episodes", [])

        print(f"{idx}. {fact_text}")
        print(f"   {source} --[{relation}]--> {target}")
        print(f"   UUID: {uuid}")
        if episodes:
            print(f"   Referenced by {len(episodes)} episode(s)")
        
        # Show actor if requested and driver is available
        if show_actor and driver and episodes:
            actor_info = await find_actor_for_fact(driver, fact_text, episodes)
            if actor_info:
                print(f"   Said by: {actor_info['actor']}")
                print(f"   Original message: {actor_info['message'][:100]}{'...' if len(actor_info['message']) > 100 else ''}")
        
        print()


async def extract_all_facts(
    driver: Neo4jDriver,
    limit: int | None = None,
    show_actor: bool = True,
    filter_actor: str | None = None,
):
    """Extract and display all facts from the database."""
    print("\nExtracting all facts from database...")
    facts = await get_all_facts(driver, limit=limit)
    title = f"ALL FACTS{' (said by ' + filter_actor + ')' if filter_actor else ''}"
    await display_facts(
        facts, title=title, driver=driver, show_actor=show_actor, filter_actor=filter_actor
    )
    return facts


async def extract_facts_for_entity(
    driver: Neo4jDriver,
    entity_name: str | None = None,
    entity_uuid: str | None = None,
    show_actor: bool = True,
):
    """Extract and display facts for a specific entity."""
    if not entity_name and not entity_uuid:
        print("Error: entity_name or entity_uuid must be provided")
        return []

    identifier = entity_name or entity_uuid
    print(f"\nExtracting facts for entity: {identifier}...")

    edges = await get_facts_for_entity(
        driver, entity_uuid=entity_uuid, entity_name=entity_name
    )

    # Convert EntityEdge to dict format for display
    facts = []
    for edge in edges:
        # Get source and target node names
        from graphiti_core.nodes import EntityNode

        source_node = await EntityNode.get_by_uuid(driver, edge.source_node_uuid)
        target_node = await EntityNode.get_by_uuid(driver, edge.target_node_uuid)

        facts.append(
            {
                "source": source_node.name if source_node else "Unknown",
                "target": target_node.name if target_node else "Unknown",
                "relation": edge.name,
                "fact": edge.fact,
                "uuid": edge.uuid,
                "episodes": edge.episodes or [],
            }
        )

    await display_facts(
        facts, title=f"FACTS FOR ENTITY: {identifier}", driver=driver, show_actor=show_actor
    )
    return facts


async def extract_facts_by_search(
    graphiti: Graphiti, query: str, num_results: int = 10
):
    """Extract and display facts matching a search query."""
    print(f"\nSearching for facts matching: '{query}'...")

    edges = await search_facts(graphiti, query, num_results=num_results)

    # Convert EntityEdge to dict format for display
    facts = []
    for edge in edges:
        # Get source and target node names
        from graphiti_core.nodes import EntityNode

        source_node = await EntityNode.get_by_uuid(
            graphiti.driver, edge.source_node_uuid
        )
        target_node = await EntityNode.get_by_uuid(
            graphiti.driver, edge.target_node_uuid
        )

        facts.append(
            {
                "source": source_node.name if source_node else "Unknown",
                "target": target_node.name if target_node else "Unknown",
                "relation": edge.name,
                "fact": edge.fact,
                "uuid": edge.uuid,
                "episodes": edge.episodes or [],
            }
        )

    await display_facts(facts, title=f"SEARCH RESULTS: '{query}'")
    return facts


async def main():
    """Main function to extract facts."""
    import sys

    print("Graphiti Fact Extraction")
    print("=" * 80)

    # Connect to database
    driver = Neo4jDriver(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    graphiti = None  # Only create when needed (for search mode)

    try:
        # Check command line arguments for extraction mode
        if len(sys.argv) > 1:
            mode = sys.argv[1].lower()

            if mode == "all":
                # Extract all facts - no Graphiti needed
                # Check for --no-actor flag to hide actor info
                show_actor = "--no-actor" not in sys.argv
                # Check for --actor flag to filter by actor
                filter_actor = None
                if "--actor" in sys.argv:
                    actor_idx = sys.argv.index("--actor")
                    if actor_idx + 1 < len(sys.argv):
                        filter_actor = sys.argv[actor_idx + 1]
                # Get limit (skip --no-actor and --actor if present)
                limit = None
                for arg in sys.argv[2:]:
                    if arg not in ["--no-actor", "--actor"] and not (
                        "--actor" in sys.argv
                        and sys.argv.index("--actor") > 0
                        and arg == sys.argv[sys.argv.index("--actor") + 1]
                    ):
                        try:
                            limit = int(arg)
                        except ValueError:
                            pass
                        break
                await extract_all_facts(
                    driver, limit=limit, show_actor=show_actor, filter_actor=filter_actor
                )

            elif mode == "entity":
                # Extract facts for a specific entity - no Graphiti needed
                if len(sys.argv) < 3:
                    print("Error: entity name or UUID required")
                    print("Usage: python test_edges.py entity <entity_name_or_uuid>")
                    return
                entity_identifier = sys.argv[2]
                # Try as UUID first, then as name
                if len(entity_identifier) == 36:  # UUID format
                    await extract_facts_for_entity(
                        driver, entity_uuid=entity_identifier
                    )
                else:
                    await extract_facts_for_entity(
                        driver, entity_name=entity_identifier
                    )

            elif mode == "search":
                # Search for facts - Graphiti needed
                if len(sys.argv) < 3:
                    print("Error: search query required")
                    print("Usage: python test_edges.py search <query> [num_results]")
                    return
                # Only create Graphiti when needed for search
                if graphiti is None:
                    graphiti = Graphiti(
                        uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD
                    )
                query = sys.argv[2]
                num_results = int(sys.argv[3]) if len(sys.argv) > 3 else 10
                await extract_facts_by_search(graphiti, query, num_results=num_results)

            else:
                print(f"Unknown mode: {mode}")
                print("\nAvailable modes:")
                print(
                    "  all [limit]              - Extract all facts (optionally limit results)"
                )
                print(
                    "  entity <name_or_uuid>    - Extract facts for a specific entity"
                )
                print("  search <query> [limit]   - Search for facts matching a query")
        else:
            # Default: extract all facts - no Graphiti needed
            print("\nNo mode specified. Extracting all facts...")
            print("Usage examples:")
            print("  python test_edges.py all                    # All facts (with actor info)")
            print("  python test_edges.py all 100                 # First 100 facts")
            print("  python test_edges.py all --actor user       # Facts said by 'user'")
            print("  python test_edges.py all --no-actor          # Hide actor info")
            print("  python test_edges.py entity <name_or_uuid>   # Facts for entity")
            print("  python test_edges.py search <query>          # Search facts")
            print()
            await extract_all_facts(driver)

    finally:
        try:
            await driver.close()
        except Exception as e:
            # Ignore connection errors during cleanup
            if "defunct connection" not in str(e).lower():
                print(f"\nWarning: Error closing driver: {e}")
        
        if graphiti is not None:
            try:
                await graphiti.close()
            except Exception as e:
                # Ignore connection errors during cleanup
                if "defunct connection" not in str(e).lower():
                    print(f"\nWarning: Error closing graphiti: {e}")


if __name__ == "__main__":
    asyncio.run(main())
