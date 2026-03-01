from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError

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
    # Price and category fields
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_free = models.BooleanField(default=False)
    category = models.CharField(
        max_length=50,
        choices=[
            ('programming', 'Programming'),
            ('data_science', 'Data Science'),
            ('web_development', 'Web Development'),
            ('mobile_development', 'Mobile Development'),
            ('devops', 'DevOps'),
            ('design', 'Design'),
            ('business', 'Business'),
            ('other', 'Other')
        ],
        default='programming'
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
    completed_lectures = models.ManyToManyField('Lecture', related_name='completed_by_enrollments', blank=True)
    is_course_completed = models.BooleanField(default=False)
    completion_date = models.DateTimeField(null=True, blank=True)
    certificate_requested = models.BooleanField(default=False)
    certificate_issued = models.BooleanField(default=False)
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
    last_accessed = models.DateTimeField(auto_now=True)
    last_lecture = models.ForeignKey('Lecture', on_delete=models.SET_NULL, related_name='last_accessed_by_enrollments', blank=True, null=True)
    
    class Meta:
        unique_together = ['student', 'course']
    
    def __str__(self):
        return f"{self.student.username} enrolled in {self.course.title}"
        
    def update_completion_percentage(self):
        """Update the completion percentage based on lecture progress"""
        course_lectures = self.course.lectures.count()
        if course_lectures == 0:
            return 0
            
        completed_lectures = LectureProgress.objects.filter(
            student=self.student,
            lecture__course=self.course,
            is_completed=True
        ).count()
        
        self.completion_percentage = float((completed_lectures / course_lectures) * 100)
        self.save(update_fields=['completion_percentage'])
        return self.completion_percentage

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
    video_file = models.FileField(upload_to='lecture_videos/', blank=True, null=True, 
                                 validators=[FileExtensionValidator(allowed_extensions=['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'])])  # For direct video uploads
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


class Quiz(models.Model):
    """
    Quiz model for course assessments
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    time_limit_minutes = models.PositiveIntegerField(default=30)
    passing_score = models.PositiveIntegerField(default=70)  # Percentage
    attempts_allowed = models.PositiveIntegerField(default=3)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Quizzes'
    
    def __str__(self):
        return f"{self.title} - {self.course.title}"


class Question(models.Model):
    """
    Question model for quizzes
    """
    QUESTION_TYPES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
        ('coding', 'Coding Question'),
    ]
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    points = models.PositiveIntegerField(default=1)
    code_snippet = models.TextField(blank=True, null=True)  # For coding questions
    explanation = models.TextField(blank=True, null=True)  # Explanation shown after answering
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.question_text[:30]}..."


class Answer(models.Model):
    """
    Answer model for multiple choice and true/false questions
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.answer_text} - {'Correct' if self.is_correct else 'Incorrect'}"


class QuizAttempt(models.Model):
    """
    Tracks student attempts at quizzes
    """
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    completed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['student', 'quiz', 'started_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.quiz.title} - {self.score if self.completed else 'In Progress'}"
    
    def calculate_score(self):
        """Calculate the score based on student answers"""
        if not self.completed:
            return None
            
        total_points = sum(q.points for q in self.quiz.questions.all())
        if total_points == 0:
            return 0
            
        earned_points = sum(sa.points_earned for sa in self.student_answers.all())
        percentage = (earned_points / total_points) * 100
        return round(percentage, 2)
    
    def save(self, *args, **kwargs):
        if self.completed and not self.completed_at:
            self.completed_at = timezone.now()
            self.score = self.calculate_score()
        super().save(*args, **kwargs)


class StudentAnswer(models.Model):
    """
    Stores student answers to quiz questions
    """
    quiz_attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='student_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answers = models.ManyToManyField(Answer, blank=True)
    text_answer = models.TextField(blank=True, null=True)  # For short answer and coding questions
    points_earned = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ['quiz_attempt', 'question']
    
    def __str__(self):
        return f"{self.quiz_attempt.student.username} - {self.question.question_text[:20]}..."


class Review(models.Model):
    """
    Course review and rating model
    """
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Below Average'),
        (3, '3 - Average'),
        (4, '4 - Good'),
        (5, '5 - Excellent'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=True)  # For moderation
    
    class Meta:
        unique_together = ['course', 'student']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title} - {self.rating} stars"


class Comment(models.Model):
    """
    Comments on lectures
    """
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='comments')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=True)  # For moderation
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.lecture.title[:20]}..."