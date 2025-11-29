"""
Authentication and user management views.

This module provides views for user authentication, registration,
and profile management. Follows SOLID principles by separating
authentication logic from business logic.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext as _
from django.db import models
from tasks.models import Task, TaskStatus

class LoginView(TemplateView):
    """
    Login view for user authentication.
    
    Attributes
    ----------
    template_name : str
        Template name for login page
    
    Methods
    -------
    get(request, *args, **kwargs)
        Handle GET request for login page
    post(request, *args, **kwargs)
        Handle POST request for login form submission
    """
    
    template_name = 'users/login.html'
    
    def get(self, request, *args, **kwargs):
        """Handle GET request for login page."""
        if request.user.is_authenticated:
            return redirect('home')
        form = AuthenticationForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request, *args, **kwargs):
        """Handle POST request for login form submission."""
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Добро пожаловать, {user.username}!")
                return redirect('home')
            else:
                messages.error(request, _("Неверное имя пользователя или пароль."))
        else:
            messages.error(request, _("Неверное имя пользователя или пароль."))
        
        return render(request, self.template_name, {'form': form})

class LogoutView(LoginRequiredMixin, TemplateView):
    """
    Logout view for user session termination.
    
    Attributes
    ----------
    login_url : str
        URL to redirect to if user is not authenticated
    
    Methods
    -------
    get(request, *args, **kwargs)
        Handle GET request for logout
    """
    
    login_url = reverse_lazy('login')
    
    def get(self, request, *args, **kwargs):
        """Handle GET request for logout."""
        logout(request)
        messages.success(request, _("Вы успешно вышли из системы."))
        return redirect('login')

class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard view showing user-specific information.
    
    Attributes
    ----------
    template_name : str
        Template name for dashboard page
    login_url : str
        URL to redirect to if user is not authenticated
    
    Methods
    -------
    get_context_data(**kwargs)
        Get context data for dashboard template
    """
    
    template_name = 'dashboard.html'
    login_url = reverse_lazy('login')
    
    def get_context_data(self, **kwargs):
        """
        Get context data for dashboard template.
        
        Returns
        -------
        dict
            Context data containing active tasks, statistics, and moderator comments
        """
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get active tasks for employee
        context['active_tasks'] = []
        context['active_tasks_count'] = 0
        context['moderator_comment'] = ""
        context['completion_rate'] = 75  # Placeholder
        
        if user.role == 'EMPLOYEE':
            active_tasks = Task.objects.filter(
                status__in=[TaskStatus.SENT, TaskStatus.REWORK],
                is_active=True
            ).filter(
                models.Q(assigned_to=user) | models.Q(assigned_to__isnull=True)
            )
            context['active_tasks'] = active_tasks
            context['active_tasks_count'] = active_tasks.count()
        
        return context