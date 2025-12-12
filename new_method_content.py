    def survey_answer_list_view(self, request):
        """Custom view for survey answers with filters and search functionality."""
        from django.contrib.admin import site
        from django.contrib.admin.views.main import ChangeList
        from django.contrib.admin.options import IncorrectLookupParameters
        from django.core.paginator import Paginator
        from django.db.models import Count, Q
        from datetime import datetime, timedelta
        from django.utils import timezone

        # Get all survey answers with related data
        queryset = self.get_queryset(request)

        # Apply filters
        if request.GET.get('client'):
            queryset = queryset.filter(client__id=request.GET.get('client'))

        if request.GET.get('user'):
            queryset = queryset.filter(user__id=request.GET.get('user'))

        if request.GET.get('moderator'):
            queryset = queryset.filter(question__task__created_by__id=request.GET.get('moderator'))

        if request.GET.get('task_type'):
            queryset = queryset.filter(question__task__task_type=request.GET.get('task_type'))

        if request.GET.get('task'):
            queryset = queryset.filter(question__task__id=request.GET.get('task'))

        # Date filters
        if request.GET.get('date_filter'):
            date_filter = request.GET.get('date_filter')
            if date_filter == 'today':
                queryset = queryset.filter(created_at__date=timezone.now().date())
            elif date_filter == 'yesterday':
                yesterday = timezone.now().date() - timedelta(days=1)
                queryset = queryset.filter(created_at__date=yesterday)
            elif date_filter == 'week':
                week_ago = timezone.now().date() - timedelta(days=7)
                queryset = queryset.filter(created_at__date__gte=week_ago)

        # Date range filter
        if request.GET.get('date_from') and request.GET.get('date_to'):
            from_date = request.GET.get('date_from')
            to_date = request.GET.get('date_to')
            queryset = queryset.filter(created_at__date__gte=from_date, created_at__date__lte=to_date)

        # Client name search - case insensitive
        if request.GET.get('client_search'):
            client_search = request.GET.get('client_search')
            queryset = queryset.filter(client__name__icontains=client_search)

        # Task name search - case insensitive
        if request.GET.get('task_search'):
            task_search = request.GET.get('task_search')
            queryset = queryset.filter(question__task__title__icontains=task_search)

        # Order by latest first
        queryset = queryset.order_by('-created_at')

        # Group answers by task to create task groups
        from django.db.models import Prefetch
        
        # Get distinct tasks with their answers
        tasks_with_answers = {}
        for answer in queryset:
            task_id = answer.question.task.id
            if task_id not in tasks_with_answers:
                tasks_with_answers[task_id] = {
                    'task': answer.question.task,
                    'answers': [],
                    'unique_clients': set(),
                    'unique_users': set(),
                    'latest_answer_date': answer.created_at,
                    'is_new': False,  # Will be set later if any answer is recent
                }
            tasks_with_answers[task_id]['answers'].append(answer)
            tasks_with_answers[task_id]['unique_clients'].add(answer.client)
            tasks_with_answers[task_id]['unique_users'].add(answer.user)
            
            # Update latest answer date
            if answer.created_at > tasks_with_answers[task_id]['latest_answer_date']:
                tasks_with_answers[task_id]['latest_answer_date'] = answer.created_at
            
            # Check if this answer is new (within last 24 hours)
            if answer.created_at >= timezone.now() - timedelta(hours=24):
                tasks_with_answers[task_id]['is_new'] = True

        # Convert to list and sort by latest answer
        task_groups = list(tasks_with_answers.values())
        task_groups.sort(key=lambda x: x['latest_answer_date'], reverse=True)

        # Pagination for task groups
        paginator = Paginator(task_groups, 20)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        # Get distinct clients, users, moderators, tasks for filter dropdowns
        from clients.models import Client
        from users.models import CustomUser
        from .models import Task

        clients = Client.objects.all()
        users = CustomUser.objects.filter(role='EMPLOYEE')
        moderators = CustomUser.objects.filter(role='MODERATOR')
        tasks = Task.objects.filter(task_type='SURVEY')

        context = {
            'title': _('Ответы на вопросы'),
            'page_obj': page_obj,
            'clients': clients,
            'users': users,
            'moderators': moderators,
            'tasks': tasks,
            'current_filters': request.GET,
            'opts': self.model._meta,
        }

        return render(request, 'admin/tasks/surveyanswer_list.html', context)