from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from reports.models import (
    EquipmentReport, Evaluation, Photo,
    EquipmentPhotoReportQuestion, EquipmentPhotoReportQuestionChoice,
    EquipmentPhotoReportAnswer, EquipmentPhotoReportAnswerPhoto
)
from tasks.models import Task, TaskType
from clients.models import Client
from users.models import CustomUser, UserRoles
from django.core.files.uploadedfile import SimpleUploadedFile
import os

User = get_user_model()


class EquipmentReportModelsTest(TestCase):
    """Test cases for equipment report models."""
    
    def setUp(self):
        """Set up test data."""
        # Create test user
        self.moderator = CustomUser.objects.create_user(
            username='moderator',
            password='testpass123',
            role=UserRoles.MODERATOR
        )
        
        self.employee = CustomUser.objects.create_user(
            username='employee',
            password='testpass123',
            role=UserRoles.EMPLOYEE
        )
        
        # Create test client
        self.client = Client.objects.create(
            name='Test Client',
            address='Test Address',
            trading_point_name='Test Trading Point',
            trading_point_address='Test Trading Point Address'
        )
        
        # Create test task
        self.task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            task_type=TaskType.EQUIPMENT_PHOTO,
            created_by=self.moderator
        )
        
        # Create test equipment report
        self.equipment_report = EquipmentReport.objects.create(
            client=self.client,
            employee=self.employee,
            date=timezone.now().date()
        )
        
        # Create test photo
        self.photo = Photo.objects.create(
            photo=SimpleUploadedFile(
                name='test_image.jpg',
                content=b'test_image_content',
                content_type='image/jpeg'
            ),
            description='Test Photo Description'
        )

    def test_equipment_report_creation(self):
        """Test equipment report creation."""
        self.assertEqual(self.equipment_report.client, self.client)
        self.assertEqual(self.equipment_report.employee, self.employee)
        self.assertEqual(self.equipment_report.date, timezone.now().date())
        self.assertEqual(str(self.equipment_report), f"Отчет по оборудованию для {self.client.name} ({self.equipment_report.date})")

    def test_evaluation_creation(self):
        """Test evaluation creation."""
        evaluation = Evaluation.objects.create(
            report=self.equipment_report,
            moderator=self.moderator,
            fullness_comment='Good fullness',
            no_foreign_goods_comment='No foreign goods',
            presentation_comment='Good presentation'
        )
        
        self.assertEqual(evaluation.report, self.equipment_report)
        self.assertEqual(evaluation.moderator, self.moderator)
        self.assertEqual(evaluation.fullness_comment, 'Good fullness')
        self.assertEqual(str(evaluation), f"Оценка от {self.moderator.username} для {self.equipment_report}")

    def test_photo_creation(self):
        """Test photo creation."""
        self.assertEqual(self.photo.description, 'Test Photo Description')
        self.assertTrue(self.photo.photo.name)  # Проверяем, что файл существует
        self.assertIn('test_image', self.photo.photo.name)  # Проверяем, что имя содержит 'test_image'


class EquipmentPhotoReportQuestionsTest(TestCase):
    """Test cases for equipment photo report questions and answers."""
    
    def setUp(self):
        """Set up test data."""
        # Create test user
        self.moderator = CustomUser.objects.create_user(
            username='moderator',
            password='testpass123',
            role=UserRoles.MODERATOR
        )
        
        self.employee = CustomUser.objects.create_user(
            username='employee',
            password='testpass123',
            role=UserRoles.EMPLOYEE
        )
        
        # Create test client
        self.client = Client.objects.create(
            name='Test Client',
            address='Test Address',
            trading_point_name='Test Trading Point',
            trading_point_address='Test Trading Point Address'
        )
        
        # Create test equipment report
        self.equipment_report = EquipmentReport.objects.create(
            client=self.client,
            employee=self.employee,
            date=timezone.now().date()
        )
        
        # Create test question
        self.question = EquipmentPhotoReportQuestion.objects.create(
            report=self.equipment_report,
            question_text='How is the equipment arranged?',
            question_type='TEXT'
        )
        
        # Create test choice
        self.choice = EquipmentPhotoReportQuestionChoice.objects.create(
            question=self.question,
            choice_text='Very well organized',
            is_correct=True
        )

    def test_question_creation(self):
        """Test question creation."""
        self.assertEqual(self.question.report, self.equipment_report)
        self.assertEqual(self.question.question_text, 'How is the equipment arranged?')
        self.assertEqual(self.question.question_type, 'TEXT')
        self.assertTrue(self.question.has_custom_choices())
        self.assertEqual(str(self.question), 'How is the equipment arranged?')

    def test_choice_creation(self):
        """Test choice creation."""
        self.assertEqual(self.choice.question, self.question)
        self.assertEqual(self.choice.choice_text, 'Very well organized')
        self.assertTrue(self.choice.is_correct)
        self.assertEqual(str(self.choice), 'Very well organized')

    def test_answer_creation(self):
        """Test answer creation."""
        answer = EquipmentPhotoReportAnswer.objects.create(
            question=self.question,
            user=self.employee,
            text_answer='The equipment is very well organized',
            client=self.client
        )
        
        self.assertEqual(answer.question, self.question)
        self.assertEqual(answer.user, self.employee)
        self.assertEqual(answer.text_answer, 'The equipment is very well organized')
        self.assertEqual(answer.client, self.client)
        self.assertIn(self.employee.username, str(answer))
        self.assertIn('How is the equipment arranged?', str(answer))

    def test_answer_photo_creation(self):
        """Test answer photo creation."""
        answer = EquipmentPhotoReportAnswer.objects.create(
            question=self.question,
            user=self.employee,
            text_answer='The equipment is very well organized',
            client=self.client
        )
        
        answer_photo = EquipmentPhotoReportAnswerPhoto.objects.create(
            answer=answer,
            photo=SimpleUploadedFile(
                name='answer_test_image.jpg',
                content=b'answer_test_image_content',
                content_type='image/jpeg'
            ),
            description='Test answer photo'
        )
        
        self.assertEqual(answer_photo.answer, answer)
        self.assertEqual(answer_photo.description, 'Test answer photo')
        self.assertTrue(answer_photo.photo.name)  # Проверяем, что файл существует
        self.assertIn('answer_test_image', answer_photo.photo.name)  # Проверяем, что имя содержит 'answer_test_image'