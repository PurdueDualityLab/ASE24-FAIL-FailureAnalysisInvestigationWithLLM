import os
import django
import asyncio
from asgiref.sync import sync_to_async

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from failures.chat.models import ChainlitThread
from failures.chat.datalayer import DjangoDataLayer

async def debug():
    print("Listing threads...")
    threads = [t async for t in ChainlitThread.objects.all()]
    print(f"Found {len(threads)} threads.")
    
    if not threads:
        print("No threads found. Creating one for testing...")
        t = await ChainlitThread.objects.acreate(id="test_thread_1", name="Test Thread")
        threads = [t]

    thread_id = threads[0].id
    print(f"Testing get_thread for ID: {thread_id}")
    
    dl = DjangoDataLayer()
    result = await dl.get_thread(thread_id)
    
    if result:
        print("Success! Thread found.")
        print(f"ID: {result['id']}")
        print(f"Steps: {len(result.get('steps', []))}")
    else:
        print("Failed! Thread not found via get_thread.")

if __name__ == "__main__":
    asyncio.run(debug())
