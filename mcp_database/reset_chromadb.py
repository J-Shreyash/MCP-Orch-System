"""
Reset ChromaDB Database
Use this script to manually reset ChromaDB if schema errors occur
Company: Sepia ML | Developer: Shreyash Shankarrao Jadhav
"""
import os
import shutil
import time

def reset_chromadb(chroma_dir: str = "./chroma_db"):
    """Reset ChromaDB database by deleting the directory"""
    print(f"\n{'='*60}")
    print("🔄 ChromaDB Database Reset Tool")
    print(f"{'='*60}\n")
    
    if not os.path.exists(chroma_dir):
        print(f"ℹ️ ChromaDB directory does not exist: {chroma_dir}")
        print("✅ Nothing to reset")
        return True
    
    print(f"📁 ChromaDB Directory: {chroma_dir}")
    print(f"⚠️ This will DELETE all data in ChromaDB!")
    
    # Try to delete
    max_retries = 5
    for attempt in range(max_retries):
        try:
            print(f"\n🗑️ Attempting to delete directory (attempt {attempt + 1}/{max_retries})...")
            shutil.rmtree(chroma_dir)
            print("✅ Directory deleted successfully!")
            
            # Recreate empty directory
            os.makedirs(chroma_dir, exist_ok=True)
            print(f"✅ Created fresh ChromaDB directory: {chroma_dir}")
            print("\n✅ ChromaDB reset complete! You can now restart the server.")
            return True
            
        except PermissionError as pe:
            if attempt < max_retries - 1:
                print(f"⚠️ File locked, waiting 3 seconds before retry...")
                time.sleep(3)
            else:
                print(f"\n❌ Could not delete directory after {max_retries} attempts")
                print("\n💡 Manual Reset Instructions:")
                print("   1. Stop all running servers (Database MCP, RAG PDF MCP)")
                print("   2. Close any programs that might be using ChromaDB")
                print(f"   3. Manually delete the directory: {os.path.abspath(chroma_dir)}")
                print("   4. Restart the servers")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    return False

if __name__ == "__main__":
    import sys
    
    # Get directory from command line or use default
    chroma_dir = sys.argv[1] if len(sys.argv) > 1 else "./chroma_db"
    
    success = reset_chromadb(chroma_dir)
    sys.exit(0 if success else 1)
