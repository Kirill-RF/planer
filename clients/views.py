from django.http import JsonResponse
from django.views import View
from tasks.models import Client

class ClientSearchView(View):
    def get(self, request):
        query = request.GET.get('q', '')
        if len(query) < 2:
            return JsonResponse([], safe=False)
        
        clients = Client.objects.filter(name__icontains=query)[:20]
        data = [{'id': c.id, 'name': c.name} for c in clients]
        return JsonResponse(data, safe=False)