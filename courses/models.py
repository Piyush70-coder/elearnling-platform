from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class Course(models.Model):
    """
    Course model for managing university courses
    """
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='courses_taught',
        limit_choices_to={'role': 'teacher'}
    )
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    code = models.CharField(max_length=20, unique=True)  # e.g., CS101, MATH201
    credits = models.IntegerField(default=3)
    duration_weeks = models.IntegerField(default=16)
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced')
        ],
        default='beginner'
    )
    programming_language = models.CharField(
        max_length=50,
        choices=[
            ('python', 'Python'),
            ('java', 'Java'),
            ('cpp', 'C++'),
            ('c', 'C'),
            ('javascript', 'JavaScript'),
            ('multiple', 'Multiple Languages')
        ],
        default='python'
    )
    is_active = models.BooleanField(default=True)
    enrollment_limit = models.IntegerField(default=50)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.code} - {self.title}"
    
    @property
    def enrolled_students_count(self):
        return self.enrollments.filter(is_active=True).count()
    
    @property
    def is_enrollment_open(self):
        return self.enrolled_students_count < self.enrollment_limit

class Enrollment(models.Model):
    """
    Student enrollment in courses
    """
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments',
        limit_choices_to={'role': 'student'}
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    completion_percentage = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    grade = models.CharField(
        max_length=5,
        choices=[
            ('A+', 'A+'), ('A', 'A'), ('A-', 'A-'),
            ('B+', 'B+'), ('B', 'B'), ('B-', 'B-'),
            ('C+', 'C+'), ('C', 'C'), ('C-', 'C-'),
            ('D', 'D'), ('F', 'F'), ('I', 'Incomplete')
        ],
        blank=True, null=True
    )
    
    class Meta:
        unique_together = ['student', 'course']
    
    def __str__(self):
        return f"{self.student.username} enrolled in {self.course.title}"

class Lecture(models.Model):
    """
    Lectures within a course
    """
    CONTENT_TYPE_CHOICES = [
        ('video', 'Video'),
        ('text', 'Text'),
        ('pdf', 'PDF'),
        ('interactive', 'Interactive Content')
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lectures')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    content_url = models.URLField(blank=True, null=True)  # For video links
    content_file = models.FileField(upload_to='lecture_content/', blank=True, null=True)
    content_text = models.TextField(blank=True, null=True)  # For text content
    order = models.PositiveIntegerField(default=0)
    duration_minutes = models.IntegerField(default=0)  # For videos
    is_free = models.BooleanField(default=False)  # Some lectures can be free preview
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.course.code} - {self.title}"

class LectureProgress(models.Model):
    """
    Track student progress through lectures
    """
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lecture_progress'
    )
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='progress')
    is_completed = models.BooleanField(default=False)
    watch_time_minutes = models.IntegerField(default=0)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        unique_together = ['student', 'lecture']
    
    def __str__(self):
        return f"{self.student.username} - {self.lecture.title} ({'Completed' if self.is_completed else 'In Progress'})"