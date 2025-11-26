# surveys/admin.py
from django.contrib import admin
from .models import Survey, Question, Option, Client, Employee, Holding, PhotoReport, Photo, ModeratorComment


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


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'email', 'holding', 'employee')
    list_filter = ('holding', 'employee')
    search_fields = ('full_name', 'email')
    ordering = ('full_name',)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'position')
    search_fields = ('full_name',)


@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(PhotoReport)
class PhotoReportAdmin(admin.ModelAdmin):
    list_display = ('client', 'employee', 'status', 'created_at')
    list_filter = ('status', 'client', 'employee')


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('report', 'is_high_quality')