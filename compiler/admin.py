from django.contrib import admin
from .models import CodeExecution, CodeTemplate

@admin.register(CodeExecution)
class CodeExecutionAdmin(admin.ModelAdmin):
    list_display = ('user', 'language', 'status', 'created_at', 'completed_at')
    list_filter = ('language', 'status', 'created_at')
    search_fields = ('user__username', 'source_code')
    readonly_fields = ('judge0_token', 'stdout', 'stderr', 'compile_output', 'execution_time', 'memory_used')
    
@admin.register(CodeTemplate)
class CodeTemplateAdmin(admin.ModelAdmin):
    list_display = ('language', 'description', 'created_at')
    list_filter = ('language',)
    search_fields = ('description', 'template_code')
