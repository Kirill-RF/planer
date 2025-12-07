#!/usr/bin/env python
"""
Test script to verify case-insensitive search functionality
"""
import os
import sys
import django
from django.conf import settings

# Add the workspace directory to Python path so we can import the clients app
sys.path.insert(0, '/workspace')

# Configure Django settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'clients',
        ],
        SECRET_KEY='test-key',
        USE_TZ=True,
    )

django.setup()

from django.db import connection
from clients.models import Client
from django.test import TestCase

def test_case_insensitive_search():
    """
    Test if the database supports case-insensitive search properly
    """
    # Create the table
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(Client)
    
    # Create test data
    Client.objects.create(name='Test Client ABC')
    Client.objects.create(name='Another Client XYZ')
    Client.objects.create(name='ТЕСТ КЛИЕНТ РУССКИЙ')
    
    print("Testing case-insensitive search...")
    
    # Test case-insensitive search
    print('Searching for "test" (lowercase):')
    test_results = Client.objects.filter(name__icontains='test')
    for client in test_results:
        print(f'  - {client.name}')

    print('\nSearching for "TEST" (uppercase):')
    test_results_upper = Client.objects.filter(name__icontains='TEST')
    for client in test_results_upper:
        print(f'  - {client.name}')
    
    # Check if results are the same
    lowercase_results = [c.name for c in Client.objects.filter(name__icontains='test')]
    uppercase_results = [c.name for c in Client.objects.filter(name__icontains='TEST')]
    
    print(f'\nLowercase search results: {lowercase_results}')
    print(f'Uppercase search results: {uppercase_results}')
    
    if lowercase_results == uppercase_results:
        print('\n✓ Case-insensitive search is working correctly!')
        return True
    else:
        print('\n✗ Case-insensitive search is NOT working properly!')
        return False

if __name__ == '__main__':
    success = test_case_insensitive_search()
    sys.exit(0 if success else 1)