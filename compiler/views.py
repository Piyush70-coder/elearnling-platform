from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.contrib import messages
import json
from datetime import datetime

from .models import CodeExecution, CodeTemplate
from .services import Judge0Service

@login_required
def compiler_view(request):
    """
    Main compiler interface
    """
    # Get recent executions for history
    recent_executions = request.user.code_executions.all()[:10]
    
    context = {
        'recent_executions': recent_executions,
        'supported_languages': CodeExecution.LANGUAGE_CHOICES,
    }
    return render(request, 'compiler/compiler.html', context)

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def execute_code(request):
    """
    Execute code using Judge0 API
    """
    try:
        data = json.loads(request.body)
        language = data.get('language')
        source_code = data.get('source_code', '').strip()
        stdin_data = data.get('stdin', '')
        
        if not language or not source_code:
            return JsonResponse({
                'success': False,
                'error': 'Language and source code are required'
            })
        
        # Validate language
        valid_languages = [choice[0] for choice in CodeExecution.LANGUAGE_CHOICES]
        if language not in valid_languages:
            return JsonResponse({
                'success': False,
                'error': f'Unsupported language: {language}'
            })
        
        # Create execution record
        execution = CodeExecution.objects.create(
            user=request.user,
            language=language,
            source_code=source_code,
            stdin_data=stdin_data,
            status='pending'
        )
        
        # Submit to Judge0
        judge0_service = Judge0Service()
        if judge0_service.submit_code(execution):
            # Wait for result
            success = judge0_service.wait_for_result(execution)
            execution.refresh_from_db()
            
            if success:
                execution.completed_at = datetime.now()
                execution.save()
                
                return JsonResponse({
                    'success': True,
                    'execution_id': execution.id,
                    'status': execution.status,
                    'stdout': execution.stdout,
                    'stderr': execution.stderr,
                    'compile_output': execution.compile_output,
                    'execution_time': execution.execution_time,
                    'memory_used': execution.memory_used,
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Execution failed or timed out',
                    'execution_id': execution.id,
                })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Failed to submit code for execution',
                'execution_id': execution.id,
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        })

@login_required
def get_execution_result(request, execution_id):
    """
    Get result of a specific code execution
    """
    execution = get_object_or_404(CodeExecution, id=execution_id, user=request.user)
    
    return JsonResponse({
        'success': True,
        'execution_id': execution.id,
        'status': execution.status,
        'stdout': execution.stdout,
        'stderr': execution.stderr,
        'compile_output': execution.compile_output,
        'execution_time': execution.execution_time,
        'memory_used': execution.memory_used,
        'created_at': execution.created_at.isoformat(),
        'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
    })

@login_required
def execution_history(request):
    """
    Get user's code execution history
    """
    executions = request.user.code_executions.all()[:50]  # Last 50 executions
    
    history_data = []
    for execution in executions:
        history_data.append({
            'id': execution.id,
            'language': execution.get_language_display(),
            'status': execution.get_status_display(),
            'created_at': execution.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'source_code_preview': execution.source_code[:100] + '...' if len(execution.source_code) > 100 else execution.source_code,
        })
    
    return JsonResponse({
        'success': True,
        'history': history_data,
    })

@login_required
def get_code_template(request, language):
    """
    Get code template for a specific language
    """
    try:
        template = CodeTemplate.objects.get(language=language)
        return JsonResponse({
            'success': True,
            'template': template.template_code,
            'description': template.description,
        })
    except CodeTemplate.DoesNotExist:
        # Return basic templates if not found in database
        templates = {
            'c': '#include <stdio.h>\n\nint main() {\n    printf("Hello, World!\\n");\n    return 0;\n}',
            'cpp': '#include <iostream>\nusing namespace std;\n\nint main() {\n    cout << "Hello, World!" << endl;\n    return 0;\n}',
            'java': 'public class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello, World!");\n    }\n}',
            'python': '# Python code\nprint("Hello, World!")',
            'javascript': '// JavaScript code\nconsole.log("Hello, World!");',
        }
        
        template_code = templates.get(language, '')
        return JsonResponse({
            'success': True,
            'template': template_code,
            'description': f'Basic {language} template',
        })