"""
Graph Handler - Neo4j Integration for PDF Relationship-Based Search
Manages graph database operations for PDF entity relationships
Company: Sepia ML | Developer: Shreyash Shankarrao Jadhav
"""
from neo4j import GraphDatabase
from typing import List, Dict, Optional
import os
import json
from datetime import datetime


class GraphHandler:
    """Handles Neo4j graph database operations for PDFs"""
    
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        """
        Initialize Neo4j Graph Handler
        
        Args:
            uri: Neo4j connection URI (default: from env or bolt://localhost:7687)
            user: Neo4j username (default: from env or neo4j)
            password: Neo4j password (default: from env or password)
        """
        # Get connection details from environment or use defaults
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")
        
        # Initialize driver
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            print("✅ Neo4j connected successfully!")
        except Exception as e:
            print(f"⚠️  Neo4j connection failed: {e}")
            print("   Graph features will be disabled. Please check Neo4j configuration.")
            self.driver = None
    
    def is_connected(self) -> bool:
        """Check if Neo4j is connected"""
        if not self.driver:
            return False
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            return True
        except:
            return False
    
    def create_pdf_node(self, pdf_id: str, filename: str, metadata: Dict = None) -> bool:
        """
        Create a PDF node in Neo4j
        
        Args:
            pdf_id: PDF ID
            filename: PDF filename
            metadata: Additional metadata
            
        Returns:
            Success boolean
        """
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                query = """
                MERGE (p:PDF {pdf_id: $pdf_id})
                SET p.filename = $filename,
                    p.metadata = $metadata,
                    p.created_at = datetime()
                RETURN p
                """
                session.run(query, {
                    'pdf_id': pdf_id,
                    'filename': filename,
                    'metadata': json.dumps(metadata or {})
                })
            return True
        except Exception as e:
            print(f"⚠️  Failed to create PDF node: {e}")
            return False
    
    def create_chunk_node(self, chunk_id: str, pdf_id: str, page_number: int = None) -> bool:
        """
        Create a chunk node in Neo4j
        
        Args:
            chunk_id: Chunk ID
            pdf_id: PDF ID
            page_number: Page number (optional)
            
        Returns:
            Success boolean
        """
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (p:PDF {pdf_id: $pdf_id})
                MERGE (c:Chunk {chunk_id: $chunk_id})
                SET c.pdf_id = $pdf_id,
                    c.page_number = $page_number,
                    c.created_at = datetime()
                MERGE (p)-[:CONTAINS]->(c)
                RETURN c
                """
                session.run(query, {
                    'chunk_id': chunk_id,
                    'pdf_id': pdf_id,
                    'page_number': page_number
                })
            return True
        except Exception as e:
            print(f"⚠️  Failed to create chunk node: {e}")
            return False
    
    def create_entity_node(self, entity_name: str, entity_type: str, 
                          properties: Dict = None) -> bool:
        """
        Create or update an entity node (Person, Project, Topic, etc.)
        
        Args:
            entity_name: Entity name
            entity_type: Entity type (Person, Project, Topic, Organization, etc.)
            properties: Additional properties
            
        Returns:
            Success boolean
        """
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                # Use MERGE to create or update
                query = f"""
                MERGE (e:{entity_type} {{name: $name}})
                SET e.updated_at = datetime()
                """
                
                params = {'name': entity_name}
                
                if properties:
                    for key, value in properties.items():
                        query += f", e.{key} = ${key}"
                        params[key] = value
                
                query += " RETURN e"
                
                session.run(query, params)
            return True
        except Exception as e:
            print(f"⚠️  Failed to create entity node: {e}")
            return False
    
    def create_relationship(self, source_entity: str, source_type: str,
                           relationship_type: str, target_entity: str,
                           target_type: str, properties: Dict = None) -> bool:
        """
        Create a relationship between entities
        
        Args:
            source_entity: Source entity name
            source_type: Source entity type
            relationship_type: Relationship type (WORKS_ON, MENTIONS, etc.)
            target_entity: Target entity name
            target_type: Target entity type
            properties: Relationship properties (confidence, context, etc.)
            
        Returns:
            Success boolean
        """
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                query = f"""
                MATCH (s:{source_type} {{name: $source}})
                MATCH (t:{target_type} {{name: $target}})
                MERGE (s)-[r:{relationship_type}]->(t)
                SET r.updated_at = datetime()
                """
                
                params = {
                    'source': source_entity,
                    'target': target_entity
                }
                
                if properties:
                    for key, value in properties.items():
                        query += f", r.{key} = ${key}"
                        params[key] = value
                
                query += " RETURN r"
                
                result = session.run(query, params)
                return result.single() is not None
        except Exception as e:
            print(f"⚠️  Failed to create relationship: {e}")
            return False
    
    def link_chunk_to_entity(self, chunk_id: str, entity_name: str,
                            entity_type: str, relationship_type: str = "MENTIONS") -> bool:
        """
        Link a chunk to an entity
        
        Args:
            chunk_id: Chunk ID
            entity_name: Entity name
            entity_type: Entity type
            relationship_type: Relationship type (default: MENTIONS)
            
        Returns:
            Success boolean
        """
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                query = f"""
                MATCH (c:Chunk {{chunk_id: $chunk_id}})
                MATCH (e:{entity_type} {{name: $entity_name}})
                MERGE (c)-[r:{relationship_type}]->(e)
                SET r.updated_at = datetime()
                RETURN r
                """
                result = session.run(query, {
                    'chunk_id': chunk_id,
                    'entity_name': entity_name
                })
                return result.single() is not None
        except Exception as e:
            print(f"⚠️  Failed to link chunk to entity: {e}")
            return False
    
    def index_entities_and_relationships(self, extraction_result: Dict, pdf_id: str = None) -> bool:
        """
        Index entities and relationships from extraction result
        
        Args:
            extraction_result: Result from EntityExtractor.extract_all()
            pdf_id: PDF ID (optional)
            
        Returns:
            Success boolean
        """
        if not self.driver:
            return False
        
        try:
            chunk_id = extraction_result.get('chunk_id')
            entities = extraction_result.get('entities', {})
            relationships = extraction_result.get('relationships', [])
            
            # Create chunk node if pdf_id provided
            if pdf_id and chunk_id:
                self.create_chunk_node(chunk_id, pdf_id)
            
            # Create entity nodes
            entity_type_map = {
                'persons': 'Person',
                'organizations': 'Organization',
                'locations': 'Location',
                'dates': 'Date',
                'other': 'Entity'
            }
            
            for category, items in entities.items():
                entity_type = entity_type_map.get(category, 'Entity')
                for item in items:
                    self.create_entity_node(
                        item['text'],
                        entity_type,
                        {'label': item['label']}
                    )
                    # Link chunk to entity
                    if chunk_id:
                        self.link_chunk_to_entity(chunk_id, item['text'], entity_type)
            
            # Create relationships
            for rel in relationships:
                source_type = rel.get('source_type', 'Entity')
                target_type = rel.get('target_type', 'Entity')
                
                # Create entity nodes if they don't exist
                self.create_entity_node(rel['source_entity'], source_type)
                self.create_entity_node(rel['target_entity'], target_type)
                
                # Create relationship
                self.create_relationship(
                    rel['source_entity'],
                    source_type,
                    rel['relationship'],
                    rel['target_entity'],
                    target_type,
                    {
                        'confidence': rel.get('confidence', 0.5),
                        'context': rel.get('context', '')
                    }
                )
            
            return True
        except Exception as e:
            print(f"⚠️  Failed to index entities: {e}")
            return False
    
    def search_by_relationship(self, entity_name: str, relationship_type: str = None,
                              limit: int = 10) -> List[Dict]:
        """
        Search PDFs/chunks by entity relationships
        
        Args:
            entity_name: Entity name to search for
            relationship_type: Filter by relationship type (optional)
            limit: Maximum results
            
        Returns:
            List of related PDFs/chunks
        """
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                if relationship_type:
                    query = f"""
                    MATCH (p:PDF)-[:CONTAINS]->(c:Chunk)-[r:{relationship_type}]->(e {{name: $entity_name}})
                    RETURN DISTINCT p.pdf_id as pdf_id, p.filename as filename, 
                           c.chunk_id as chunk_id, type(r) as relationship
                    LIMIT $limit
                    """
                else:
                    query = """
                    MATCH (p:PDF)-[:CONTAINS]->(c:Chunk)-[r]->(e {name: $entity_name})
                    RETURN DISTINCT p.pdf_id as pdf_id, p.filename as filename,
                           c.chunk_id as chunk_id, type(r) as relationship
                    LIMIT $limit
                    """
                
                result = session.run(query, {
                    'entity_name': entity_name,
                    'limit': limit
                })
                
                documents = []
                for record in result:
                    documents.append({
                        'pdf_id': record['pdf_id'],
                        'filename': record['filename'],
                        'chunk_id': record['chunk_id'],
                        'relationship': record['relationship'],
                        'relevance_score': 0.8  # Default relevance
                    })
                
                return documents
        except Exception as e:
            print(f"⚠️  Graph search failed: {e}")
            return []
    
    def query_by_query(self, query_text: str, limit: int = 10) -> List[Dict]:
        """
        Search PDFs using natural language query
        Extracts entities from query and finds related PDFs
        
        Args:
            query_text: Natural language query
            limit: Maximum results
            
        Returns:
            List of relevant PDFs/chunks
        """
        if not self.driver:
            return []
        
        # Simple entity extraction from query (can be enhanced)
        import re
        potential_entities = re.findall(r'\b[A-Z][a-z]+\b', query_text)
        
        if not potential_entities:
            return []
        
        # Search for PDFs related to these entities
        all_docs = {}
        for entity in potential_entities[:3]:  # Limit to 3 entities
            docs = self.search_by_relationship(entity, limit=limit)
            for doc in docs:
                key = f"{doc['pdf_id']}_{doc['chunk_id']}"
                if key not in all_docs:
                    all_docs[key] = doc
                else:
                    # Boost score if multiple entities match
                    all_docs[key]['relevance_score'] = min(
                        all_docs[key]['relevance_score'] + 0.1, 1.0
                    )
        
        return list(all_docs.values())[:limit]
    
    def get_related_pdfs(self, pdf_id: str, limit: int = 10) -> List[Dict]:
        """
        Get PDFs related to a given PDF through shared entities
        
        Args:
            pdf_id: PDF ID
            limit: Maximum results
            
        Returns:
            List of related PDFs
        """
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (p1:PDF {pdf_id: $pdf_id})-[:CONTAINS]->(c1:Chunk)-[:MENTIONS]->(e)<-[:MENTIONS]-(c2:Chunk)<-[:CONTAINS]-(p2:PDF)
                WHERE p1 <> p2
                RETURN DISTINCT p2.pdf_id as pdf_id, p2.filename as filename,
                       count(e) as shared_entities
                ORDER BY shared_entities DESC
                LIMIT $limit
                """
                
                result = session.run(query, {
                    'pdf_id': pdf_id,
                    'limit': limit
                })
                
                documents = []
                for record in result:
                    documents.append({
                        'pdf_id': record['pdf_id'],
                        'filename': record['filename'],
                        'shared_entities': record['shared_entities'],
                        'relevance_score': min(record['shared_entities'] / 5.0, 1.0)
                    })
                
                return documents
        except Exception as e:
            print(f"⚠️  Failed to get related PDFs: {e}")
            return []
    
    def delete_pdf(self, pdf_id: str) -> bool:
        """Delete PDF and its relationships from graph"""
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (p:PDF {pdf_id: $pdf_id})
                DETACH DELETE p
                """
                session.run(query, {'pdf_id': pdf_id})
            return True
        except Exception as e:
            print(f"⚠️  Failed to delete PDF: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get graph database statistics"""
        if not self.driver:
            return {'connected': False}
        
        try:
            with self.driver.session() as session:
                # Count nodes
                node_result = session.run("MATCH (n) RETURN count(n) as count")
                node_count = node_result.single()['count']
                
                # Count relationships
                rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                rel_count = rel_result.single()['count']
                
                # Count PDFs
                pdf_result = session.run("MATCH (p:PDF) RETURN count(p) as count")
                pdf_count = pdf_result.single()['count']
                
                return {
                    'connected': True,
                    'total_nodes': node_count,
                    'total_relationships': rel_count,
                    'total_pdfs': pdf_count
                }
        except Exception as e:
            print(f"⚠️  Failed to get stats: {e}")
            return {'connected': False, 'error': str(e)}
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            print("🔌 Neo4j connection closed")
