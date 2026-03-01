from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def is_teacher(function):
    """Decorator to check if the user is a teacher"""
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.role == 'teacher':
            return function(request, *args, **kwargs)
        else:
            messages.error(request, "You must be a teacher to access this page.")
            return redirect('home')
    return wrap

def is_student(function):
    """Decorator to check if the user is a student"""
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.role == 'student':
            return function(request, *args, **kwargs)
        else:
            messages.error(request, "You must be a student to access this page.")
            return redirect('home')
    return wrap

def is_admin(function):
    """Decorator to check if the user is an admin"""
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.is_staff or request.user.is_superuser:
            return function(request, *args, **kwargs)
        else:
            messages.error(request, "You must be an administrator to access this page.")
            return redirect('home')
    return wrap