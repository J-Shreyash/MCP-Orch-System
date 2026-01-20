"""
Sync Manager - Coordinates MySQL, ChromaDB, BM25, and Neo4j operations
Ensures data consistency across all databases
Company: Sepia ML | Developer: Shreyash Shankarrao Jadhav
"""
from typing import Dict, List, Optional
import uuid
from collections import defaultdict


class SyncManager:
    """Manages synchronization between MySQL, ChromaDB, BM25, and Neo4j"""
    
    def __init__(self, mysql_handler, chroma_handler, bm25_handler=None, 
                 graph_handler=None, entity_extractor=None):
        """
        Initialize Sync Manager
        
        Args:
            mysql_handler: MySQLHandler instance
            chroma_handler: ChromaHandler instance
            bm25_handler: BM25Handler instance (optional)
            graph_handler: GraphHandler instance (optional)
            entity_extractor: EntityExtractor instance (optional)
        """
        self.mysql = mysql_handler
        self.chroma = chroma_handler
        self.bm25 = bm25_handler
        self.graph = graph_handler
        self.entity_extractor = entity_extractor
        
        # Build BM25 index from existing documents
        if self.bm25:
            self._rebuild_bm25_index()
        
        print("🔄 Sync Manager initialized (MySQL + ChromaDB + BM25 + Neo4j)")
    
    def create_document(self, title: str, content: str, metadata: Dict = None,
                       category: str = "general", tags: List[str] = None) -> Optional[Dict]:
        """
        Create document in both MySQL and ChromaDB
        
        Args:
            title: Document title
            content: Document content
            metadata: Additional metadata
            category: Document category
            tags: Document tags
            
        Returns:
            Document info or None
        """
        try:
            # Generate unique ID
            doc_id = str(uuid.uuid4())
            
            print(f"\n{'='*60}")
            print(f"📝 Creating document: {title}")
            print(f"   ID: {doc_id}")
            print(f"{'='*60}\n")
            
            # Add to ChromaDB first (for embedding)
            chroma_success = self.chroma.add_document(
                doc_id=doc_id,
                title=title,
                content=content,
                metadata=metadata or {}
            )
            
            if not chroma_success:
                print("❌ Failed to add to ChromaDB")
                return None
            
            # Add to MySQL
            mysql_success = self.mysql.insert_document(
                doc_id=doc_id,
                title=title,
                content=content,
                metadata=metadata or {},
                category=category,
                tags=tags or [],
                chroma_id=doc_id
            )
            
            if not mysql_success:
                # Rollback ChromaDB if MySQL fails
                print("⚠️  MySQL insert failed, rolling back ChromaDB...")
                self.chroma.delete_document(doc_id)
                return None
            
            print(f"✅ Document created successfully in MySQL and ChromaDB!")
            
            # Add to BM25 index - CRITICAL FIX: Rebuild from all documents to avoid losing previous ones
            if self.bm25:
                try:
                    # Rebuild index from all MySQL documents to ensure all documents are indexed
                    self._rebuild_bm25_index()
                    print("   ✅ BM25 index rebuilt with all documents")
                except Exception as e:
                    print(f"   ⚠️  BM25 indexing failed: {e}")
            
            # Extract entities and index in Neo4j (async-friendly, but blocking for now)
            if self.graph and self.entity_extractor:
                try:
                    print("   🔍 Extracting entities and relationships...")
                    extraction_result = self.entity_extractor.extract_all(content, doc_id)
                    
                    # Index in Neo4j
                    self.graph.create_document_node(doc_id, title, metadata or {})
                    self.graph.index_entities_and_relationships(extraction_result)
                    print("   ✅ Indexed in Neo4j graph")
                except Exception as e:
                    print(f"   ⚠️  Graph indexing failed: {e}")
            
            print(f"✅ Document fully indexed!\n")
            
            # Return document info
            return self.mysql.get_document(doc_id)
        
        except Exception as e:
            print(f"❌ Create document failed: {e}")
            return None
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        """Get document from MySQL (includes all metadata)"""
        return self.mysql.get_document(doc_id)
    
    def update_document(self, doc_id: str, **kwargs) -> bool:
        """
        Update document in both databases
        
        Args:
            doc_id: Document ID
            **kwargs: Fields to update (title, content, metadata, etc.)
            
        Returns:
            Success boolean
        """
        try:
            print(f"\n{'='*60}")
            print(f"✏️  Updating document: {doc_id}")
            print(f"{'='*60}\n")
            
            # Update MySQL
            mysql_success = self.mysql.update_document(doc_id, **kwargs)
            
            if not mysql_success:
                return False
            
            # Update ChromaDB if content or title changed
            if 'content' in kwargs or 'title' in kwargs:
                chroma_success = self.chroma.update_document(
                    doc_id=doc_id,
                    title=kwargs.get('title'),
                    content=kwargs.get('content'),
                    metadata=kwargs.get('metadata')
                )
                
                if not chroma_success:
                    print("⚠️  ChromaDB update failed, but MySQL updated")
            
            # Update BM25 index
            if self.bm25:
                try:
                    self.bm25.update_document(
                        doc_id=doc_id,
                        title=kwargs.get('title'),
                        content=kwargs.get('content'),
                        **{k: v for k, v in kwargs.items() if k not in ['title', 'content']}
                    )
                except Exception as e:
                    print(f"⚠️  BM25 update failed: {e}")
            
            # Re-extract entities if content changed
            if 'content' in kwargs and self.graph and self.entity_extractor:
                try:
                    content = kwargs.get('content')
                    if content:
                        extraction_result = self.entity_extractor.extract_all(content, doc_id)
                        self.graph.index_entities_and_relationships(extraction_result)
                except Exception as e:
                    print(f"⚠️  Graph re-indexing failed: {e}")
            
            print(f"✅ Document updated in all databases!\n")
            return True
        
        except Exception as e:
            print(f"❌ Update failed: {e}")
            return False
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete document from both databases
        
        Args:
            doc_id: Document ID
            
        Returns:
            Success boolean
        """
        try:
            print(f"\n{'='*60}")
            print(f"🗑️  Deleting document: {doc_id}")
            print(f"{'='*60}\n")
            
            # Delete from all databases
            mysql_success = self.mysql.delete_document(doc_id)
            chroma_success = self.chroma.delete_document(doc_id)
            
            # Delete from BM25
            bm25_success = True
            if self.bm25:
                try:
                    self.bm25.remove_document(doc_id)
                except Exception as e:
                    print(f"⚠️  BM25 deletion failed: {e}")
                    bm25_success = False
            
            # Delete from Neo4j
            graph_success = True
            if self.graph:
                try:
                    self.graph.delete_document(doc_id)
                except Exception as e:
                    print(f"⚠️  Graph deletion failed: {e}")
                    graph_success = False
            
            if mysql_success and chroma_success:
                print(f"✅ Document deleted from all databases!\n")
                return True
            else:
                print(f"⚠️  Partial deletion - MySQL: {mysql_success}, Chroma: {chroma_success}, BM25: {bm25_success}, Graph: {graph_success}\n")
                return False
        
        except Exception as e:
            print(f"❌ Delete failed: {e}")
            return False
    
    def search_documents(self, query: str, search_type: str = "semantic",
                        limit: int = 10, category: str = None) -> List[Dict]:
        """
        Search documents using different methods
        
        Args:
            query: Search query
            search_type: "semantic", "keyword", or "hybrid"
            limit: Number of results
            category: Filter by category
            
        Returns:
            List of search results
        """
        try:
            import logging
            search_logger = logging.getLogger(__name__)
            search_logger.info(f"\n{'='*60}")
            search_logger.info(f"🔍 Searching documents")
            search_logger.info(f"   Query: '{query}'")
            search_logger.info(f"   Type: {search_type}")
            search_logger.info(f"   Limit: {limit}")
            search_logger.info(f"{'='*60}\n")
            print(f"\n{'='*60}")
            print(f"🔍 Searching documents")
            print(f"   Query: '{query}'")
            print(f"   Type: {search_type}")
            print(f"   Limit: {limit}")
            print(f"{'='*60}\n")
            
            if search_type == "semantic":
                # Use ChromaDB for semantic search
                chroma_results = self.chroma.search_similar(query, limit=limit)
                
                # Enrich with MySQL data
                results = []
                for result in chroma_results:
                    mysql_doc = self.mysql.get_document(result['doc_id'])
                    if mysql_doc:
                        results.append({
                            'doc_id': result['doc_id'],
                            'title': mysql_doc['title'],
                            'content': result['content'],
                            'similarity_score': result['similarity_score'],
                            'metadata': mysql_doc['metadata'],
                            'category': mysql_doc['category'],
                            'tags': mysql_doc['tags']
                        })
                
                return results
            
            elif search_type == "keyword":
                # Use BM25 for keyword search (if available), fallback to MySQL
                if self.bm25:
                    bm25_results = self.bm25.search(query, limit=limit, category=category)
                    return bm25_results
                else:
                    # Fallback to MySQL LIKE search
                    mysql_results = self.mysql.search_documents(
                        keyword=query,
                        category=category,
                        limit=limit
                    )
                    
                    # Format results
                    results = []
                    for doc in mysql_results:
                        results.append({
                            'doc_id': doc['doc_id'],
                            'title': doc['title'],
                            'content': doc['content'],
                            'similarity_score': 0.5,  # Default score for keyword search
                            'metadata': doc['metadata'],
                            'category': doc['category'],
                            'tags': doc['tags']
                        })
                    
                    return results
            
            elif search_type == "hybrid":
                # Enhanced hybrid: BM25 + Semantic + Graph
                results = self._hybrid_search_enhanced(query, limit, category)
                
                # FALLBACK: If hybrid search returns no results or very few, try MySQL keyword search
                if not results or len(results) == 0:
                    import logging
                    fallback_logger = logging.getLogger(__name__)
                    fallback_logger.warning(f"   ⚠️  Hybrid search returned {len(results)} results, trying MySQL keyword fallback...")
                    print(f"   ⚠️  Hybrid search returned {len(results)} results, trying MySQL keyword fallback...")
                    try:
                        mysql_results = self.mysql.search_documents(keyword=query, category=category, limit=limit*2)
                        if mysql_results:
                            fallback_logger.info(f"   ✅ MySQL fallback found {len(mysql_results)} results")
                            print(f"   ✅ MySQL fallback found {len(mysql_results)} results")
                            # Format MySQL results to match expected format
                            formatted_results = []
                            for doc in mysql_results:
                                doc_id = doc.get('doc_id') or doc.get('id')
                                if doc_id:
                                    # Parse JSON fields if needed
                                    metadata = doc.get('metadata', {})
                                    if isinstance(metadata, str):
                                        import json
                                        try:
                                            metadata = json.loads(metadata)
                                        except:
                                            metadata = {}
                                    
                                    tags = doc.get('tags', [])
                                    if isinstance(tags, str):
                                        import json
                                        try:
                                            tags = json.loads(tags)
                                        except:
                                            tags = []
                                    
                                    formatted_results.append({
                                        'doc_id': str(doc_id),
                                        'title': doc.get('title', ''),
                                        'content': doc.get('content', ''),
                                        'similarity_score': 0.4,  # Reasonable score for keyword match
                                        'bm25_score': 0.4,
                                        'semantic_score': 0.0,
                                        'graph_score': 0.0,
                                        'metadata': metadata,
                                        'category': doc.get('category', 'general'),
                                        'tags': tags
                                    })
                            if formatted_results:
                                fallback_logger.info(f"   ✅ Returning {len(formatted_results)} fallback results")
                                print(f"   ✅ Returning {len(formatted_results)} fallback results")
                                return formatted_results
                    except Exception as e:
                        fallback_logger.error(f"   ⚠️  MySQL fallback failed: {e}")
                        print(f"   ⚠️  MySQL fallback failed: {e}")
                
                return results
            
            else:
                print(f"❌ Invalid search type: {search_type}")
                return []
        
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []
    
    def get_all_documents(self, limit: int = 100) -> List[Dict]:
        """Get all documents from MySQL"""
        return self.mysql.get_all_documents(limit=limit)
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        try:
            mysql_count = self.mysql.get_document_count()
            chroma_count = self.chroma.get_document_count()
            collections = self.chroma.get_collections()
            
            sync_status = "synced" if mysql_count == chroma_count else "out_of_sync"
            
            return {
                'mysql_documents': mysql_count,
                'chroma_documents': chroma_count,
                'total_documents': mysql_count,
                'collections': collections,
                'sync_status': sync_status,
                'sync_difference': abs(mysql_count - chroma_count)
            }
        
        except Exception as e:
            print(f"❌ Get stats failed: {e}")
            return {}
    
    def verify_sync(self) -> Dict:
        """Verify synchronization between databases"""
        try:
            print(f"\n{'='*60}")
            print("🔍 Verifying database synchronization...")
            print(f"{'='*60}\n")
            
            mysql_docs = self.mysql.get_all_documents(limit=1000)
            mysql_ids = {doc['doc_id'] for doc in mysql_docs}
            
            chroma_docs = self.chroma.get_all_documents(limit=1000)
            chroma_ids = {doc['doc_id'] for doc in chroma_docs}
            
            # Find differences
            only_in_mysql = mysql_ids - chroma_ids
            only_in_chroma = chroma_ids - mysql_ids
            
            synced = len(mysql_ids & chroma_ids)
            
            print(f"   MySQL documents: {len(mysql_ids)}")
            print(f"   ChromaDB documents: {len(chroma_ids)}")
            print(f"   Synced: {synced}")
            print(f"   Only in MySQL: {len(only_in_mysql)}")
            print(f"   Only in ChromaDB: {len(only_in_chroma)}")
            
            status = "synced" if len(only_in_mysql) == 0 and len(only_in_chroma) == 0 else "out_of_sync"
            
            return {
                'status': status,
                'synced_count': synced,
                'only_in_mysql': list(only_in_mysql),
                'only_in_chroma': list(only_in_chroma),
                'mysql_total': len(mysql_ids),
                'chroma_total': len(chroma_ids)
            }
        
        except Exception as e:
            print(f"❌ Verify sync failed: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _rebuild_bm25_index(self):
        """Rebuild BM25 index from MySQL documents"""
        if not self.bm25:
            return
        
        print("🔨 Rebuilding BM25 index...")
        try:
            documents = self.mysql.get_all_documents(limit=10000)  # Adjust limit as needed
            
            if documents:
                # Format for BM25
                bm25_docs = []
                skipped = 0
                for doc in documents:
                    # Handle documents that might not have doc_id (legacy data)
                    doc_id = doc.get('doc_id') or doc.get('id')
                    if not doc_id:
                        # Skip documents without valid ID
                        skipped += 1
                        continue
                    
                    # Convert id to string if it's numeric
                    doc_id = str(doc_id)
                    
                    bm25_docs.append({
                        'doc_id': doc_id,
                        'title': doc.get('title', ''),
                        'content': doc.get('content', ''),
                        'metadata': doc.get('metadata', {}),
                        'category': doc.get('category', 'general'),
                        'tags': doc.get('tags', [])
                    })
                
                if bm25_docs:
                    self.bm25.add_documents(bm25_docs)
                    print(f"✅ BM25 index rebuilt with {len(bm25_docs)} documents")
                    if skipped > 0:
                        print(f"⚠️  Skipped {skipped} documents without valid doc_id")
                else:
                    print("⚠️  No valid documents found for BM25 indexing")
            else:
                print("⚠️  No documents found for BM25 indexing")
        except Exception as e:
            import traceback
            print(f"⚠️  BM25 index rebuild failed: {e}")
            traceback.print_exc()
    
    def _hybrid_search_enhanced(self, query: str, limit: int, 
                               category: str = None) -> List[Dict]:
        """
        Enhanced hybrid search with weighted fusion
        BM25 (0.3) + Semantic (0.4) + Graph (0.3)
        
        Args:
            query: Search query
            limit: Maximum results
            category: Filter by category
            
        Returns:
            List of search results with weighted scores
        """
        # Parallel queries
        bm25_results = []
        semantic_results = []
        graph_results = []
        
        # BM25 keyword search
        import logging
        search_logger = logging.getLogger(__name__)
        search_logger.info(f"   🔍 Starting hybrid search for: '{query}'")
        print(f"   🔍 Starting hybrid search for: '{query}'")
        if self.bm25:
            search_logger.info(f"   📊 Querying BM25 index...")
            print(f"   📊 Querying BM25 index...")
            bm25_results = self.bm25.search(query, limit=limit*2, category=category)
            search_logger.info(f"   📊 BM25 returned {len(bm25_results)} raw results")
            print(f"   📊 BM25 returned {len(bm25_results)} raw results")
        else:
            # Fallback to MySQL
            mysql_results = self.mysql.search_documents(query, category, limit=limit*2)
            bm25_results = []
            for doc in mysql_results:
                doc_id = doc.get('doc_id') or doc.get('id')
                if not doc_id:
                    continue  # Skip documents without valid ID
                bm25_results.append({
                    'doc_id': str(doc_id),
                    'title': doc.get('title', ''),
                    'content': doc.get('content', ''),
                    'similarity_score': 0.5,
                    'bm25_score': 0.5,
                    'metadata': doc.get('metadata', {}),
                    'category': doc.get('category', 'general'),
                    'tags': doc.get('tags', [])
                })
        
        # Semantic search
        search_logger.info(f"   🔍 Querying ChromaDB semantic search...")
        print(f"   🔍 Querying ChromaDB semantic search...")
        semantic_results = self.chroma.search_similar(query, limit=limit*2)
        search_logger.info(f"   🔍 Semantic returned {len(semantic_results)} raw results")
        print(f"   🔍 Semantic returned {len(semantic_results)} raw results")
        
        # Graph search (if available)
        if self.graph:
            search_logger.info(f"   🕸️  Querying Neo4j graph search...")
            print(f"   🕸️  Querying Neo4j graph search...")
            graph_results = self.graph.query_by_query(query, limit=limit*2)
            search_logger.info(f"   🕸️  Graph returned {len(graph_results)} raw results")
            print(f"   🕸️  Graph returned {len(graph_results)} raw results")
        else:
            graph_results = []
            search_logger.info(f"   🕸️  Graph search not available")
            print(f"   🕸️  Graph search not available")
        
        # Combine and deduplicate with weighted fusion
        doc_scores = defaultdict(lambda: {
            'bm25_score': 0.0,
            'semantic_score': 0.0,
            'graph_score': 0.0,
            'doc_data': None
        })
        
        # Process BM25 results
        search_logger.info(f"   📊 Processing {len(bm25_results)} BM25 results...")
        print(f"   📊 Processing {len(bm25_results)} BM25 results...")
        for result in bm25_results:
            doc_id = result.get('doc_id')
            if not doc_id:
                continue  # Skip results without valid doc_id
            # Convert doc_id to string for consistency
            doc_id = str(doc_id)
            bm25_score = result.get('bm25_score', 0.0)
            similarity_score = result.get('similarity_score', 0.0)
            # Use BM25 score if available, otherwise use similarity score, otherwise default to 0.1 (not 0)
            final_bm25_score = bm25_score if bm25_score > 0 else (similarity_score if similarity_score > 0 else 0.1)
            
            # CRITICAL FIX: Verify document exists in MySQL and get actual doc_id
            mysql_doc = self.mysql.get_document(doc_id)
            if mysql_doc:
                # Use the actual doc_id from MySQL (might be doc_id UUID or id integer)
                actual_doc_id = str(mysql_doc.get('doc_id') or mysql_doc.get('id') or doc_id)
                doc_scores[actual_doc_id]['bm25_score'] = final_bm25_score
                # Update result with actual doc_id and MySQL data
                result['doc_id'] = actual_doc_id
                result['title'] = mysql_doc.get('title', result.get('title', ''))
                result['content'] = mysql_doc.get('content', result.get('content', ''))
                result['metadata'] = mysql_doc.get('metadata', result.get('metadata', {}))
                result['category'] = mysql_doc.get('category', result.get('category', 'general'))
                result['tags'] = mysql_doc.get('tags', result.get('tags', []))
                doc_scores[actual_doc_id]['doc_data'] = result
                search_logger.info(f"      - Doc {actual_doc_id}: BM25 score={final_bm25_score:.3f}, title='{result['title'][:50]}'")
                print(f"      - Doc {actual_doc_id}: BM25 score={final_bm25_score:.3f}, title='{result['title'][:50]}'")
            else:
                search_logger.warning(f"      - ⚠️  Doc {doc_id} not found in MySQL, skipping")
                print(f"      - ⚠️  Doc {doc_id} not found in MySQL, skipping")
        
        # Process semantic results
        search_logger.info(f"   🔍 Processing {len(semantic_results)} semantic results...")
        print(f"   🔍 Processing {len(semantic_results)} semantic results...")
        for result in semantic_results:
            doc_id = result.get('doc_id')
            if not doc_id:
                continue  # Skip results without valid doc_id
            # Convert doc_id to string for consistency
            doc_id = str(doc_id)
            doc_scores[doc_id]['semantic_score'] = result.get('similarity_score', 0.0)
            if not doc_scores[doc_id]['doc_data']:
                # Get from MySQL if not in BM25 results
                mysql_doc = self.mysql.get_document(doc_id)
                if mysql_doc:
                    # Use the actual doc_id from MySQL (might be different from search result)
                    actual_doc_id = str(mysql_doc.get('doc_id') or mysql_doc.get('id') or doc_id)
                    doc_scores[actual_doc_id]['doc_data'] = {
                        'doc_id': actual_doc_id,
                        'title': mysql_doc.get('title', ''),
                        'content': result.get('content', '') or mysql_doc.get('content', ''),
                        'metadata': mysql_doc.get('metadata', {}),
                        'category': mysql_doc.get('category', 'general'),
                        'tags': mysql_doc.get('tags', [])
                    }
                    # Also update semantic score for the actual doc_id
                    if actual_doc_id != doc_id:
                        doc_scores[actual_doc_id]['semantic_score'] = doc_scores[doc_id]['semantic_score']
        
        # Process graph results
        for result in graph_results:
            doc_id = result.get('doc_id')
            if not doc_id:
                continue  # Skip results without valid doc_id
            doc_scores[doc_id]['graph_score'] = result.get('relevance_score', 0.5)
            if not doc_scores[doc_id]['doc_data']:
                # Get from MySQL
                mysql_doc = self.mysql.get_document(doc_id)
                if mysql_doc:
                    doc_scores[doc_id]['doc_data'] = {
                        'doc_id': doc_id,
                        'title': mysql_doc.get('title', result.get('title', '')),
                        'content': mysql_doc.get('content', ''),
                        'metadata': mysql_doc.get('metadata', {}),
                        'category': mysql_doc.get('category', 'general'),
                        'tags': mysql_doc.get('tags', [])
                    }
        
        # Calculate weighted fusion scores
        final_results = []
        search_logger.info(f"   🔄 Processing {len(doc_scores)} unique documents for fusion...")
        print(f"   🔄 Processing {len(doc_scores)} unique documents for fusion...")
        for doc_id, scores in doc_scores.items():
            if scores['doc_data']:
                # Weighted fusion: BM25 (0.3) + Semantic (0.4) + Graph (0.3)
                final_score = (
                    0.3 * scores['bm25_score'] +
                    0.4 * scores['semantic_score'] +
                    0.3 * scores['graph_score']
                )
                
                # CRITICAL FIX: Include results even with low scores (BM25 keyword matches are valid)
                # Only filter out completely zero scores
                if final_score > 0 or scores['bm25_score'] > 0:
                    final_results.append({
                        **scores['doc_data'],
                        'similarity_score': final_score,
                        'bm25_score': scores['bm25_score'],
                        'semantic_score': scores['semantic_score'],
                        'graph_score': scores['graph_score']
                    })
        
        # Sort by final score
        final_results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        search_logger.info(f"   ✅ Returning {len(final_results)} final results (limit: {limit})")
        print(f"   ✅ Returning {len(final_results)} final results (limit: {limit})")
        return final_results[:limit]
