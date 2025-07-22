#!/usr/bin/env python3
"""
Example client for Cellpose Django REST API
Demonstrates how to use the API to submit images and retrieve results
"""

import requests
import time
import json
import os
from pathlib import Path


class CellposeAPIClient:
    """Client for interacting with Cellpose Django REST API"""
    
    def __init__(self, base_url="http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def submit_image(self, image_path, **kwargs):
        """
        Submit an image for Cellpose prediction
        
        Args:
            image_path: Path to image file
            **kwargs: Additional parameters (diameter, flow_threshold, etc.)
        
        Returns:
            dict: Job information including job ID
        """
        url = f"{self.base_url}/predictions/"
        
        with open(image_path, 'rb') as f:
            files = {'input_image': f}
            data = kwargs
            
            response = self.session.post(url, files=files, data=data)
            response.raise_for_status()
            
            return response.json()
    
    def get_job_status(self, job_id):
        """Get current status of a prediction job"""
        url = f"{self.base_url}/predictions/{job_id}/status/"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_results(self, job_id):
        """Get complete results for a completed job"""
        url = f"{self.base_url}/predictions/{job_id}/results/"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_metrics(self, job_id):
        """Get detailed metrics for all detected cells"""
        url = f"{self.base_url}/predictions/{job_id}/metrics/"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def download_file(self, job_id, file_type, output_path):
        """
        Download a result file
        
        Args:
            job_id: Job ID
            file_type: 'segmented_image', 'individual_cells', 'masks', or 'flows'
            output_path: Where to save the file
        """
        url = f"{self.base_url}/predictions/{job_id}/download_{file_type}/"
        
        response = self.session.get(url)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"Downloaded {file_type} to {output_path}")
    
    def wait_for_completion(self, job_id, timeout=300, poll_interval=5):
        """
        Wait for a job to complete
        
        Args:
            job_id: Job ID to wait for
            timeout: Maximum time to wait in seconds
            poll_interval: How often to check status in seconds
        
        Returns:
            dict: Final job status
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_job_status(job_id)
            
            if status['status'] in ['completed', 'failed']:
                return status
            
            print(f"Job {job_id} status: {status['status']}")
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")


def main():
    """Example usage of the Cellpose API client"""
    
    # Initialize client
    client = CellposeAPIClient()
    
    # Example image path (replace with your image)
    image_path = "example_image.png"
    
    if not os.path.exists(image_path):
        print(f"Please provide an image file at {image_path}")
        print("You can download example images from:")
        print("https://cellpose.readthedocs.io/en/latest/gui.html#example-images")
        return
    
    try:
        # Submit image for prediction
        print(f"Submitting image: {image_path}")
        job = client.submit_image(
            image_path,
            flow_threshold=0.4,
            cellprob_threshold=0.0,
            min_size=15
        )
        
        job_id = job['id']
        print(f"Job submitted with ID: {job_id}")
        
        # Wait for completion
        print("Waiting for prediction to complete...")
        final_status = client.wait_for_completion(job_id)
        
        if final_status['status'] == 'completed':
            print(f"✅ Prediction completed!")
            print(f"   Cells detected: {final_status['num_cells_detected']}")
            print(f"   Processing time: {final_status['processing_time']:.2f}s")
            
            # Get detailed results
            results = client.get_results(job_id)
            print(f"\n📊 Results:")
            print(f"   Masks file: {results['result_masks']}")
            print(f"   Segmented image: {results['result_segmented_images']}")
            print(f"   Individual cells: {results['result_tif_archive']}")
            
            # Get metrics
            metrics = client.get_metrics(job_id)
            print(f"\n📈 Metrics Summary:")
            summary = metrics['summary']
            print(f"   Total cells: {summary['total_cells']}")
            print(f"   Average area: {summary['average_area']:.1f} pixels")
            print(f"   Average aspect ratio: {summary['average_aspect_ratio']:.2f}")
            
            # Download files
            output_dir = Path("results")
            output_dir.mkdir(exist_ok=True)
            
            print(f"\n⬇️  Downloading results to {output_dir}/")
            
            # Download segmented image
            client.download_file(
                job_id, 
                'segmented_image', 
                output_dir / f"segmented_{job_id}.png"
            )
            
            # Download individual cells ZIP
            client.download_file(
                job_id, 
                'individual_cells', 
                output_dir / f"individual_cells_{job_id}.zip"
            )
            
            # Show first few cell metrics
            print(f"\n🔬 Individual Cell Metrics (first 5):")
            for i, cell in enumerate(metrics['individual_metrics'][:5]):
                print(f"   Cell {cell['cell_id']}: "
                      f"area={cell['area']:.1f}, "
                      f"aspect_ratio={cell['aspect_ratio']:.2f}, "
                      f"eccentricity={cell['eccentricity']:.2f}")
            
            if len(metrics['individual_metrics']) > 5:
                print(f"   ... and {len(metrics['individual_metrics']) - 5} more cells")
            
            print(f"\n✨ All done! Check the {output_dir}/ directory for results.")
            
        else:
            print(f"❌ Prediction failed: {final_status.get('error_message', 'Unknown error')}")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def batch_example():
    """Example of processing multiple images"""
    
    client = CellposeAPIClient()
    
    # List of images to process
    image_paths = [
        "image1.png",
        "image2.png", 
        "image3.png"
    ]
    
    # Submit all jobs
    job_ids = []
    for image_path in image_paths:
        if os.path.exists(image_path):
            job = client.submit_image(image_path)
            job_ids.append(job['id'])
            print(f"Submitted {image_path} -> Job {job['id']}")
    
    # Wait for all to complete
    completed_jobs = []
    for job_id in job_ids:
        try:
            status = client.wait_for_completion(job_id)
            if status['status'] == 'completed':
                completed_jobs.append(job_id)
                print(f"✅ Job {job_id} completed")
            else:
                print(f"❌ Job {job_id} failed")
        except TimeoutError:
            print(f"⏰ Job {job_id} timed out")
    
    # Get summary statistics
    total_cells = 0
    for job_id in completed_jobs:
        metrics = client.get_metrics(job_id)
        cells = metrics['summary']['total_cells']
        total_cells += cells
        print(f"Job {job_id}: {cells} cells detected")
    
    print(f"\n📊 Batch Summary: {total_cells} total cells across {len(completed_jobs)} images")


if __name__ == "__main__":
    print("🔬 Cellpose API Client Example")
    print("=" * 40)
    
    # Run single image example
    main()
    
    # Uncomment to run batch example
    # print("\n" + "=" * 40)
    # print("🔬 Batch Processing Example")
    # print("=" * 40)
    # batch_example()

