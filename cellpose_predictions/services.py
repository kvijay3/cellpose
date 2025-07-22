import os
import time
import numpy as np
import cv2
import tifffile
import zipfile
from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
from skimage import measure
from skimage.segmentation import find_boundaries
import requests
import json
import logging

# Import cellpose modules
from cellpose import models, io, utils
from cellpose.metrics import average_precision, aggregated_jaccard_index

from .models import PredictionJob, CellMetrics

logger = logging.getLogger(__name__)


class CellposeService:
    """Service class for handling Cellpose predictions"""
    
    def __init__(self):
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the Cellpose model"""
        try:
            # Use GPU if available
            gpu = settings.CELLPOSE_DEVICE == 'cuda'
            self.model = models.CellposeModel(
                gpu=gpu,
                pretrained_model=settings.CELLPOSE_MODEL_PATH
            )
            logger.info(f"Cellpose model loaded successfully on {settings.CELLPOSE_DEVICE}")
        except Exception as e:
            logger.error(f"Failed to load Cellpose model: {str(e)}")
            raise
    
    def predict(self, job_id):
        """Run Cellpose prediction on a job"""
        try:
            job = PredictionJob.objects.get(id=job_id)
            job.status = 'processing'
            job.save()
            
            start_time = time.time()
            
            # Load image
            image_path = job.input_image.path
            img = io.imread(image_path)
            
            # Run prediction
            masks, flows, styles = self.model.eval(
                img,
                diameter=job.diameter,
                flow_threshold=job.flow_threshold,
                cellprob_threshold=job.cellprob_threshold,
                min_size=job.min_size,
                channels=[0, 0]  # grayscale
            )
            
            processing_time = time.time() - start_time
            
            # Save results
            self._save_results(job, img, masks, flows, styles)
            
            # Calculate metrics
            self._calculate_metrics(job, img, masks)
            
            # Create individual segmented images and TIF files
            self._create_individual_segments(job, img, masks)
            
            # Send to Modal if configured
            if hasattr(settings, 'MODAL_ENDPOINT_URL') and settings.MODAL_ENDPOINT_URL:
                self._send_to_modal(job, masks, flows)
            
            # Update job status
            job.status = 'completed'
            job.num_cells_detected = len(np.unique(masks)) - 1  # Exclude background
            job.processing_time = processing_time
            job.save()
            
            logger.info(f"Prediction job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Prediction job {job_id} failed: {str(e)}")
            job = PredictionJob.objects.get(id=job_id)
            job.status = 'failed'
            job.error_message = str(e)
            job.save()
            raise
    
    def _save_results(self, job, img, masks, flows, styles):
        """Save prediction results to files"""
        
        # Save masks as numpy array
        masks_buffer = BytesIO()
        np.save(masks_buffer, masks)
        masks_buffer.seek(0)
        job.result_masks.save(
            f'masks_{job.id}.npy',
            ContentFile(masks_buffer.getvalue()),
            save=False
        )
        
        # Save flows
        flows_buffer = BytesIO()
        np.save(flows_buffer, flows)
        flows_buffer.seek(0)
        job.result_flows.save(
            f'flows_{job.id}.npy',
            ContentFile(flows_buffer.getvalue()),
            save=False
        )
        
        # Create segmented image overlay
        segmented_img = self._create_segmented_overlay(img, masks)
        segmented_buffer = BytesIO()
        cv2.imwrite(segmented_buffer, segmented_img)
        segmented_buffer.seek(0)
        job.result_segmented_images.save(
            f'segmented_{job.id}.png',
            ContentFile(segmented_buffer.getvalue()),
            save=False
        )
        
        job.save()
    
    def _create_segmented_overlay(self, img, masks):
        """Create a visual overlay of segmentation on original image"""
        if len(img.shape) == 2:
            # Convert grayscale to RGB
            img_rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        else:
            img_rgb = img.copy()
        
        # Create colored overlay
        overlay = np.zeros_like(img_rgb)
        
        # Generate random colors for each mask
        unique_masks = np.unique(masks)[1:]  # Exclude background
        colors = np.random.randint(0, 255, (len(unique_masks), 3))
        
        for i, mask_id in enumerate(unique_masks):
            mask_pixels = masks == mask_id
            overlay[mask_pixels] = colors[i]
        
        # Blend original image with overlay
        result = cv2.addWeighted(img_rgb, 0.7, overlay, 0.3, 0)
        
        # Add boundaries
        boundaries = find_boundaries(masks, mode='outer')
        result[boundaries] = [255, 255, 255]  # White boundaries
        
        return result
    
    def _calculate_metrics(self, job, img, masks):
        """Calculate metrics for each detected cell"""
        
        # Get region properties
        props = measure.regionprops(masks)
        
        # Clear existing metrics
        CellMetrics.objects.filter(prediction_job=job).delete()
        
        # Calculate metrics for each cell
        metrics_list = []
        for prop in props:
            metrics = CellMetrics(
                prediction_job=job,
                cell_id=prop.label,
                area=prop.area,
                perimeter=prop.perimeter,
                centroid_x=prop.centroid[1],
                centroid_y=prop.centroid[0],
                aspect_ratio=prop.major_axis_length / prop.minor_axis_length if prop.minor_axis_length > 0 else 0,
                eccentricity=prop.eccentricity,
                solidity=prop.solidity,
                extent=prop.extent,
                bbox_min_row=prop.bbox[0],
                bbox_min_col=prop.bbox[1],
                bbox_max_row=prop.bbox[2],
                bbox_max_col=prop.bbox[3],
                equivalent_diameter=prop.equivalent_diameter
            )
            metrics_list.append(metrics)
        
        # Bulk create metrics
        CellMetrics.objects.bulk_create(metrics_list)
    
    def _create_individual_segments(self, job, img, masks):
        """Create individual segmented images and TIF files"""
        
        # Create a zip file containing individual cell images
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            unique_masks = np.unique(masks)[1:]  # Exclude background
            
            for mask_id in unique_masks:
                # Create binary mask for this cell
                cell_mask = (masks == mask_id).astype(np.uint8)
                
                # Get bounding box
                props = measure.regionprops(cell_mask)[0]
                bbox = props.bbox
                
                # Extract cell region from original image
                if len(img.shape) == 2:
                    cell_img = img[bbox[0]:bbox[2], bbox[1]:bbox[3]]
                else:
                    cell_img = img[bbox[0]:bbox[2], bbox[1]:bbox[3], :]
                
                # Extract mask region
                cell_mask_cropped = cell_mask[bbox[0]:bbox[2], bbox[1]:bbox[3]]
                
                # Apply mask to image
                if len(img.shape) == 2:
                    masked_cell = cell_img * cell_mask_cropped
                else:
                    masked_cell = cell_img * cell_mask_cropped[:, :, np.newaxis]
                
                # Save as TIF
                tif_buffer = BytesIO()
                tifffile.imwrite(tif_buffer, masked_cell.astype(np.uint16))
                zip_file.writestr(f'cell_{mask_id:04d}.tif', tif_buffer.getvalue())
                
                # Also save as PNG for visualization
                if len(masked_cell.shape) == 2:
                    png_img = cv2.cvtColor(masked_cell.astype(np.uint8), cv2.COLOR_GRAY2RGB)
                else:
                    png_img = masked_cell.astype(np.uint8)
                
                png_buffer = BytesIO()
                cv2.imencode('.png', png_img)[1].tobytes()
                zip_file.writestr(f'cell_{mask_id:04d}.png', png_buffer.getvalue())
        
        zip_buffer.seek(0)
        job.result_tif_archive.save(
            f'individual_cells_{job.id}.zip',
            ContentFile(zip_buffer.getvalue()),
            save=False
        )
        job.save()
    
    def _send_to_modal(self, job, masks, flows):
        """Send results to Modal endpoint"""
        try:
            # Prepare data for Modal
            data = {
                'job_id': str(job.id),
                'num_cells': len(np.unique(masks)) - 1,
                'masks_shape': masks.shape,
                'processing_time': job.processing_time
            }
            
            # Send POST request to Modal
            response = requests.post(
                settings.MODAL_ENDPOINT_URL,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            
            logger.info(f"Successfully sent job {job.id} results to Modal")
            
        except Exception as e:
            logger.error(f"Failed to send job {job.id} to Modal: {str(e)}")
            # Don't fail the entire job if Modal fails


class MetricsService:
    """Service for calculating advanced segmentation metrics"""
    
    @staticmethod
    def calculate_segmentation_quality(masks_true, masks_pred):
        """Calculate segmentation quality metrics"""
        
        # Average Precision
        ap = average_precision(masks_true, masks_pred)
        
        # Aggregated Jaccard Index
        aji = aggregated_jaccard_index(masks_true, masks_pred)
        
        return {
            'average_precision_50': ap[0] if len(ap) > 0 else 0,
            'average_precision_75': ap[1] if len(ap) > 1 else 0,
            'average_precision_90': ap[2] if len(ap) > 2 else 0,
            'aggregated_jaccard_index': aji[0] if len(aji) > 0 else 0
        }
    
    @staticmethod
    def get_cell_shape_analysis(masks):
        """Get detailed shape analysis for all cells"""
        props = measure.regionprops(masks)
        
        analysis = []
        for prop in props:
            cell_analysis = {
                'cell_id': prop.label,
                'area': prop.area,
                'perimeter': prop.perimeter,
                'aspect_ratio': prop.major_axis_length / prop.minor_axis_length if prop.minor_axis_length > 0 else 0,
                'eccentricity': prop.eccentricity,
                'solidity': prop.solidity,
                'extent': prop.extent,
                'equivalent_diameter': prop.equivalent_diameter,
                'orientation': prop.orientation,
                'major_axis_length': prop.major_axis_length,
                'minor_axis_length': prop.minor_axis_length,
                'convex_area': prop.convex_area,
                'filled_area': prop.filled_area,
                'euler_number': prop.euler_number
            }
            analysis.append(cell_analysis)
        
        return analysis

