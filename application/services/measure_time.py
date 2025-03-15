import time
from functools import wraps
from flask import request

def measure_response_time(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        response = f(*args, **kwargs)
        end_time = time.time()

        # Calculate the response time
        response_time = end_time - start_time

        # Log the response time
        print(f"Response time for {request.method} {request.path}: {response_time:.4f} seconds")

        return response
    return wrapper
