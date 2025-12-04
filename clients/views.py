from django.http import JsonResponse
from django.views import View
from clients.models import Client
from django.db.models import Q

class ClientSearchView(View):
    def get(self, request):
        query = request.GET.get('q', '')
        if len(query) < 2:
            return JsonResponse([], safe=False)
        
        # Using icontains for case-insensitive search - more reliable across database backends
        clients = Client.objects.filter(
            name__icontains=query
        ).distinct()[:20]
        
        data = [{'id': c.id, 'name': c.name} for c in clients]
        return JsonResponse(data, safe=False)