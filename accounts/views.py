from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.http import require_http_methods
from .models import User
from .forms import CustomUserCreationForm

def register_view(request):
    """User registration view for students, teachers, and admins"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def login_view(request):
    """User login view"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}.")
                # Redirect based on user role
                if user.is_admin:
                    return redirect('accounts:admin_dashboard')
                elif user.is_teacher:
                    return redirect('accounts:teacher_dashboard')
                else:
                    return redirect('accounts:student_dashboard')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

@require_http_methods(["POST"])
def logout_view(request):
    """User logout view"""
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('home')

@login_required
def profile_view(request):
    """User profile view"""
    return render(request, 'accounts/profile.html', {'user': request.user})

@login_required
def student_dashboard(request):
    """Student dashboard view"""
    if not request.user.is_student:
        messages.error(request, "Access denied. Students only.")
        return redirect('home')
    
    # Get student's enrolled courses and progress
    enrollments = request.user.enrollments.filter(is_active=True)
    
    context = {
        'enrollments': enrollments,
        'total_courses': enrollments.count(),
    }
    return render(request, 'accounts/student_dashboard.html', context)

@login_required
def teacher_dashboard(request):
    """Teacher dashboard view"""
    if not request.user.is_teacher:
        messages.error(request, "Access denied. Teachers only.")
        return redirect('home')
    
    # Get courses taught by the teacher
    courses = request.user.courses_taught.filter(is_active=True)
    
    context = {
        'courses': courses,
        'total_courses': courses.count(),
    }
    return render(request, 'accounts/teacher_dashboard.html', context)

@login_required
def admin_dashboard(request):
    """Admin dashboard view"""
    if not request.user.is_admin:
        messages.error(request, "Access denied. Administrators only.")
        return redirect('home')
    
    from courses.models import Course, Enrollment
    from assignments.models import Assignment, Submission
    
    # Get statistics for admin dashboard
    total_users = User.objects.count()
    total_courses = Course.objects.count()
    total_assignments = Assignment.objects.count()
    total_submissions = Submission.objects.count()
    
    context = {
        'total_users': total_users,
        'total_courses': total_courses,
        'total_assignments': total_assignments,
        'total_submissions': total_submissions,
    }
    return render(request, 'accounts/admin_dashboard.html', context)