"""
Modal integration for Cellpose predictions
This file shows how to set up a Modal endpoint to receive Cellpose results
"""

import modal
import json
from typing import Dict, Any

# Create Modal app
app = modal.App("cellpose-predictions")

# Define the Modal function
@app.function(
    image=modal.Image.debian_slim().pip_install([
        "fastapi",
        "numpy",
        "requests"
    ]),
    secrets=[modal.Secret.from_name("cellpose-api-secrets")]
)
@modal.web_endpoint(method="POST")
def receive_cellpose_results(data: Dict[str, Any]):
    """
    Modal endpoint to receive Cellpose prediction results
    
    Expected data format:
    {
        "job_id": "uuid-string",
        "num_cells": 42,
        "masks_shape": [1024, 1024],
        "processing_time": 15.3
    }
    """
    
    print(f"Received Cellpose results for job: {data.get('job_id')}")
    print(f"Number of cells detected: {data.get('num_cells')}")
    print(f"Processing time: {data.get('processing_time')} seconds")
    
    # Here you can add your custom logic:
    # - Store results in a database
    # - Send notifications
    # - Trigger downstream processing
    # - Generate reports
    
    # Example: Log to external service
    try:
        # Your custom processing logic here
        process_results(data)
        
        return {
            "status": "success",
            "message": f"Successfully processed results for job {data.get('job_id')}"
        }
    except Exception as e:
        print(f"Error processing results: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


def process_results(data: Dict[str, Any]):
    """
    Custom processing logic for Cellpose results
    """
    job_id = data.get('job_id')
    num_cells = data.get('num_cells')
    processing_time = data.get('processing_time')
    
    # Example processing:
    if num_cells > 100:
        print(f"High cell count detected in job {job_id}: {num_cells} cells")
        # Could trigger alerts or special processing
    
    if processing_time > 60:
        print(f"Long processing time for job {job_id}: {processing_time}s")
        # Could log performance metrics
    
    # Add your custom logic here:
    # - Database operations
    # - External API calls
    # - File processing
    # - Notifications


# Example of how to deploy this Modal app:
# 1. Install Modal: pip install modal
# 2. Set up Modal account: modal setup
# 3. Deploy: modal deploy modal_integration.py
# 4. The endpoint URL will be provided after deployment
# 5. Set this URL in your Django settings as MODAL_ENDPOINT_URL


if __name__ == "__main__":
    # For local testing
    test_data = {
        "job_id": "test-123",
        "num_cells": 25,
        "masks_shape": [512, 512],
        "processing_time": 8.5
    }
    
    result = receive_cellpose_results(test_data)
    print(result)

