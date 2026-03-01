from django.contrib import admin
from .models import Assignment, TestCase, Submission, SubmissionResult

class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 1

class SubmissionResultInline(admin.TabularInline):
    model = SubmissionResult
    readonly_fields = ['test_case', 'status', 'execution_time', 'memory_used', 'output', 'error_message']
    extra = 0
    can_delete = False
    max_num = 0
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'difficulty', 'due_date', 'is_active']
    list_filter = ['course', 'difficulty', 'is_active']
    search_fields = ['title', 'description']
    inlines = [TestCaseInline]
    fieldsets = [
        (None, {'fields': ['course', 'title', 'description', 'problem_statement', 'constraints']}),
        ('Examples', {'fields': ['sample_input', 'sample_output']}),
        ('Configuration', {'fields': ['difficulty', 'max_score', 'programming_language', 'time_limit_seconds', 'memory_limit_mb']}),
        ('Code', {'fields': ['starter_code', 'solution_code']}),
        ('Settings', {'fields': ['due_date', 'is_active', 'allow_multiple_submissions']}),
    ]

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['student', 'assignment', 'status', 'score', 'submitted_at']
    list_filter = ['status', 'assignment']
    search_fields = ['student__username', 'assignment__title']
    readonly_fields = ['assignment', 'student', 'code', 'status', 'score', 'execution_time', 'memory_used', 
                      'compilation_output', 'error_message', 'submitted_at', 'graded_at']
    inlines = [SubmissionResultInline]
    
    def has_add_permission(self, request):
        return False

@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ['assignment', 'is_hidden', 'weight']
    list_filter = ['assignment', 'is_hidden']
    
@admin.register(SubmissionResult)
class SubmissionResultAdmin(admin.ModelAdmin):
    list_display = ['submission', 'test_case', 'status', 'execution_time']
    list_filter = ['status']
    readonly_fields = ['submission', 'test_case', 'status', 'execution_time', 'memory_used', 'output', 'error_message']
    
    def has_add_permission(self, request):
        return False
