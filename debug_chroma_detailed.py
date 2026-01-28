import chromadb
import sys
import logging

def check_chroma():
    print("Connecting to ChromaDB at localhost:8001...")
    try:
        # Connect to Chroma
        # Note: When running from host, we use localhost:8001
        # When running from inside docker (like this script might be), we might need 'chroma:8001'
        # But this script is likely run via 'docker compose run ...' which puts it in a container on the network.
        # IF running from host machine (where port 8001 is mapped), use localhost.
        # IF running via 'docker compose run django ...', use 'chroma'.
        
        # We'll try 'chroma' first (internal), then localhost fallback? 
        # Actually, let's assume this is run via 'docker compose run django ...'
        host = "chroma"
        port = 8001
        
        print(f"Attempting connection to {host}:{port}")
        client = chromadb.HttpClient(host=host, port=port)
        print("Connected.")
        
        # List collections
        collections = client.list_collections()
        print(f"Found {len(collections)} collections.")
        
        found = False
        for col in collections:
            print(f"- Name: {col.name}, ID: {col.id}")
            cnt = col.count()
            print(f"  Count: {cnt}")
            
            if col.name == "articlesVDB":
                found = True
                if cnt == 0:
                    print("  WARNING: articlesVDB is empty!")
                else:
                    print("  articlesVDB seems populated.")
                    # Peek
                    print("  Peeking first item:")
                    print(col.peek(limit=1))

        if not found:
             print("  WARNING: 'articlesVDB' collection NOT found in list!")

    except Exception as e:
        print(f"Error connecting or querying Chroma: {e}")

if __name__ == "__main__":
    check_chroma()
