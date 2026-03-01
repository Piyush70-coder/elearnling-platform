# Compiler app settings

# Judge0 API Configuration
JUDGE0_API_URL = "https://judge0-ce.p.rapidapi.com"

# Default timeout for code execution in seconds
EXECUTION_TIMEOUT = 30

# Maximum code size in characters
MAX_CODE_SIZE = 50000

# Maximum stdin size in characters
MAX_STDIN_SIZE = 5000

# Default limits for execution
DEFAULT_TIME_LIMIT = 2    # seconds
DEFAULT_MEMORY_LIMIT = 128  # MB

# Language ID mapping for Judge0 API
JUDGE0_LANGUAGE_MAP = {
    'c': 50,           # C (GCC 9.2.0)
    'cpp': 54,         # C++ (GCC 9.2.0)
    'java': 62,        # Java (OpenJDK 13.0.1)
    'python': 71,      # Python (3.8.1)
    'javascript': 63,  # JavaScript (Node.js 12.14.0)
    'ruby': 72,        # Ruby (2.7.0)
    'go': 60,          # Go (1.13.5)
    'csharp': 51,      # C# (Mono 6.6.0.161)
    'php': 68,         # PHP (7.4.1)
    'swift': 83,       # Swift (5.2.3)
}

# Judge0 status ID mapping
JUDGE0_STATUS_MAP = {
    1: 'pending',      # In Queue
    2: 'processing',   # Processing
    3: 'completed',    # Accepted
    4: 'error',        # Wrong Answer
    5: 'timeout',      # Time Limit Exceeded
    6: 'error',        # Compilation Error
    7: 'error',        # Runtime Error (SIGSEGV)
    8: 'error',        # Runtime Error (SIGXFSZ)
    9: 'error',        # Runtime Error (SIGFPE)
    10: 'error',       # Runtime Error (SIGABRT)
    11: 'error',       # Runtime Error (NZEC)
    12: 'error',       # Runtime Error (Other)
    13: 'error',       # Internal Error
    14: 'error',       # Exec Format Error
}