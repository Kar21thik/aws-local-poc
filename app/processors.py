# app/processors.py
import time

def calculate_sum(numbers):
    if not numbers:
        return 0
    return sum(numbers)

def calculate_average(numbers):
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)
    
def build_result(task_id, total):
    return {
        "task_id": task_id,
        "total": total,
        "status": "completed",
        "timestamp": time.time() 
    }
