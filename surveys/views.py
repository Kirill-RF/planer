# surveys/views.py
import pandas as pd
import json
import re
import tempfile
import os
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from collections import defaultdict
from .models import (
    Survey, Question, Option, Client, Employee, Response,
    PhotoReport, Photo, ModeratorComment, Holding,
    normalize_company_name, normalize_phone
)
from .utils import is_high_quality_image
# === ФУНКЦИЯ ЗАГРУЗКИ КЛИЕНТОВ (восстановлена!) ===

def upload_clients(request):
    if request.method == 'POST':
        if 'excel_file' in request.FILES and 'preview' in request.POST:
            file = request.FILES['excel_file']
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                    for chunk in file.chunks():
                        tmp.write(chunk)
                    tmp_path = tmp.name

                df = pd.read_excel(tmp_path)
                if 'full_name' not in df.columns:
                    os.unlink(tmp_path)
                    messages.error(request, "Файл должен содержать столбец 'full_name'")
                    return render(request, 'surveys/upload_clients.html')

                preview_data = []
                for _, row in df.iterrows():
                    full_name_raw = row.get('full_name', '')
                    full_name = normalize_company_name(str(full_name_raw))
                    phone_raw = row.get('phone')
                    phone = normalize_phone(phone_raw)
                    email = str(row.get('email', '')).strip()
                    if email == 'nan' or not email:
                        email = ''
                    holding_name = str(row.get('holding', '')).strip() or None
                    employee_name = str(row.get('employee_full_name', '')).strip() or None

                    errors = []
                    if not full_name:
                        errors.append("Пустое имя/название")
                    if phone_raw and not phone:
                        errors.append(f"Неверный телефон: {phone_raw}")
                    if email and '@' not in email:
                        errors.append(f"Неверный email: {email}")

                    preview_data.append({
                        'full_name': full_name,
                        'phone': phone,
                        'email': email,
                        'holding': holding_name,
                        'employee_full_name': employee_name,
                        'errors': errors,
                        'is_valid': len(errors) == 0
                    })

                valid_count = sum(1 for r in preview_data if r['is_valid'])
                request.session['tmp_excel_path'] = tmp_path
                return render(request, 'surveys/upload_clients.html', {
                    'preview_data': preview_data,
                    'valid_count': valid_count,
                    'invalid_count': len(preview_data) - valid_count,
                })

            except Exception as e:
                messages.error(request, f"Ошибка при анализе файла: {e}")
                return render(request, 'surveys/upload_clients.html')

        elif 'confirm_upload' in request.POST:
            tmp_path = request.session.get('tmp_excel_path')
            if not tmp_path or not os.path.exists(tmp_path):
                messages.error(request, "Файл устарел. Загрузите заново.")
                return redirect('upload_clients')

            try:
                df = pd.read_excel(tmp_path)
                created = updated = 0
                for _, row in df.iterrows():
                    full_name = normalize_company_name(str(row.get('full_name', '')))
                    if not full_name:
                        continue

                    holding = None
                    holding_name = str(row.get('holding', '')).strip()
                    if holding_name:
                        holding, _ = Holding.objects.get_or_create(name=holding_name)

                    employee = None
                    emp_name = str(row.get('employee_full_name', '')).strip()
                    if emp_name:
                        try:
                            employee = Employee.objects.get(full_name=emp_name)
                        except Employee.DoesNotExist:
                            pass

                    phone = normalize_phone(row.get('phone'))
                    email = str(row.get('email', '')).strip()
                    if email == 'nan' or not email:
                        email = ''

                    obj, created_flag = Client.objects.update_or_create(
                        full_name=full_name,
                        defaults={
                            'phone': phone or '',
                            'email': email,
                            'holding': holding,
                            'employee': employee,
                        }
                    )
                    if created_flag:
                        created += 1
                    else:
                        updated += 1

                messages.success(request, f"Загружено: {created} новых, {updated} обновлено.")
            except Exception as e:
                messages.error(request, f"Ошибка при сохранении: {e}")
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                request.session.pop('tmp_excel_path', None)

            return redirect('upload_clients')

    return render(request, 'surveys/upload_clients.html')


# === ОСТАЛЬНЫЕ VIEW (без изменений) ===

def create_photo_report(request):
    if request.method == 'POST':
        client_id = request.POST.get('client_id')
        stand_count = request.POST.get('stand_count')
        address = request.POST.get('address', '')
        client = get_object_or_404(Client, id=client_id)
        employee = get_object_or_404(Employee, id=request.POST.get('employee_id'))

        report = PhotoReport.objects.create(
            client=client,
            employee=employee,
            created_by=employee,
            stand_count=stand_count,
            address=address,
            status='submitted'
        )

        for f in request.FILES.getlist('photos'):
            photo_path = f.temporary_file_path() if hasattr(f, 'temporary_file_path') else None
            is_high = is_high_quality_image(photo_path) if photo_path else False
            Photo.objects.create(
                report=report,
                image=f,
                is_high_quality=is_high
            )

        messages.success(request, "Фотоотчёт отправлен на проверку!")
        return redirect('home')

    clients = Client.objects.all()
    employees = Employee.objects.all()
    return render(request, 'surveys/create_photo_report.html', {
        'clients': clients,
        'employees': employees,
    })


def pending_photo_reports(request):
    """Модератор: список отчётов на проверку + назначенные"""
    # Отчёты, отправленные сотрудниками (status='submitted')
    submitted_reports = PhotoReport.objects.filter(status='submitted')
    # Отчёты, назначенные модератором (status='draft' и assigned_to не None)
    assigned_reports = PhotoReport.objects.filter(status='draft', assigned_to__isnull=False)

    all_reports = (submitted_reports | assigned_reports).distinct()
    return render(request, 'surveys/pending_reports.html', {
        'reports': all_reports,
        'user_is_moderator': True  # для шаблона
    })


def review_photo_report(request, report_id):
    report = get_object_or_404(PhotoReport, id=report_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            report.status = 'approved'
            report.moderator = get_object_or_404(Employee, id=request.POST.get('moderator_id'))
            report.save()
            messages.success(request, "Отчёт принят!")
        elif action == 'reject':
            report.status = 'rejected'
            report.rejected_reason = request.POST.get('reason')
            report.moderator = get_object_or_404(Employee, id=request.POST.get('moderator_id'))
            report.save()
            messages.warning(request, "Отчёт возвращён на доработку.")
        return redirect('pending_photo_reports')
    moderators = Employee.objects.all()
    return render(request, 'surveys/review_report.html', {
        'report': report,
        'moderators': moderators,
    })


# surveys/views.py

def assign_photo_report(request):
    """Модератор назначает задачу на фотоотчёт"""
    if request.method == 'POST':
        client_id = request.POST.get('client_id')
        assigned_to_id = request.POST.get('assigned_to_id')
        stand_count = request.POST.get('stand_count', 1)
        comment = request.POST.get('assignment_comment', '')
        
        client = get_object_or_404(Client, id=client_id)
        assigned_to = get_object_or_404(Employee, id=assigned_to_id)

        # Создаём задачу — СОХРАНЯЕМ В БД!
        report = PhotoReport.objects.create(
            client=client,
            employee=assigned_to,          # сотрудник, который выполнит
            assigned_to=assigned_to,       # явное назначение
            stand_count=stand_count,
            status='draft',
            assignment_comment=comment
        )

        messages.success(request, f"Задача назначена сотруднику {assigned_to.full_name}!")
        return redirect('pending_photo_reports')

    # GET-запрос — показываем форму
    clients = Client.objects.all()
    employees = Employee.objects.all()
    return render(request, 'surveys/assign_photo_report.html', {
        'clients': clients,
        'employees': employees,
    })


def my_rejected_reports(request):
    reports = PhotoReport.objects.filter(status='rejected')
    return render(request, 'surveys/my_rejected_reports.html', {'reports': reports})


def fill_survey(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id, is_active=True)
    clients = Client.objects.all()
    employees = Employee.objects.all()

    if request.method == 'POST':
        employee = Employee.objects.get(id=request.POST['employee_id'])
        client = Client.objects.get(id=request.POST['client_id'])

        for question in survey.questions.all():
            response = Response.objects.create(
                survey=survey,
                question=question,
                employee=employee,
                client=client
            )

            answer_key = f"q_{question.id}"
            if question.question_type == 'text':
                response.text_answer = request.POST.get(answer_key)
            elif question.question_type == 'photo':
                if answer_key in request.FILES:
                    response.photo = request.FILES[answer_key]
            elif question.question_type in ['radio', 'single_select']:
                opt_id = request.POST.get(answer_key)
                if opt_id:
                    try:
                        option = Option.objects.get(id=opt_id)
                        response.selected_options.add(option)
                    except Option.DoesNotExist:
                        pass
            elif question.question_type in ['checkbox', 'multi_select']:
                opt_ids = request.POST.getlist(f"{answer_key}[]")
                for opt_id in opt_ids:
                    try:
                        option = Option.objects.get(id=opt_id)
                        response.selected_options.add(option)
                    except Option.DoesNotExist:
                        continue

            response.save()

        messages.success(request, "Анкета успешно отправлена!")
        return redirect('fill_survey', survey_id=survey.id)

    return render(request, 'surveys/fill_survey.html', {
        'survey': survey,
        'clients': clients,
        'employees': employees,
    })


def aggregate_responses(responses_qs):
    data = defaultdict(lambda: defaultdict(int))
    question_map = {}
    option_map = {}

    for resp in responses_qs:
        q = resp.question
        question_map[q.id] = q.text
        if q.question_type in ['single_select', 'multi_select', 'radio', 'checkbox']:
            for opt in resp.selected_options.all():
                data[q.id][opt.id] += 1
                option_map[opt.id] = opt.text
        elif q.question_type == 'text':
            data[q.id]['text'] += 1
            option_map['text'] = 'Текстовые ответы'

    base_colors = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
        '#FF9F40', '#7B68EE', '#00CED1', '#FFD700', '#8B4513'
    ]

    chart_data = []
    for q_id, opt_counts in data.items():
        total = sum(opt_counts.values())
        labels = []
        counts = []
        percentages = []
        colors = []
        for i, (opt_id, count) in enumerate(opt_counts.items()):
            labels.append(option_map.get(opt_id, str(opt_id)))
            counts.append(count)
            percentages.append(round((count / total * 100), 1) if total > 0 else 0)
            colors.append(base_colors[i % len(base_colors)])
        chart_data.append({
            'question': question_map[q_id],
            'labels': labels,
            'counts': counts,
            'percentages': percentages,
            'colors': colors,
            'total': total
        })
    return chart_data


def results_overview(request):
    surveys = Survey.objects.all()
    clients = Client.objects.all()
    employees = Employee.objects.all()

    last_survey_id = Response.objects.order_by('-submitted_at').values_list('survey_id', flat=True).first()
    survey_id = request.GET.get('survey') or last_survey_id
    client_id = request.GET.get('client')
    employee_id = request.GET.get('employee')
    view_mode = request.GET.get('view', 'detail')

    if not survey_id:
        grouped_responses = {}
        my_stats_json = company_stats_json = None
    else:
        responses = Response.objects.filter(survey_id=survey_id).select_related(
            'survey', 'question', 'client', 'employee'
        ).prefetch_related('selected_options')

        if client_id:
            responses = responses.filter(client_id=client_id)
        if employee_id:
            responses = responses.filter(employee_id=employee_id)

        grouped_responses = {}
        for resp in responses:
            key = (resp.client_id, resp.employee_id, resp.submitted_at.date())
            if key not in grouped_responses:
                grouped_responses[key] = {
                    'survey': resp.survey,
                    'client': resp.client,
                    'employee': resp.employee,
                    'date': resp.submitted_at.date(),
                    'answers': []
                }
            grouped_responses[key]['answers'].append(resp)

        my_stats_json = company_stats_json = None
        if employee_id:
            my_qs = Response.objects.filter(survey_id=survey_id, employee_id=employee_id)
            my_stats = aggregate_responses(my_qs)
            my_stats_json = json.dumps(my_stats, cls=DjangoJSONEncoder)

        all_qs = Response.objects.filter(survey_id=survey_id)
        company_stats = aggregate_responses(all_qs)
        company_stats_json = json.dumps(company_stats, cls=DjangoJSONEncoder)

    context = {
        'surveys': surveys,
        'clients': clients,
        'employees': employees,
        'grouped_responses': grouped_responses.values(),
        'my_stats_json': my_stats_json,
        'company_stats_json': company_stats_json,
        'selected_survey': int(survey_id) if survey_id else None,
        'selected_client': int(client_id) if client_id else None,
        'selected_employee': int(employee_id) if employee_id else None,
        'view_mode': view_mode,
    }
    return render(request, 'surveys/results_overview.html', context)


# surveys/views.py — убедись, что в home есть:
def home(request):
    surveys = Survey.objects.filter(is_active=True)
    surveys_with_progress = []
    for survey in surveys:
        completed = Response.objects.filter(survey=survey).count()
        target = survey.target_count
        surveys_with_progress.append({
            'survey': survey,
            'target': target,
            'completed': completed,
        })
    return render(request, 'surveys/home.html', {
        'surveys_with_progress': surveys_with_progress,
        'user_is_moderator': request.user.is_staff,  # ← ВАЖНО: нужно для условий в шаблоне
    })

def my_photo_tasks(request):
    """Сотрудник: список назначенных ему задач и отправленных отчётов"""
    # Получаем текущего сотрудника (временно — по ID из сессии или параметру)
    # В будущем: request.user.employee
    employee_id = request.GET.get('employee_id')
    if not employee_id:
        # Пока просто берем первого сотрудника для демонстрации
        employee = Employee.objects.first()
    else:
        employee = get_object_or_404(Employee, id=employee_id)

    if not employee:
        return render(request, 'surveys/my_photo_tasks.html', {'tasks': []})

    # Назначенные задачи (статус draft)
    assigned_tasks = PhotoReport.objects.filter(assigned_to=employee, status='draft')
    # Отправленные отчёты (статус submitted или rejected)
    my_reports = PhotoReport.objects.filter(employee=employee).exclude(status='draft')

    all_tasks = (assigned_tasks | my_reports).distinct().order_by('-created_at')
    return render(request, 'surveys/my_photo_tasks.html', {
        'tasks': all_tasks,
    })