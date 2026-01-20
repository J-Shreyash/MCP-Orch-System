"""
Cleanup and Rename ChromaDB Directories
Removes old backup directories and renames the active one to chroma_db
Company: Sepia ML | Developer: Shreyash Shankarrao Jadhav
"""
import os
import shutil
from pathlib import Path
from datetime import datetime

def cleanup_and_rename_chromadb():
    """Clean up backup directories and rename active one to chroma_db"""
    print("\n" + "="*60)
    print("Cleaning Up and Renaming ChromaDB Directories")
    print("="*60 + "\n")
    
    base_dir = Path(__file__).parent
    
    # Process each MCP directory
    mcp_dirs = [
        ("mcp_database", "chroma_db"),
        ("mcp_rag_pdf", "chroma_db_pdf")
    ]
    
    for mcp_name, target_name in mcp_dirs:
        mcp_path = base_dir / mcp_name
        
        if not mcp_path.exists():
            print(f"INFO: {mcp_name} directory not found, skipping...")
            continue
        
        print(f"\nProcessing: {mcp_name}")
        print("-" * 60)
        
        # Find all chroma_db backup directories
        backup_dirs = []
        for item in mcp_path.iterdir():
            if item.is_dir() and item.name.startswith("chroma_db") and "backup" in item.name:
                # Get modification time
                mtime = item.stat().st_mtime
                backup_dirs.append((item, mtime))
        
        if not backup_dirs:
            print(f"INFO: No backup directories found in {mcp_name}")
            continue
        
        # Sort by modification time (newest first)
        backup_dirs.sort(key=lambda x: x[1], reverse=True)
        
        # Keep the newest, delete the rest
        newest_dir, newest_time = backup_dirs[0]
        print(f"KEEPING (newest): {newest_dir.name}")
        print(f"  Modified: {datetime.fromtimestamp(newest_time).strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Delete older backups
        for old_dir, old_time in backup_dirs[1:]:
            print(f"\nDELETING (old): {old_dir.name}")
            try:
                shutil.rmtree(old_dir)
                print(f"SUCCESS: Deleted {old_dir.name}")
            except Exception as e:
                print(f"ERROR: Could not delete {old_dir.name}: {e}")
        
        # Check if target directory already exists
        target_path = mcp_path / target_name
        if target_path.exists():
            if target_path.samefile(newest_dir):
                print(f"\nINFO: {target_name} already points to the active directory")
            else:
                print(f"\nWARNING: {target_name} already exists but is different")
                print(f"  Renaming it to {target_name}_old_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                try:
                    old_target = mcp_path / f"{target_name}_old_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    shutil.move(str(target_path), str(old_target))
                    print(f"SUCCESS: Moved old {target_name} to {old_target.name}")
                except Exception as e:
                    print(f"ERROR: Could not move old {target_name}: {e}")
                    continue
        
        # Rename newest backup to target name
        if not newest_dir.name == target_name:
            print(f"\nRENAMING: {newest_dir.name} -> {target_name}")
            try:
                newest_dir.rename(target_path)
                print(f"SUCCESS: Renamed to {target_name}")
            except Exception as e:
                print(f"ERROR: Could not rename: {e}")
                print(f"  You may need to stop the servers first")
        else:
            print(f"\nINFO: Directory already named {target_name}")
    
    print("\n" + "="*60)
    print("Cleanup Complete!")
    print("="*60)
    print("\nTIP: If you see errors, make sure all servers are stopped")
    print("     before running this script.\n")

if __name__ == "__main__":
    cleanup_and_rename_chromadb()
