# surveys/views.py
import pandas as pd
import json
import re
import tempfile
import os
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
from .models import Survey, Question, Option, Client, Employee, Response, Holding
from collections import defaultdict


def normalize_company_name(name: str) -> str:
    if not name:
        return ""
    name = re.sub(r'\s+', ' ', name.strip())
    for abbr in ['ООО', 'ИП', 'ЗАО', 'ОАО', 'АО', 'ПАО', 'НКО']:
        name = re.sub(rf'\b{abbr.lower()}\b', abbr, name, flags=re.IGNORECASE)
    return name


def normalize_phone(phone):
    if not phone:
        return None
    cleaned = re.sub(r'[^\d+]', '', str(phone))
    if cleaned.startswith('8'):
        cleaned = '+7' + cleaned[1:]
    elif cleaned.startswith('7') and not cleaned.startswith('+7'):
        cleaned = '+' + cleaned
    elif not cleaned.startswith('+7'):
        return None
    if len(cleaned) == 12:
        return cleaned
    return None


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


@login_required
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


@login_required
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
    
    # Проверяем, является ли пользователь модератором (администратором)
    user_is_moderator = request.user.is_staff
    
    # Также проверяем, является ли пользователь связанным сотрудником
    user_is_employee = False
    try:
        employee = Employee.objects.get(user=request.user)
        user_is_employee = True
    except Employee.DoesNotExist:
        pass
    
    return render(request, 'surveys/home.html', {
        'surveys_with_progress': surveys_with_progress,
        'user_is_moderator': user_is_moderator,
        'user_is_employee': user_is_employee,
    })


# === ФОТООТЧЁТ ===

from .utils import is_high_quality_image
from .models import PhotoReport, Photo, ModeratorComment
import os

@login_required
def create_photo_report(request):
    """Сотрудник создаёт фотоотчёт"""
    if request.method == 'POST':
        client_id = request.POST.get('client_id')
        stand_count = request.POST.get('stand_count')
        address = request.POST.get('address', '')
        client = get_object_or_404(Client, id=client_id)
        employee = get_object_or_404(Employee, id=request.POST.get('employee_id'))

        report = PhotoReport.objects.create(
            client=client,
            employee=employee,
            stand_count=stand_count,
            address=address,
            status='submitted'
        )

        # Сохраняем фото
        for f in request.FILES.getlist('photos'):
            # Сохраняем файл во временный файл для проверки качества
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                for chunk in f.chunks():
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name

            is_high = is_high_quality_image(tmp_path)
            
            # Перемещаем файл в правильное место
            photo_instance = Photo.objects.create(
                report=report,
                image=f,
                is_high_quality=is_high
            )
            
            # Удаляем временный файл
            os.unlink(tmp_path)

        messages.success(request, "Фотоотчёт отправлен на проверку!")
        return redirect('home')

    clients = Client.objects.all()
    employees = Employee.objects.all()
    return render(request, 'surveys/create_photo_report.html', {
        'clients': clients,
        'employees': employees,
    })


@login_required
def pending_photo_reports(request):
    """Модератор: список отчётов на проверку"""
    reports = PhotoReport.objects.filter(status='submitted')
    return render(request, 'surveys/pending_reports.html', {'reports': reports})


@login_required
def review_photo_report(request, report_id):
    """Модератор: проверка отчёта"""
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


@login_required
def my_rejected_reports(request):
    """Сотрудник: список отчётов на доработку"""
    # В будущем можно фильтровать по request.user.employee
    reports = PhotoReport.objects.filter(status='rejected')
    return render(request, 'surveys/my_rejected_reports.html', {'reports': reports})


# === АУТЕНТИФИКАЦИЯ СОТРУДНИКОВ ===

def employee_login(request):
    """Аутентификация сотрудника"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Проверяем, связан ли пользователь с сотрудником
            try:
                employee = Employee.objects.get(user=user)
                login(request, user)
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            except Employee.DoesNotExist:
                messages.error(request, 'Пользователь не связан с сотрудником')
        else:
            messages.error(request, 'Неверный логин или пароль')
    
    return render(request, 'surveys/login.html')


def employee_logout(request):
    """Выход сотрудника"""
    logout(request)
    return redirect('home')


@login_required
def profile(request):
    """Страница профиля сотрудника"""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        employee = None
    
    return render(request, 'surveys/profile.html', {'employee': employee})