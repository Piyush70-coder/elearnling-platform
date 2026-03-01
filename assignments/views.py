from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
import json
from datetime import datetime

from .models import Assignment, TestCase, Submission, SubmissionResult, AssignmentUpload
from .forms import AssignmentForm, AssignmentUploadForm
from compiler.services import Judge0Service
from compiler import settings as compiler_settings
from courses.models import Course

def is_teacher(user):
    return user.is_authenticated and user.role == 'teacher'

@login_required
def assignment_list(request, course_id=None):
    """
    List all assignments for a course or all courses the student is enrolled in
    """
    if course_id:
        assignments = Assignment.objects.filter(course_id=course_id, is_active=True)
        context = {
            'assignments': assignments,
            'course_id': course_id
        }
    else:
        # Get assignments from all courses the student is enrolled in
        assignments = Assignment.objects.filter(
            course__enrollments__student=request.user,
            is_active=True
        ).select_related('course')
        context = {'assignments': assignments}
    
    return render(request, 'assignments/assignment_list.html', context)

@login_required
@user_passes_test(is_teacher)
@csrf_protect
def upload_assignment(request, course_id):
    """
    Allow teachers to upload assignment PDFs for a specific course
    """
    course = get_object_or_404(Course, id=course_id)
    
    # Check if the teacher is the instructor of the course
    if request.user != course.instructor and not request.user.is_staff:
        messages.error(request, "You don't have permission to upload assignments for this course.")
        return redirect('courses:course_list')
    
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.course = course
            assignment.created_by = request.user
            assignment.save()
            
            # Handle file upload if provided
            if 'assignment_file' in request.FILES:
                AssignmentUpload.objects.create(
                    assignment=assignment,
                    file=request.FILES['assignment_file'],
                    title=assignment.title,
                    description="Primary assignment document",
                    uploaded_by=request.user
                )
                messages.success(request, 'Assignment created and PDF uploaded successfully')
            else:
                messages.success(request, 'Assignment created successfully')
            
            return redirect('assignments:assignment_detail', assignment_id=assignment.id)
    else:
        form = AssignmentForm()
    
    context = {
        'course': course,
        'form': form,
        'programming_languages': dict(Assignment._meta.get_field('programming_language').choices),
        'difficulty_levels': dict(Assignment.DIFFICULTY_CHOICES)
    }
    return render(request, 'assignments/upload_assignment.html', context)

@login_required
@user_passes_test(is_teacher)
@csrf_protect
def manage_assignment_uploads(request, assignment_id):
    """
    Allow teachers to manage uploaded files for an assignment
    """
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    # Check if the teacher is the instructor of the course
    if request.user != assignment.course.instructor and not request.user.is_staff:
        messages.error(request, "You don't have permission to manage this assignment.")
        return redirect('courses:course_list')
    
    if request.method == 'POST':
        if 'upload_file' in request.POST:
            # Handle new file upload
            if 'file' in request.FILES:
                title = request.POST.get('title', request.FILES['file'].name)
                description = request.POST.get('description', '')
                
                AssignmentUpload.objects.create(
                    assignment=assignment,
                    file=request.FILES['file'],
                    title=title,
                    description=description,
                    uploaded_by=request.user
                )
                messages.success(request, 'File uploaded successfully')
        
        elif 'delete_file' in request.POST:
            # Handle file deletion
            file_id = request.POST.get('file_id')
            if file_id:
                try:
                    file_upload = AssignmentUpload.objects.get(id=file_id, assignment=assignment)
                    file_upload.delete()
                    messages.success(request, 'File deleted successfully')
                except AssignmentUpload.DoesNotExist:
                    messages.error(request, 'File not found')
        
        elif 'delete_main_file' in request.POST:
            # Handle main assignment file deletion
            if assignment.assignment_file:
                # Delete the file from storage
                assignment.assignment_file.delete()
                assignment.assignment_file = None
                assignment.save()
                messages.success(request, 'Main assignment file deleted successfully')
            else:
                messages.error(request, 'No main assignment file to delete')
    
    uploads = AssignmentUpload.objects.filter(assignment=assignment).order_by('-upload_date')
    context = {
        'assignment': assignment,
        'uploads': uploads
    }
    return render(request, 'assignments/manage_uploads.html', context)

@login_required
def view_assignment_uploads(request, assignment_id):
    """
    Allow students to view uploaded files for an assignment
    """
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    # Check if student is enrolled in the course
    if not assignment.course.enrollments.filter(student=request.user).exists():
        messages.error(request, "You must be enrolled in this course to view assignment files.")
        return redirect('courses:course_list')
    
    uploads = AssignmentUpload.objects.filter(assignment=assignment).order_by('-upload_date')
    context = {
        'assignment': assignment,
        'uploads': uploads
    }
    return render(request, 'assignments/view_uploads.html', context)

@login_required
def course_assignment_uploads(request, course_id=None):
    """
    Allow students to view all uploaded files for assignments in a specific course or all enrolled courses
    """
    if course_id:
        # Check if student is enrolled in the course
        course = get_object_or_404(Course, id=course_id)
        if not course.enrollments.filter(student=request.user).exists():
            messages.error(request, "You must be enrolled in this course to view assignment files.")
            return redirect('courses:course_list')
        
        # Get all assignments for this course
        assignments = Assignment.objects.filter(course_id=course_id, is_active=True)
    else:
        # Get assignments from all courses the student is enrolled in
        assignments = Assignment.objects.filter(
            course__enrollments__student=request.user,
            is_active=True
        ).select_related('course')
    
    # Get all uploads for these assignments
    assignment_uploads = []
    for assignment in assignments:
        uploads = AssignmentUpload.objects.filter(assignment=assignment).order_by('-upload_date')
        if uploads.exists():
            assignment_uploads.append({
                'assignment': assignment,
                'uploads': uploads
            })
    
    context = {
        'assignment_uploads': assignment_uploads,
        'course_id': course_id
    }
    return render(request, 'assignments/course_assignment_uploads.html', context)

@login_required
def assignment_detail(request, assignment_id):
    """
    Show assignment details and submission form
    """
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    # Check if student is enrolled in the course
    if not assignment.course.enrollments.filter(student=request.user).exists():
        messages.error(request, "You must be enrolled in this course to view assignments.")
        return redirect('courses:course_list')
    
    # Get student's submissions for this assignment
    submissions = Submission.objects.filter(
        assignment=assignment,
        student=request.user
    ).order_by('-submitted_at')
    
    context = {
        'assignment': assignment,
        'submissions': submissions,
        'starter_code': assignment.starter_code,
    }
    return render(request, 'assignments/assignment_detail.html', context)

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def submit_assignment(request, assignment_id):
    """
    Submit code for an assignment and run auto-grading
    """
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    # Check if student is enrolled in the course
    if not assignment.course.enrollments.filter(student=request.user).exists():
        return JsonResponse({
            'success': False,
            'error': 'You must be enrolled in this course to submit assignments.'
        })
    
    # Check if assignment is still active
    if not assignment.is_active or (assignment.due_date and assignment.due_date < timezone.now()):
        return JsonResponse({
            'success': False,
            'error': 'This assignment is no longer accepting submissions.'
        })
    
    try:
        data = json.loads(request.body)
        code = data.get('code', '').strip()
        
        if not code:
            return JsonResponse({
                'success': False,
                'error': 'Code submission cannot be empty'
            })
            
        # Validate code size
        if len(code) > compiler_settings.MAX_CODE_SIZE:
            return JsonResponse({
                'success': False,
                'error': f'Code exceeds maximum size limit of {compiler_settings.MAX_CODE_SIZE} characters'
            })
        
        # Create submission record
        submission = Submission.objects.create(
            assignment=assignment,
            student=request.user,
            code=code,
            status='pending'
        )
        
        # Start auto-grading process
        grade_submission(submission.id)
        
        return JsonResponse({
            'success': True,
            'submission_id': submission.id,
            'message': 'Submission received and grading started'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def submission_detail(request, submission_id):
    """
    Show details of a specific submission including test results
    """
    submission = get_object_or_404(Submission, id=submission_id)
    
    # Security check - only allow viewing own submissions
    if submission.student != request.user:
        messages.error(request, "You can only view your own submissions.")
        return redirect('assignments:assignment_list')
    
    context = {
        'submission': submission,
        'results': submission.results.all().select_related('test_case'),
        'assignment': submission.assignment
    }
    return render(request, 'assignments/submission_detail.html', context)

@login_required
def submission_status(request, submission_id):
    """
    API endpoint to check submission status
    """
    submission = get_object_or_404(Submission, id=submission_id)
    
    # Security check - only allow viewing own submissions
    if submission.student != request.user:
        return JsonResponse({
            'success': False,
            'error': 'Unauthorized'
        })
    
    return JsonResponse({
        'success': True,
        'status': submission.status,
        'score': submission.score,
        'graded': submission.graded_at is not None
    })

@login_required
def test_result(request, result_id):
    """Get details of a specific test case result"""
    # Get the test result and verify it belongs to the current user
    result = get_object_or_404(SubmissionResult, id=result_id)
    if result.submission.student != request.user:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    # Prepare the response data
    data = {
        'success': True,
        'status': result.status,
        'status_display': result.get_status_display(),
        'execution_time': result.execution_time,
        'memory_used': result.memory_used,
        'output': result.output,
        'error_message': result.error_message
    }
    
    # Only include input and expected output for non-hidden test cases or if user is staff
    if not result.test_case.is_hidden or request.user.is_staff:
        data.update({
            'input': result.test_case.input_data,
            'expected_output': result.test_case.expected_output
        })
    
    return JsonResponse(data)

@login_required
def submission_list(request):
    """
    List all submissions made by the current student
    """
    # Get all submissions for the current user
    submissions = Submission.objects.filter(
        student=request.user
    ).select_related('assignment', 'assignment__course').order_by('-submitted_at')
    
    context = {
        'submissions': submissions,
    }
    
    return render(request, 'assignments/submission_list.html', context)

def grade_submission(submission_id):
    """
    Auto-grade a submission by running it against test cases
    This function can be called directly or via a background task
    """
    try:
        submission = Submission.objects.get(id=submission_id)
        assignment = submission.assignment
        test_cases = assignment.test_cases.all()
        
        # Update submission status
        submission.status = 'running'
        submission.save(update_fields=['status'])
        
        # Initialize Judge0 service
        judge0_service = Judge0Service()
        
        # Track results for scoring
        passed_tests = 0
        total_weight = 0
        
        # Process each test case
        for test_case in test_cases:
            total_weight += test_case.weight
            
            # Create a temporary code execution object for Judge0
            execution = {
                'language': assignment.programming_language,
                'source_code': submission.code,
                'stdin_data': test_case.input_data,
                'expected_output': test_case.expected_output.strip(),
                'time_limit': assignment.time_limit_seconds,
                'memory_limit': assignment.memory_limit_mb
            }
            
            # Submit to Judge0 and get result
            result = judge0_service.run_test_case(execution)
            
            # Create result record
            test_result = SubmissionResult.objects.create(
                submission=submission,
                test_case=test_case,
                status=result['status'],
                execution_time=result.get('execution_time', 0),
                memory_used=result.get('memory_used', 0),
                output=result.get('output', ''),
                error_message=result.get('error', '')
            )
            
            # Check if test passed
            if result['status'] == 'accepted':
                passed_tests += test_case.weight
        
        # Calculate final score
        if total_weight > 0:
            final_score = (passed_tests / total_weight) * assignment.max_score
        else:
            final_score = 0
            
        # Determine overall status
        if passed_tests == total_weight:
            overall_status = 'accepted'
        elif submission.results.filter(status='compilation_error').exists():
            overall_status = 'compilation_error'
        elif submission.results.filter(status='runtime_error').exists():
            overall_status = 'runtime_error'
        elif submission.results.filter(status='time_limit_exceeded').exists():
            overall_status = 'time_limit_exceeded'
        elif submission.results.filter(status='memory_limit_exceeded').exists():
            overall_status = 'memory_limit_exceeded'
        else:
            overall_status = 'wrong_answer'
        
        # Update submission with final results
        submission.status = overall_status
        submission.score = final_score
        submission.graded_at = timezone.now()
        submission.save(update_fields=['status', 'score', 'graded_at'])
        
        return True
        
    except Exception as e:
        # Log the error
        print(f"Error grading submission {submission_id}: {str(e)}")
        
        # Update submission status
        try:
            submission = Submission.objects.get(id=submission_id)
            submission.status = 'error'
            submission.error_message = str(e)
            submission.save(update_fields=['status', 'error_message'])
        except:
            pass
            
        return False
