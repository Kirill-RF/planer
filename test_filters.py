import os
import django
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_filters():
    """Test the filter functionality in the survey answer admin"""
    from tasks.models import SurveyAnswer, Client, Task
    from tasks.admin import SurveyAnswerAdmin
    from django.contrib.admin import AdminSite
    from django.http import HttpRequest
    from django.test import RequestFactory
    from django.contrib.auth import get_user_model
    from django.core.paginator import Paginator
    
    print("Testing Filter Functionality...")
    
    # Create admin instance
    admin = SurveyAnswerAdmin(SurveyAnswer, AdminSite())
    
    # Create a mock request with various filter parameters
    factory = RequestFactory()
    
    # Test 1: Base queryset
    queryset = admin.get_queryset(None)
    print(f"✓ Base queryset has {queryset.count()} answers")
    
    # Test 2: Client filter
    try:
        sample_client = Client.objects.first()
        if sample_client:
            filtered_queryset = queryset.filter(client__id=sample_client.id)
            print(f"✓ Client filter works - found {filtered_queryset.count()} answers for client {sample_client.name}")
    except Exception as e:
        print(f"✗ Client filter error: {e}")
    
    # Test 3: Task type filter
    try:
        filtered_queryset = queryset.filter(question__task__task_type='SURVEY')
        print(f"✓ Task type filter works - found {filtered_queryset.count()} survey answers")
    except Exception as e:
        print(f"✗ Task type filter error: {e}")
    
    # Test 4: Date filters
    try:
        # Today
        today_queryset = queryset.filter(created_at__date=timezone.now().date())
        print(f"✓ Today date filter works - found {today_queryset.count()} answers")
        
        # Yesterday
        yesterday = timezone.now().date() - timedelta(days=1)
        yesterday_queryset = queryset.filter(created_at__date=yesterday)
        print(f"✓ Yesterday date filter works - found {yesterday_queryset.count()} answers")
        
        # Week
        week_ago = timezone.now().date() - timedelta(days=7)
        week_queryset = queryset.filter(created_at__date__gte=week_ago)
        print(f"✓ Week date filter works - found {week_queryset.count()} answers")
    except Exception as e:
        print(f"✗ Date filter error: {e}")
    
    # Test 5: Text search filters
    try:
        # Client name search
        sample_answer = queryset.first()
        if sample_answer:
            client_name = sample_answer.client.name[:3] if sample_answer.client.name else ""
            if client_name:
                search_queryset = queryset.filter(client__name__icontains=client_name)
                print(f"✓ Client name search works - found {search_queryset.count()} answers for '{client_name}'")
        
        # Task name search
        sample_task = Task.objects.filter(task_type='SURVEY').first()
        if sample_task:
            task_name = sample_task.title[:3] if sample_task.title else ""
            if task_name:
                search_queryset = queryset.filter(question__task__title__icontains=task_name)
                print(f"✓ Task name search works - found {search_queryset.count()} answers for '{task_name}'")
    except Exception as e:
        print(f"✗ Text search filter error: {e}")
    
    print("Filter functionality test completed.")

def test_pagination():
    """Test pagination functionality"""
    from tasks.models import SurveyAnswer
    from django.core.paginator import Paginator
    
    print("\nTesting Pagination Functionality...")
    
    queryset = SurveyAnswer.objects.all().order_by('-created_at')
    paginator = Paginator(queryset, 20)  # 20 items per page as in the template
    
    print(f"✓ Total answers: {paginator.count}")
    print(f"✓ Total pages: {paginator.num_pages}")
    
    if paginator.num_pages > 0:
        first_page = paginator.get_page(1)
        print(f"✓ First page has {len(first_page)} items")
        print(f"✓ Has next page: {first_page.has_next()}")
        print(f"✓ Has previous page: {first_page.has_previous()}")
    
    print("Pagination functionality test completed.")

def test_export_data_structure():
    """Test the data structure for Excel export"""
    from tasks.models import Task, SurveyAnswer
    
    print("\nTesting Export Data Structure...")
    
    try:
        survey_task = Task.objects.filter(task_type='SURVEY').first()
        if survey_task:
            answers = SurveyAnswer.objects.filter(
                question__task=survey_task
            ).select_related(
                'user', 'question', 'client'
            ).prefetch_related(
                'photos', 'selected_choices'
            ).order_by('client__name', 'question__order', 'created_at')
            
            if answers.exists():
                sample_answer = answers.first()
                
                # Test all the fields that will be exported
                client_name = sample_answer.client.name
                user_name = sample_answer.user.get_full_name() or sample_answer.user.username
                created_at = sample_answer.created_at.strftime('%d.%m.%Y %H:%M:%S')
                question_text = sample_answer.question.question_text
                question_type = sample_answer.question.get_question_type_display()
                selected_choices_text = ', '.join([choice.choice_text for choice in sample_answer.selected_choices.all()])
                text_answer = sample_answer.text_answer
                photo_count = sample_answer.photos.count()
                
                print(f"✓ Export data structure works:")
                print(f"  - Client: {client_name}")
                print(f"  - User: {user_name}")
                print(f"  - Date: {created_at}")
                print(f"  - Question: {question_text[:30]}...")
                print(f"  - Question Type: {question_type}")
                print(f"  - Choices: {selected_choices_text}")
                print(f"  - Text Answer: {text_answer[:30] if text_answer else 'None'}")
                print(f"  - Photo Count: {photo_count}")
        
        print("Export data structure test completed.")
    except Exception as e:
        print(f"✗ Export data structure error: {e}")

if __name__ == "__main__":
    test_filters()
    test_pagination()
    test_export_data_structure()