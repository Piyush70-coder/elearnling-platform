from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Extended User model with role-based access control
    Roles: Student, Teacher, Admin
    """
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=15, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    university_id = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} ({self.role})"
    
    @property
    def is_student(self):
        return self.role == 'student'
    
    @property
    def is_teacher(self):
        return self.role == 'teacher'
    
    @property
    def is_admin(self):
        return self.role == 'admin'

class UserProfile(models.Model):
    """
    Additional profile information for users
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    emergency_contact = models.CharField(max_length=15, blank=True, null=True)
    enrollment_date = models.DateField(blank=True, null=True)
    graduation_year = models.IntegerField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

class AdminNotification(models.Model):
    """
    Notifications for admin users
    """
    NOTIFICATION_TYPES = [
        ('course_completion', 'Course Completion'),
        ('certificate_request', 'Certificate Request'),
        ('new_enrollment', 'New Enrollment'),
        ('system', 'System Notification'),
    ]
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    related_course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    related_enrollment = models.ForeignKey('courses.Enrollment', on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type}: {self.title}"
    
    @classmethod
    def create_course_completion_notification(cls, enrollment):
        """Create notification when student completes a course"""
        notification = cls(
            title=f"Course Completion: {enrollment.course.title}",
            message=f"Student {enrollment.student.username} has completed the course '{enrollment.course.title}'. Certificate needs to be issued.",
            notification_type='course_completion',
            related_user=enrollment.student,
            related_course=enrollment.course,
            related_enrollment=enrollment
        )
        notification.save()
        return notification