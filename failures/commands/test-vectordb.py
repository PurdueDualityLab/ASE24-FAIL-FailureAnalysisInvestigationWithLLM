# Fix to Chroma requires sqlite3 >= 3.35.0
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import chromadb

chroma_client = chromadb.HttpClient(port="8001")
chroma_client.heartbeat()