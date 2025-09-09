import requests
import time
import os
from django.conf import settings
from .models import CodeExecution

class Judge0Service:
    """
    Service class to handle Judge0 API interactions
    """
    
    # Judge0 language IDs
    LANGUAGE_MAP = {
        'c': 50,           # C (GCC 9.2.0)
        'cpp': 54,         # C++ (GCC 9.2.0)
        'java': 62,        # Java (OpenJDK 13.0.1)
        'python': 71,      # Python (3.8.1)
        'javascript': 63,  # JavaScript (Node.js 12.14.0)
    }
    
    def __init__(self):
        self.api_url = "https://judge0-ce.p.rapidapi.com"
        self.headers = {
            "X-RapidAPI-Key": os.environ.get('JUDGE0_API_KEY'),
            "X-RapidAPI-Host": "judge0-ce.p.rapidapi.com",
            "Content-Type": "application/json"
        }
    
    def submit_code(self, execution_obj):
        """
        Submit code to Judge0 for execution
        """
        language_id = self.LANGUAGE_MAP.get(execution_obj.language)
        if not language_id:
            execution_obj.status = 'error'
            execution_obj.stderr = f"Unsupported language: {execution_obj.language}"
            execution_obj.save()
            return False
        
        payload = {
            "language_id": language_id,
            "source_code": execution_obj.source_code,
            "stdin": execution_obj.stdin_data,
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/submissions",
                json=payload,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 201:
                result = response.json()
                execution_obj.judge0_token = result['token']
                execution_obj.status = 'processing'
                execution_obj.save()
                return True
            else:
                execution_obj.status = 'error'
                execution_obj.stderr = f"API Error: {response.status_code} - {response.text}"
                execution_obj.save()
                return False
                
        except requests.exceptions.RequestException as e:
            execution_obj.status = 'error'
            execution_obj.stderr = f"Connection error: {str(e)}"
            execution_obj.save()
            return False
    
    def get_result(self, execution_obj):
        """
        Get execution result from Judge0
        """
        if not execution_obj.judge0_token:
            return False
        
        try:
            response = requests.get(
                f"{self.api_url}/submissions/{execution_obj.judge0_token}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Update execution object with results
                execution_obj.stdout = result.get('stdout', '') or ''
                execution_obj.stderr = result.get('stderr', '') or ''
                execution_obj.compile_output = result.get('compile_output', '') or ''
                execution_obj.execution_time = result.get('time')
                execution_obj.memory_used = result.get('memory')
                
                # Determine final status
                status_id = result.get('status', {}).get('id')
                if status_id == 3:  # Accepted
                    execution_obj.status = 'completed'
                elif status_id in [1, 2]:  # In Queue, Processing
                    execution_obj.status = 'processing'
                elif status_id == 5:  # Time Limit Exceeded
                    execution_obj.status = 'timeout'
                else:  # Various error states
                    execution_obj.status = 'error'
                
                execution_obj.save()
                return True
            else:
                return False
                
        except requests.exceptions.RequestException:
            return False
    
    def wait_for_result(self, execution_obj, max_wait=30):
        """
        Wait for code execution to complete
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            if self.get_result(execution_obj):
                execution_obj.refresh_from_db()
                if execution_obj.status != 'processing':
                    return True
            time.sleep(1)
        
        # Timeout
        execution_obj.status = 'timeout'
        execution_obj.stderr = "Execution timeout"
        execution_obj.save()
        return False