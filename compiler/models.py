from django.db import models
from django.conf import settings
from courses.models import Course

class CodeExecution(models.Model):
    """
    Model to store code execution history and results
    """
    LANGUAGE_CHOICES = [
        ('c', 'C'),
        ('cpp', 'C++'),
        ('java', 'Java'),
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('error', 'Error'),
        ('timeout', 'Timeout'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='code_executions'
    )
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='code_executions',
        null=True, blank=True
    )
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    source_code = models.TextField()
    stdin_data = models.TextField(blank=True, help_text="Input data for the program")
    stdout = models.TextField(blank=True, help_text="Program output")
    stderr = models.TextField(blank=True, help_text="Error output")
    compile_output = models.TextField(blank=True, help_text="Compilation output")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    execution_time = models.FloatField(null=True, blank=True, help_text="Execution time in seconds")
    memory_used = models.IntegerField(null=True, blank=True, help_text="Memory used in KB")
    judge0_token = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_language_display()} - {self.status}"

class CodeTemplate(models.Model):
    """
    Pre-defined code templates for different languages
    """
    LANGUAGE_CHOICES = [
        ('c', 'C'),
        ('cpp', 'C++'),
        ('java', 'Java'),
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
    ]
    
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, unique=True)
    template_code = models.TextField()
    description = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_language_display()} Template"