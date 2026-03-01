import requests
import time
import os
import json
from django.conf import settings as django_settings
from .models import CodeExecution
from . import settings as compiler_settings

class Judge0Service:
    """
    Service class to handle Judge0 API interactions
    """
    
    def __init__(self):
        self.api_url = compiler_settings.JUDGE0_API_URL
        self.headers = {
            "X-RapidAPI-Key": os.environ.get('JUDGE0_API_KEY') or (django_settings.JUDGE0_API_KEY if hasattr(django_settings, 'JUDGE0_API_KEY') else '3a1b8e44d8msh3d46792ee202c55p1ef130jsn0d7e150c725e'),
            "X-RapidAPI-Host": "judge0-ce.p.rapidapi.com",
            "Content-Type": "application/json"
        }
        self.timeout = compiler_settings.EXECUTION_TIMEOUT
        
    def run_test_case(self, execution_data):
        """
        Run a test case for auto-grading and return the result
        
        execution_data should be a dict with:
        - language: programming language
        - source_code: code to execute
        - stdin_data: input data
        - expected_output: expected output for comparison
        - time_limit: time limit in seconds
        - memory_limit: memory limit in MB
        """
        language_id = compiler_settings.JUDGE0_LANGUAGE_MAP.get(execution_data.get('language'))
        if not language_id:
            return {
                'status': 'error',
                'error': f"Unsupported language: {execution_data.get('language')}"
            }
        
        # Prepare payload for Judge0
        payload = {
            "language_id": language_id,
            "source_code": execution_data.get('source_code', ''),
            "stdin": execution_data.get('stdin_data', ''),
            "expected_output": execution_data.get('expected_output', ''),
            "cpu_time_limit": execution_data.get('time_limit', compiler_settings.DEFAULT_TIME_LIMIT),
            "memory_limit": execution_data.get('memory_limit', compiler_settings.DEFAULT_MEMORY_LIMIT) * 1000,  # Convert to KB
        }
        
        try:
            # Submit to Judge0
            response = requests.post(f"{self.api_url}/submissions", 
                                    headers=self.headers, 
                                    json=payload)
            
            if response.status_code != 201:
                return {
                    'status': 'error',
                    'error': f"Judge0 API error: {response.text}"
                }
                
            token = response.json().get('token')
            if not token:
                return {
                    'status': 'error',
                    'error': "No token received from Judge0 API"
                }
                
            # Wait for result
            result = self._wait_for_test_result(token)
            
            # Map Judge0 status to our status
            status_id = result.get('status', {}).get('id')
            status = compiler_settings.JUDGE0_STATUS_MAP.get(status_id, 'error')
            
            # Check if output matches expected output
            if status == 'accepted':
                actual_output = result.get('stdout', '').strip()
                expected_output = execution_data.get('expected_output', '').strip()
                
                if actual_output != expected_output:
                    status = 'wrong_answer'
            
            return {
                'status': status,
                'output': result.get('stdout', ''),
                'error': result.get('stderr', '') or result.get('compile_output', ''),
                'execution_time': float(result.get('time', 0)),
                'memory_used': float(result.get('memory', 0)) / 1000,  # Convert from KB to MB
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _wait_for_test_result(self, token):
        """
        Wait for test case execution result from Judge0
        """
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            try:
                response = requests.get(
                    f"{self.api_url}/submissions/{token}",
                    headers=self.headers,
                    params={"fields": "status,stdout,stderr,compile_output,time,memory"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    status_id = result.get('status', {}).get('id')
                    
                    # If processing is done
                    if status_id not in [1, 2]:  # Not in Queue or Processing
                        return result
                        
            except Exception as e:
                print(f"Error checking submission status: {str(e)}")
                
            # Wait before checking again
            time.sleep(1)
            
        # Timeout reached
        return {
            'status': {'id': 13},  # Internal Error
            'stderr': 'Execution timed out while waiting for results'
        }
    
    def submit_code(self, execution_obj):
        """
        Submit code to Judge0 for execution
        """
        # Validate code size
        if len(execution_obj.source_code) > compiler_settings.MAX_CODE_SIZE:
            execution_obj.status = 'error'
            execution_obj.stderr = f"Code exceeds maximum size limit of {compiler_settings.MAX_CODE_SIZE} characters"
            execution_obj.save()
            return False
            
        # Validate stdin size
        if len(execution_obj.stdin_data) > compiler_settings.MAX_STDIN_SIZE:
            execution_obj.status = 'error'
            execution_obj.stderr = f"Input exceeds maximum size limit of {compiler_settings.MAX_STDIN_SIZE} characters"
            execution_obj.save()
            return False
        
        language_id = compiler_settings.JUDGE0_LANGUAGE_MAP.get(execution_obj.language)
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
                timeout=10,
                params={"base64_encoded": "false", "fields": "*"}
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
                execution_obj.status = compiler_settings.JUDGE0_STATUS_MAP.get(status_id, 'error')
                
                # Add detailed error message if available
                if execution_obj.status == 'error':
                    status_description = result.get('status', {}).get('description', '')
                    if status_description and not execution_obj.stderr:
                        execution_obj.stderr = f"Execution error: {status_description}"
                
                execution_obj.save()
                return True
            else:
                return False
                
        except requests.exceptions.RequestException:
            return False
    
    def wait_for_result(self, execution_obj, max_wait=None):
        """
        Wait for code execution to complete
        """
        if max_wait is None:
            max_wait = self.timeout
            
        start_time = time.time()
        retry_count = 0
        
        while time.time() - start_time < max_wait:
            try:
                if self.get_result(execution_obj):
                    execution_obj.refresh_from_db()
                    if execution_obj.status != 'processing':
                        return True
                # Exponential backoff for polling
                sleep_time = min(1 * (2 ** retry_count), 5)  # Max 5 seconds between polls
                retry_count += 1
                time.sleep(sleep_time)
            except Exception as e:
                # Log the error but continue trying
                print(f"Error polling Judge0 API: {str(e)}")
                time.sleep(2)
        
        # Timeout
        execution_obj.status = 'timeout'
        execution_obj.stderr = "Execution timeout"
        execution_obj.save()
        return False