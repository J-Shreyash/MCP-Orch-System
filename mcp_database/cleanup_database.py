"""
Database Cleanup Script
Removes orphaned ChromaDB entries that don't exist in MySQL
"""

import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_database():
    """Clean up orphaned entries"""
    
    base_url = "http://localhost:8003"
    
    try:
        # Get all documents from list endpoint
        logger.info("📋 Getting document list...")
        list_response = requests.get(f"{base_url}/documents?limit=1000")
        
        if list_response.status_code == 200:
            docs = list_response.json().get('documents', [])
            logger.info(f"Found {len(docs)} documents in list")
            
            # Check which ones actually exist
            valid_count = 0
            orphaned_ids = []
            
            for doc in docs:
                doc_id = doc.get('id') or doc.get('document_id')
                if not doc_id:
                    continue
                
                # Try to get the document
                get_response = requests.get(f"{base_url}/documents/{doc_id}")
                
                if get_response.status_code == 200:
                    valid_count += 1
                    logger.info(f"✅ Document {doc_id} is valid")
                else:
                    orphaned_ids.append(doc_id)
                    logger.warning(f"⚠️ Document {doc_id} is orphaned")
            
            logger.info(f"\n📊 Summary:")
            logger.info(f"   Valid: {valid_count}")
            logger.info(f"   Orphaned: {len(orphaned_ids)}")
            
            if orphaned_ids:
                logger.info(f"\n🗑️ Orphaned IDs: {orphaned_ids}")
                logger.info("\nTo fix: You need to manually clean ChromaDB")
                logger.info("Run this in your Database MCP server Python console:")
                logger.info(f"collection.delete(ids={[str(id) for id in orphaned_ids]})")
            
            return {
                "valid_count": valid_count,
                "orphaned_count": len(orphaned_ids),
                "orphaned_ids": orphaned_ids
            }
        else:
            logger.error(f"Failed to get documents: {list_response.status_code}")
            return None
    
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        return None


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧹 Database Cleanup Script")
    print("="*60 + "\n")
    
    result = cleanup_database()
    
    if result:
        print("\n" + "="*60)
        print(f"✅ Cleanup analysis complete!")
        print(f"   Valid documents: {result['valid_count']}")
        print(f"   Orphaned entries: {result['orphaned_count']}")
        print("="*60 + "\n")