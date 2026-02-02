import toml
from supabase import create_client
import sys

def test_connection():
    try:
        print("🔍 Reading secrets...")
        secrets = toml.load(".streamlit/secrets.toml")
        url = secrets["supabase"]["url"]
        key = secrets["supabase"]["key"]
        
        print(f"📡 Connecting to: {url}")
        print(f"🔑 Using Key: {key[:10]}...")
        
        supabase = create_client(url, key)
        
        print("⏳ Testing query on 'audit_logs' table...")
        # Try to select 1 row. 
        # Note: If database is empty, it returns [], which is SUCCESS.
        # If Auth invalid, it raises Error.
        response = supabase.table("audit_logs").select("*").limit(1).execute()
        
        # Check Campaigns Table
        try:
            res = supabase.table("campaigns").select("count", count="exact").execute()
            msg = f"Campaign Table Exists! Count: {res.count}"
            print(msg)
            with open("verification_result.txt", "w") as f:
                f.write(msg)
        except Exception as e:
            msg = f"Campaign Table NOT Found: {e}"
            print(msg)
            with open("verification_result.txt", "w") as f:
                f.write(msg)


        
        print("\n✅ CONNECTION SUCCESSFUL!")
        print(f"Response Data: {response.data}")
        return True

    except Exception as e:
        print("\n❌ CONNECTION FAILED")
        print(f"Error: {str(e)}")
        
        if "pk_" in str(e) or "sb_" in str(e) or "JWT" in str(e):
            print("\n💡 TIP: The key might be incorrect. Ensure you used the 'anon' 'public' key (starts with 'eyJ...'), not a Publishable key.")
        return False

if __name__ == "__main__":
    success = test_connection()
    if not success:
        sys.exit(1)
