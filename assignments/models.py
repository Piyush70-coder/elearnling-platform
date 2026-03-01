from django.db import models
from django.conf import settings
from django.utils import timezone
from courses.models import Course

class Assignment(models.Model):
    """
    Programming assignments for courses
    """
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    description = models.TextField()
    problem_statement = models.TextField()
    constraints = models.TextField(blank=True, help_text="Input constraints and limits")
    sample_input = models.TextField(blank=True)
    sample_output = models.TextField(blank=True)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='easy')
    max_score = models.IntegerField(default=100)
    programming_language = models.CharField(
        max_length=50,
        choices=[
            ('python', 'Python'),
            ('java', 'Java'),
            ('cpp', 'C++'),
            ('c', 'C'),
            ('javascript', 'JavaScript')
        ],
        default='python'
    )
    time_limit_seconds = models.IntegerField(default=2)
    memory_limit_mb = models.IntegerField(default=128)
    starter_code = models.TextField(blank=True, help_text="Initial code template for students")
    solution_code = models.TextField(help_text="Teacher's solution (hidden from students)")
    assignment_file = models.FileField(upload_to='assignments/', blank=True, null=True, help_text="Upload assignment document or additional resources")
    due_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    allow_multiple_submissions = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.course.code} - {self.title}"

class TestCase(models.Model):
    """
    Test cases for automatic grading of assignments
    """
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='test_cases')
    input_data = models.TextField()
    expected_output = models.TextField()
    is_hidden = models.BooleanField(default=True)  # Hidden test cases for final grading
    weight = models.FloatField(default=1.0)  # Weight of this test case in final score
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.assignment.title} - Test Case {self.id}"

class Submission(models.Model):
    """
    Student submissions for assignments
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('accepted', 'Accepted'),
        ('wrong_answer', 'Wrong Answer'),
        ('time_limit_exceeded', 'Time Limit Exceeded'),
        ('memory_limit_exceeded', 'Memory Limit Exceeded'),
        ('runtime_error', 'Runtime Error'),
        ('compilation_error', 'Compilation Error')
    ]
    
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    code = models.TextField()
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='pending')
    score = models.FloatField(default=0.0)
    execution_time = models.FloatField(default=0.0)  # in seconds
    memory_used = models.FloatField(default=0.0)  # in MB
    compilation_output = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    graded_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.assignment.title} ({self.status})"

class SubmissionResult(models.Model):
    """
    Individual test case results for submissions
    """
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='results')
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE)
    status = models.CharField(max_length=25, choices=Submission.STATUS_CHOICES)
    execution_time = models.FloatField(default=0.0)
    memory_used = models.FloatField(default=0.0)
    output = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.submission.student.username} - Test Case {self.test_case.id} ({self.status})"

class AssignmentUpload(models.Model):
    """
    Tracks uploaded assignment files by teachers
    """
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='uploads')
    file = models.FileField(upload_to='assignment_uploads/')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assignment_uploads')
    upload_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.assignment.title}"