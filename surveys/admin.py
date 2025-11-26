# surveys/admin.py
from django.contrib import admin
from .models import Survey, Question, Option, Client, Employee, Holding, PhotoReport, Photo


class OptionInline(admin.TabularInline):
    model = Option
    extra = 1


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    inlines = [OptionInline]
    fields = ('text', 'question_type', 'required')


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title',)
    inlines = [QuestionInline]
    ordering = ('-created_at',)





@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'position', 'password')
    search_fields = ('full_name',)
    list_filter = ('position',)


@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('report', 'is_high_quality', 'image')
    list_filter = ('is_high_quality', 'report__client')
    readonly_fields = ('report', 'image', 'latitude', 'longitude', 'detected_address')
    fields = ('report', 'image', 'latitude', 'longitude', 'detected_address', 'is_high_quality')
    

@admin.register(PhotoReport)
class PhotoReportAdmin(admin.ModelAdmin):
    list_display = ('client', 'employee', 'assigned_to', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'client__holding', 'employee', 'assigned_to', 'moderator')
    search_fields = ('client__full_name', 'employee__full_name', 'address')
    # Include all important fields in the form
    fields = (
        'client', 'employee', 'created_by', 'assigned_to', 'assignment_comment',
        'stand_count', 'address', 'status', 'moderator', 'rejected_reason'
    )
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('client', 'employee', 'created_by', 'assigned_to', 'moderator')  # For better performance with many records
    

class PhotoReportInline(admin.TabularInline):
    model = PhotoReport
    extra = 0
    readonly_fields = ('employee', 'assigned_to', 'stand_count', 'address', 'status', 'created_at', 'updated_at')
    fields = ('employee', 'assigned_to', 'stand_count', 'address', 'status', 'created_at', 'updated_at')
    can_delete = False
    show_change_link = True  # Allows clicking to see full details


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'email', 'holding', 'employee')
    list_filter = ('holding', 'employee')
    search_fields = ('full_name', 'email')
    ordering = ('full_name',)
    inlines = [PhotoReportInline]  # Shows photo reports history for each client