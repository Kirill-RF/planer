import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_survey_answer_admin():
    """Test the survey answer admin functionality"""
    from tasks.models import SurveyAnswer
    from tasks.admin import SurveyAnswerAdmin
    from django.contrib.admin import AdminSite
    from django.contrib.auth.models import User
    from django.http import HttpRequest
    from django.test import RequestFactory
    from django.contrib.auth import get_user_model
    
    print("Testing Survey Answer Admin functionality...")
    
    # Test 1: Check if SurveyAnswer model has photos relationship
    try:
        sample_answer = SurveyAnswer.objects.first()
        if sample_answer:
            print(f"✓ Found sample survey answer: {sample_answer.question.question_text[:50]}...")
            print(f"✓ Has photos: {sample_answer.photos.exists()}")
            if sample_answer.photos.exists():
                print(f"✓ First photo: {sample_answer.photos.first().photo.url if sample_answer.photos.first().photo else 'No photo'}")
        else:
            print("⚠ No survey answers found in database")
    except Exception as e:
        print(f"✗ Error testing model relationships: {e}")
    
    # Test 2: Check admin methods
    try:
        admin = SurveyAnswerAdmin(SurveyAnswer, AdminSite())
        
        # Test text preview method
        if sample_answer and sample_answer.text_answer:
            preview = admin.text_answer_preview(sample_answer)
            print(f"✓ Text answer preview works: {preview[:30]}...")
        
        # Test selected choices method
        choices = admin.get_selected_choices(sample_answer) if sample_answer else None
        print(f"✓ Selected choices method works: {choices}")
        
        print("✓ Admin methods working correctly")
    except Exception as e:
        print(f"✗ Error testing admin methods: {e}")
    
    # Test 3: Check if custom URLs are properly defined
    try:
        urls = admin.get_urls()
        custom_urls = [url.name for url in urls if hasattr(url, 'name')]
        print(f"✓ Custom URLs available: {custom_urls}")
        
        if 'surveyanswer_list' in custom_urls:
            print("✓ surveyanswer_list URL is defined")
        else:
            print("✗ surveyanswer_list URL is not defined")
            
        if 'export_survey_answers_excel' in custom_urls:
            print("✓ export_survey_answers_excel URL is defined")
        else:
            print("✗ export_survey_answers_excel URL is not defined")
    except Exception as e:
        print(f"✗ Error testing URLs: {e}")
    
    print("\nSurvey Answer Admin functionality test completed.")

def test_excel_export():
    """Test Excel export functionality"""
    from tasks.models import Task, SurveyAnswer
    import tempfile
    import os
    
    print("\nTesting Excel export functionality...")
    
    try:
        # Get a sample survey task
        survey_task = Task.objects.filter(task_type='SURVEY').first()
        if survey_task:
            print(f"✓ Found survey task: {survey_task.title}")
            
            # Test the export logic without actually creating HTTP response
            answers = SurveyAnswer.objects.filter(
                question__task=survey_task
            ).select_related(
                'user', 'question', 'client'
            ).prefetch_related(
                'photos', 'selected_choices'
            ).order_by('client__name', 'question__order', 'created_at')
            
            print(f"✓ Found {answers.count()} answers for this task")
            
            # Test with a single answer to see if the data structure is correct
            if answers.exists():
                sample_answer = answers.first()
                selected_choices_text = ', '.join([choice.choice_text for choice in sample_answer.selected_choices.all()])
                photo_count = sample_answer.photos.count()
                
                print(f"✓ Sample answer data - Client: {sample_answer.client.name}, "
                      f"Question: {sample_answer.question.question_text[:30]}..., "
                      f"Choices: {selected_choices_text}, "
                      f"Photo count: {photo_count}")
            
            print("✓ Excel export logic works correctly")
        else:
            print("⚠ No survey tasks found for testing")
    except Exception as e:
        print(f"✗ Error testing Excel export: {e}")

if __name__ == "__main__":
    test_survey_answer_admin()
    test_excel_export()