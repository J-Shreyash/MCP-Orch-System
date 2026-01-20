"""
Google Drive Token Reset Script
Deletes expired tokens and forces re-authentication
"""
import os
from pathlib import Path

print("\n" + "🔧"*30)
print("   GOOGLE DRIVE TOKEN RESET")
print("🔧"*30 + "\n")

# Token file location
TOKEN_FILE = "token.json"

print("="*60)
print("Step 1: Checking for token file")
print("="*60)

token_path = Path(TOKEN_FILE)

if token_path.exists():
    print(f"\n✅ Found token file: {TOKEN_FILE}")
    print("🗑️  Deleting expired token...")
    
    try:
        os.remove(TOKEN_FILE)
        print("✅ Token file deleted successfully!")
    except Exception as e:
        print(f"❌ Error deleting token: {e}")
        print("   Try deleting it manually")
else:
    print(f"\n✅ No token file found (already clean)")

print("\n" + "="*60)
print("Step 2: Verification")
print("="*60)

if not token_path.exists():
    print("\n✅ Token file successfully removed!")
else:
    print("\n⚠️  Token file still exists - delete manually:")
    print(f"   {token_path.absolute()}")

print("\n" + "="*60)
print("🎉 TOKEN RESET COMPLETE!")
print("="*60)

print("\n💡 Next steps:")
print("   1. Start the server:")
print("      uvicorn server:app --reload --port 8002")
print("   2. You'll be prompted to authenticate in browser")
print("   3. Sign in with your Google account")
print("   4. Grant permissions")
print("   5. New token will be created automatically")

print("\n📝 Note:")
print("   • Make sure credentials.json is in the folder")
print("   • Browser will open automatically for authentication")
print("   • Complete the OAuth flow in browser")

print("\n" + "🔧"*30 + "\n")