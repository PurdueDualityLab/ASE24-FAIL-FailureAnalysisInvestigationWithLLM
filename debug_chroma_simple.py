import chromadb
import sys

def check_chroma():
    print("Connecting to ChromaDB at localhost:8001...")
    try:
        # Connect to Chroma
        client = chromadb.HttpClient(host="localhost", port=8001)
        print("Connected.")
        
        # List collections
        collections = client.list_collections()
        print(f"Found {len(collections)} collections.")
        
        for col in collections:
            print(f"- Name: {col.name}")
            print(f"  Count: {col.count()}")
            
            if col.name == "articlesVDB":
                if col.count() == 0:
                    print("  WARNING: articlesVDB is empty!")
                else:
                    print("  articlesVDB seems populated.")
                    # Peek
                    print("  Peeking first item:")
                    print(col.peek(limit=1))

    except Exception as e:
        print(f"Error connecting or querying Chroma: {e}")

if __name__ == "__main__":
    check_chroma()
