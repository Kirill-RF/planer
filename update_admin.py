#!/usr/bin/env python3
"""
Script to update the SurveyAnswerAdmin class in the admin.py file
"""

def update_survey_answer_admin():
    # Read the current file
    with open('/workspace/tasks/admin.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Define the old and new class content
    old_class = '''@admin.register(SurveyAnswer)
class SurveyAnswerAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'client', 'get_selected_choices', 'text_answer_preview', 'has_photos', 'created_at')
    readonly_fields = ('user', 'question', 'selected_choices', 'text_answer', 'client', 'created_at')
    list_per_page = 20

    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False

    def get_selected_choices(self, obj):
        if obj.selected_choices.exists():
            return ', '.join([choice.choice_text for choice in obj.selected_choices.all()])
        return '-'
    get_selected_choices.short_description = _('Выбранные варианты')

    def text_answer_preview(self, obj):
        if obj.text_answer:
            return obj.text_answer[:50] + '...' if len(obj.text_answer) > 50 else obj.text_answer
        return '-'
    text_answer_preview.short_description = _('Текстовый ответ')

    def has_photos(self, obj):
        return obj.photos.exists()
    has_photos.short_description = _('Есть фото')
    has_photos.boolean = True'''

    new_class = '''@admin.register(SurveyAnswer)
class SurveyAnswerAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'client', 'get_selected_choices', 'text_answer_preview', 'has_photos', 'created_at')
    readonly_fields = ('user', 'question', 'selected_choices', 'text_answer', 'client', 'created_at', 'photos_display')
    list_filter = (
        'client', 
        'user', 
        'question__task__created_by',  # moderator
        ('created_at', admin.DateFieldListFilter),
        'question__task__task_type',
        TaskFilter,
    )
    search_fields = ('text_answer', 'user__username', 'client__name')
    list_per_page = 20

    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False

    def get_selected_choices(self, obj):
        if obj.selected_choices.exists():
            return ', '.join([choice.choice_text for choice in obj.selected_choices.all()])
        return '-'
    get_selected_choices.short_description = _('Выбранные варианты')

    def text_answer_preview(self, obj):
        if obj.text_answer:
            return obj.text_answer[:50] + '...' if len(obj.text_answer) > 50 else obj.text_answer
        return '-'
    text_answer_preview.short_description = _('Текстовый ответ')

    def has_photos(self, obj):
        return obj.photos.exists()
    has_photos.short_description = _('Есть фото')
    has_photos.boolean = True
    
    def photos_display(self, obj):
        """Display photos with click to enlarge functionality"""
        if obj.photos.exists():
            photos_html = []
            for photo_obj in obj.photos.all():
                if photo_obj.photo:
                    # Create HTML with click to enlarge functionality
                    photo_html = format_html(
                        '<div style="display: inline-block; margin: 5px;">'
                        '<a href="{}" target="_blank" title="Кликните для увеличения">'
                        '<img src="{}" style="width: 100px; height: 100px; object-fit: cover; border: 1px solid #ddd; cursor: zoom-in;" />'
                        '</a></div>',
                        photo_obj.photo.url, photo_obj.photo.url
                    )
                    photos_html.append(photo_html)
            return format_html('<div>{}</div>', format_html(''.join(photos_html)))
        return '-'
    photos_display.short_description = _('Фотоответы')'''
    
    # Replace the old class with the new class
    updated_content = content.replace(old_class, new_class)
    
    # Write the updated content back to the file
    with open('/workspace/tasks/admin.py', 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("Successfully updated SurveyAnswerAdmin class!")

if __name__ == "__main__":
    update_survey_answer_admin()