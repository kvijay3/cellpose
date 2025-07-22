from django.db import models
from django.contrib.auth.models import User
import uuid


class PredictionJob(models.Model):
    """Model to track Cellpose prediction jobs"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # Input parameters
    input_image = models.ImageField(upload_to='input_images/')
    model_type = models.CharField(max_length=50, default='cpsam')
    diameter = models.FloatField(null=True, blank=True)
    flow_threshold = models.FloatField(default=0.4)
    cellprob_threshold = models.FloatField(default=0.0)
    min_size = models.IntegerField(default=15)
    
    # Job status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Results
    result_masks = models.FileField(upload_to='results/masks/', null=True, blank=True)
    result_flows = models.FileField(upload_to='results/flows/', null=True, blank=True)
    result_segmented_images = models.FileField(upload_to='results/segmented/', null=True, blank=True)
    result_tif_archive = models.FileField(upload_to='results/tif_archive/', null=True, blank=True)
    
    # Metrics
    num_cells_detected = models.IntegerField(null=True, blank=True)
    processing_time = models.FloatField(null=True, blank=True)  # in seconds
    error_message = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Prediction Job {self.id} - {self.status}"


class CellMetrics(models.Model):
    """Model to store individual cell metrics"""
    
    prediction_job = models.ForeignKey(PredictionJob, on_delete=models.CASCADE, related_name='cell_metrics')
    cell_id = models.IntegerField()  # Cell label from segmentation
    
    # Basic metrics
    area = models.FloatField()
    perimeter = models.FloatField()
    centroid_x = models.FloatField()
    centroid_y = models.FloatField()
    
    # Shape metrics
    aspect_ratio = models.FloatField()
    eccentricity = models.FloatField()
    solidity = models.FloatField()
    extent = models.FloatField()
    
    # Bounding box
    bbox_min_row = models.IntegerField()
    bbox_min_col = models.IntegerField()
    bbox_max_row = models.IntegerField()
    bbox_max_col = models.IntegerField()
    
    # Equivalent diameter
    equivalent_diameter = models.FloatField()
    
    class Meta:
        unique_together = ['prediction_job', 'cell_id']
        ordering = ['cell_id']
    
    def __str__(self):
        return f"Cell {self.cell_id} - Job {self.prediction_job.id}"

