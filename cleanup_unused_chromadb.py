"""
Cleanup Unused ChromaDB Directories
Deletes the old chroma_db directories that are no longer in use
Company: Sepia ML | Developer: Shreyash Shankarrao Jadhav
"""
import os
import shutil
import time
from pathlib import Path

def cleanup_unused_chromadb():
    """Delete unused chroma_db directories"""
    print("\n" + "="*60)
    print("Cleaning Up Unused ChromaDB Directories")
    print("="*60 + "\n")
    
    base_dir = Path(__file__).parent
    
    # Directories to clean up
    dirs_to_clean = [
        base_dir / "mcp_database" / "chroma_db",
        base_dir / "mcp_rag_pdf" / "chroma_db"
    ]
    
    cleaned = 0
    failed = 0
    
    for chroma_dir in dirs_to_clean:
        if not chroma_dir.exists():
            print(f"INFO: Directory doesn't exist: {chroma_dir}")
            continue
        
        print(f"Attempting to delete: {chroma_dir}")
        
        # Try multiple times with delays
        max_retries = 3
        deleted = False
        
        for attempt in range(max_retries):
            try:
                shutil.rmtree(chroma_dir)
                deleted = True
                print(f"SUCCESS: Deleted {chroma_dir}")
                cleaned += 1
                break
            except PermissionError as pe:
                if attempt < max_retries - 1:
                    print(f"WARNING: File locked, waiting 2 seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(2)
                else:
                    print(f"ERROR: Could not delete: {chroma_dir}")
                    print(f"   Error: {pe}")
                    print(f"   TIP: Make sure all servers are stopped before running this script")
                    failed += 1
            except Exception as e:
                print(f"ERROR: Error deleting {chroma_dir}: {e}")
                failed += 1
                break
    
    print("\n" + "="*60)
    print("Cleanup Summary")
    print("="*60)
    print(f"Successfully deleted: {cleaned} directory(ies)")
    print(f"Failed to delete: {failed} directory(ies)")
    
    if failed > 0:
        print("\nTIP: If deletion failed, please:")
        print("   1. Stop ALL running servers (Database MCP, RAG PDF MCP)")
        print("   2. Close any Python processes")
        print("   3. Wait 5 seconds")
        print("   4. Run this script again")
        print("   5. Or manually delete the directories from File Explorer")
    
    print("="*60 + "\n")

if __name__ == "__main__":
    cleanup_unused_chromadb()
