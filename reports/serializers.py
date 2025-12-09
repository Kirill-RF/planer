"""
Serializers for equipment photo reports and evaluations.

This module defines serializers for equipment reports and evaluations
that will be used in API endpoints.
"""

from rest_framework import serializers
from .models import EquipmentReport, Evaluation, Photo
from tasks.models import Task
from users.models import CustomUser
from clients.models import Client


class PhotoSerializer(serializers.ModelSerializer):
    """
    Serializer for Photo model.
    
    Parameters
    ----------
    photo : ImageField
        Photo file
    description : str
        Description of the photo
    created_at : datetime
        Creation timestamp
    """
    
    class Meta:
        model = Photo
        fields = ['id', 'photo', 'description', 'created_at']
        read_only_fields = ['created_at']


class EquipmentReportSerializer(serializers.ModelSerializer):
    """
    Serializer for EquipmentReport model.
    
    Parameters
    ----------
    id : int
        Report ID
    client : Client
        Client for the report
    employee : CustomUser
        Employee who created the report
    date : date
        Report date
    photos : list
        List of photos for the report
    created_at : datetime
        Creation timestamp
    updated_at : datetime
        Update timestamp
    """
    
    photos = PhotoSerializer(many=True, read_only=True)
    
    class Meta:
        model = EquipmentReport
        fields = ['id', 'client', 'employee', 'date', 'photos', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def to_representation(self, instance):
        """
        Customize the representation to include related data.
        """
        data = super().to_representation(instance)
        # Include client and employee details
        if instance.client:
            data['client_name'] = instance.client.name
        if instance.employee:
            data['employee_name'] = instance.employee.get_full_name() or instance.employee.username
        return data


class EvaluationSerializer(serializers.ModelSerializer):
    """
    Serializer for Evaluation model.
    
    Parameters
    ----------
    id : int
        Evaluation ID
    report : EquipmentReport
        The report being evaluated
    moderator : CustomUser
        Moderator who made the evaluation
    fullness_comment : str
        Comment about fullness
    no_foreign_goods_comment : str
        Comment about foreign goods
    presentation_comment : str
        Comment about presentation
    improvement_task : Task
        Task for improvement if needed
    created_at : datetime
        Creation timestamp
    updated_at : datetime
        Update timestamp
    """
    
    class Meta:
        model = Evaluation
        fields = [
            'id', 'report', 'moderator', 'fullness_comment', 
            'no_foreign_goods_comment', 'presentation_comment', 
            'improvement_task', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'moderator']

    def create(self, validated_data):
        """
        Create evaluation and optionally create improvement task.
        """
        # Set the current moderator from context
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['moderator'] = request.user
            
        evaluation = Evaluation.objects.create(**validated_data)
        
        # Create improvement task if any comments exist
        if (validated_data.get('fullness_comment') or 
            validated_data.get('no_foreign_goods_comment') or 
            validated_data.get('presentation_comment')):
            
            from tasks.models import Task, TaskStatus, TaskType
            
            # Create a new task for improvement
            task_description = []
            if validated_data.get('fullness_comment'):
                task_description.append(f"Наполнение: {validated_data['fullness_comment']}")
            if validated_data.get('no_foreign_goods_comment'):
                task_description.append(f"Посторонние товары: {validated_data['no_foreign_goods_comment']}")
            if validated_data.get('presentation_comment'):
                task_description.append(f"Оформление: {validated_data['presentation_comment']}")
            
            improvement_task = Task.objects.create(
                title=f"Доработка фотоотчета от {evaluation.report.date}",
                description="Необходимо внести доработки по замечаниям модератора:\n\n" + "\n".join(task_description),
                task_type=TaskType.EQUIPMENT_PHOTO,
                status=TaskStatus.SENT,
                assigned_to=evaluation.report.employee,
                client=evaluation.report.client,
                created_by=evaluation.moderator,
            )
            
            evaluation.improvement_task = improvement_task
            evaluation.save()
        
        return evaluation


class PhotoReportStatsSerializer(serializers.Serializer):
    """
    Serializer for photo report statistics.
    
    Parameters
    ----------
    client : Client
        Client data
    employee : CustomUser
        Employee data
    reports : list
        List of reports for the client
    evaluation : Evaluation
        Evaluation data if exists
    """
    
    client_id = serializers.IntegerField()
    client_name = serializers.CharField()
    employee_id = serializers.IntegerField()
    employee_name = serializers.CharField()
    reports = EquipmentReportSerializer(many=True)
    evaluation = EvaluationSerializer(required=False, allow_null=True)