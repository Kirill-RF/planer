from django.http import JsonResponse
from django.views import View
from clients.models import Client
from django.db.models import Q
import re


class ClientSearchView(View):
    def get(self, request):
        query = request.GET.get('q', '')
        if len(query) < 2:
            return JsonResponse([], safe=False)
        
        # Using iregex for case-insensitive search - more reliable for both Latin and Cyrillic
        # Escape special regex characters to prevent regex injection
        escaped_query = re.escape(query)
        clients = Client.objects.filter(
            name__iregex=escaped_query
        ).distinct()[:20]
        
        data = [{'id': c.id, 'name': c.name} for c in clients]
        return JsonResponse(data, safe=False)