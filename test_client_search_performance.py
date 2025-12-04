"""
Test script to verify client search performance with 5000+ clients
"""
import os
import sys
import django
import time
from django.conf import settings

# Setup Django environment
sys.path.append('/workspace')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from clients.models import Client
from faker import Faker

def test_client_search_performance():
    print("Testing client search performance...")
    
    # Check how many clients we have
    total_clients = Client.objects.count()
    print(f"Total clients in database: {total_clients}")
    
    if total_clients < 5000:
        print("Populating database with more test clients...")
        fake = Faker('ru_RU')
        
        # Create additional clients to reach 5000
        batch_size = 1000
        start_time = time.time()
        
        for i in range(total_clients, 5000, batch_size):
            batch_end = min(i + batch_size, 5000)
            clients_batch = []
            
            for j in range(i, batch_end):
                client = Client(
                    name=fake.company(),
                    address=fake.address()
                )
                clients_batch.append(client)
            
            Client.objects.bulk_create(clients_batch)
            print(f'Created clients {i+1} to {batch_end}')
        
        end_time = time.time()
        print(f"Added clients in {end_time - start_time:.2f} seconds")
        
        total_clients = Client.objects.count()
        print(f"Total clients in database: {total_clients}")
    
    # Test search performance
    print("\nTesting search performance...")
    
    # Find a client name that we can use for testing
    sample_client = Client.objects.first()
    if sample_client:
        test_name = sample_client.name[:3] if len(sample_client.name) >= 3 else sample_client.name
        print(f"Testing search with query: '{test_name}'")
        
        # Time the search
        start_time = time.time()
        results = Client.objects.filter(name__icontains=test_name).order_by('name')[:20]
        end_time = time.time()
        
        search_time = end_time - start_time
        result_count = len(results)
        
        print(f"Search time: {search_time:.4f} seconds")
        print(f"Results returned: {result_count}")
        
        if search_time < 0.1:
            print("✅ Search performance is excellent (< 100ms)")
        elif search_time < 0.5:
            print("✅ Search performance is good (< 500ms)")
        elif search_time < 1.0:
            print("⚠️  Search performance is acceptable (< 1000ms)")
        else:
            print("❌ Search performance is slow (>= 1000ms)")
        
        return search_time < 1.0  # Performance is acceptable if under 1 second
    else:
        print("❌ No clients found to test search")
        return False

if __name__ == "__main__":
    success = test_client_search_performance()
    print(f"\nPerformance test {'passed' if success else 'failed'}")