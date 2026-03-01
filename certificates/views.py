from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, FileResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.utils import timezone

from .models import Certificate
from courses.models import Course, Enrollment
from .utils import generate_certificate_pdf

import os
import uuid

@login_required
def student_certificates(request):
    """View for students to see all their earned certificates"""
    certificates = Certificate.objects.filter(user=request.user).select_related('course')
    return render(request, 'certificates/student_certificates.html', {
        'certificates': certificates
    })

@login_required
def course_certificates(request, course_id):
    """View for teachers to see all certificates issued for a specific course"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is the instructor of this course
    if request.user != course.instructor and not request.user.is_staff:
        messages.error(request, "You don't have permission to view certificates for this course.")
        return redirect('courses:detail', course_id=course_id)
    
    certificates = Certificate.objects.filter(course=course).select_related('user')
    return render(request, 'certificates/course_certificates.html', {
        'course': course,
        'certificates': certificates
    })

@login_required
def generate_certificate(request, enrollment_id):
    """Generate a certificate for a completed course"""
    enrollment = get_object_or_404(Enrollment, id=enrollment_id, student=request.user)
    
    # Check if course is completed
    if not enrollment.is_completed:
        messages.error(request, "You need to complete the course before generating a certificate.")
        return redirect('courses:detail', course_id=enrollment.course.id)
    
    # Check if certificate already exists
    certificate, created = Certificate.objects.get_or_create(
        user=request.user,
        course=enrollment.course,
        enrollment=enrollment,
        defaults={
            'issue_date': timezone.now(),
        }
    )
    
    # Generate PDF if it doesn't exist
    if not certificate.certificate_file:
        pdf_path = generate_certificate_pdf(certificate)
        
        # Save the file path to the certificate
        relative_path = os.path.relpath(pdf_path, settings.MEDIA_ROOT)
        certificate.certificate_file = relative_path
        certificate.save()
    
    messages.success(request, "Certificate generated successfully!")
    return redirect('certificates:view', certificate_id=certificate.id)

@login_required
def view_certificate(request, certificate_id):
    """View a specific certificate"""
    certificate = get_object_or_404(Certificate, id=certificate_id)
    
    # Check if user is the owner or the course instructor
    if request.user != certificate.user and request.user != certificate.course.instructor and not request.user.is_staff:
        messages.error(request, "You don't have permission to view this certificate.")
        return redirect('home')
    
    return render(request, 'certificates/view_certificate.html', {
        'certificate': certificate
    })

def verify_certificate(request, certificate_id):
    """Public verification page for certificates"""
    try:
        certificate = Certificate.objects.get(id=certificate_id)
        is_valid = True
    except Certificate.DoesNotExist:
        certificate = None
        is_valid = False
    
    return render(request, 'certificates/verify_certificate.html', {
        'certificate': certificate,
        'is_valid': is_valid
    })

@login_required
def download_certificate(request, certificate_id):
    """Download a certificate PDF"""
    certificate = get_object_or_404(Certificate, id=certificate_id)
    
    # Check if user is the owner or the course instructor
    if request.user != certificate.user and request.user != certificate.course.instructor and not request.user.is_staff:
        messages.error(request, "You don't have permission to download this certificate.")
        return redirect('home')
    
    # Check if certificate file exists
    if not certificate.certificate_file:
        messages.error(request, "Certificate file not found. Please regenerate the certificate.")
        return redirect('certificates:view', certificate_id=certificate.id)
    
    # Return the file as a response
    file_path = os.path.join(settings.MEDIA_ROOT, str(certificate.certificate_file))
    response = FileResponse(open(file_path, 'rb'), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{certificate.course.title}_certificate.pdf"'
    return response

@login_required
def request_certificate(request, enrollment_id):
    """Request a certificate for a completed course"""
    enrollment = get_object_or_404(Enrollment, id=enrollment_id, student=request.user)
    
    # Check if course is completed
    if not enrollment.is_completed:
        messages.error(request, "You need to complete the course before requesting a certificate.")
        return redirect('accounts:student_certificates')
    
    # Mark as requested
    enrollment.certificate_requested = True
    enrollment.save()
    
    messages.success(request, "Certificate request submitted successfully. It will be processed soon.")
    return redirect('accounts:student_certificates')
