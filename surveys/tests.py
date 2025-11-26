from django.test import TestCase
from django.contrib.auth.models import User
from surveys.models import Survey, Question, Option, Client, Employee, Holding, PhotoReport, Photo
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile


class SurveyModelTest(TestCase):
    def setUp(self):
        self.holding = Holding.objects.create(name="Test Holding")
        self.employee = Employee.objects.create(full_name="John Doe", position="Manager")
        self.client = Client.objects.create(
            full_name="Test Client",
            holding=self.holding,
            employee=self.employee
        )
        self.survey = Survey.objects.create(title="Test Survey", is_active=True)

    def test_survey_creation(self):
        """Test survey model creation"""
        self.assertEqual(self.survey.title, "Test Survey")
        self.assertTrue(self.survey.is_active)

    def test_client_creation(self):
        """Test client model creation"""
        self.assertEqual(self.client.full_name, "Test Client")
        self.assertEqual(self.client.holding, self.holding)
        self.assertEqual(self.client.employee, self.employee)


class PhotoReportModelTest(TestCase):
    def setUp(self):
        self.holding = Holding.objects.create(name="Test Holding")
        self.employee1 = Employee.objects.create(full_name="John Doe", position="Manager")
        self.employee2 = Employee.objects.create(full_name="Jane Smith", position="Moderator")
        self.client = Client.objects.create(
            full_name="Test Client",
            holding=self.holding,
            employee=self.employee1
        )

    def test_photo_report_creation(self):
        """Test photo report model creation"""
        report = PhotoReport.objects.create(
            client=self.client,
            employee=self.employee1,
            stand_count=5,
            address="Test Address",
            status='draft'
        )
        self.assertEqual(report.client, self.client)
        self.assertEqual(report.employee, self.employee1)
        self.assertEqual(report.stand_count, 5)
        self.assertEqual(report.status, 'draft')


class ViewsTest(TestCase):
    def setUp(self):
        self.holding = Holding.objects.create(name="Test Holding")
        self.employee = Employee.objects.create(full_name="John Doe", position="Manager")
        self.client_obj = Client.objects.create(
            full_name="Test Client",
            holding=self.holding,
            employee=self.employee
        )
        self.survey = Survey.objects.create(title="Test Survey", is_active=True)
        self.question = Question.objects.create(
            survey=self.survey,
            text="Test Question",
            question_type="text"
        )

    def test_home_view(self):
        """Test home view"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_upload_clients_view(self):
        """Test upload clients view"""
        response = self.client.get(reverse('upload_clients'))
        self.assertEqual(response.status_code, 200)

    def test_fill_survey_view(self):
        """Test fill survey view"""
        response = self.client.get(reverse('fill_survey', args=[self.survey.id]))
        self.assertEqual(response.status_code, 200)
