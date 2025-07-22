from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, Http404
from django.core.files.storage import default_storage
import threading
import logging

from .models import PredictionJob, CellMetrics
from .serializers import (
    PredictionJobSerializer, 
    PredictionJobCreateSerializer,
    PredictionJobStatusSerializer,
    CellMetricsSerializer
)
from .services import CellposeService, MetricsService

logger = logging.getLogger(__name__)


class PredictionJobViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Cellpose prediction jobs"""
    
    queryset = PredictionJob.objects.all()
    parser_classes = [MultiPartParser, FormParser]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PredictionJobCreateSerializer
        elif self.action == 'status':
            return PredictionJobStatusSerializer
        return PredictionJobSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new prediction job"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create job
        job = serializer.save(user=request.user if request.user.is_authenticated else None)
        
        # Start prediction in background thread
        def run_prediction():
            try:
                service = CellposeService()
                service.predict(job.id)
            except Exception as e:
                logger.error(f"Background prediction failed for job {job.id}: {str(e)}")
        
        thread = threading.Thread(target=run_prediction)
        thread.daemon = True
        thread.start()
        
        # Return job details
        response_serializer = PredictionJobSerializer(job)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get job status"""
        job = self.get_object()
        serializer = PredictionJobStatusSerializer(job)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """Get detailed job results including metrics"""
        job = self.get_object()
        
        if job.status != 'completed':
            return Response(
                {'error': 'Job not completed yet'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = PredictionJobSerializer(job)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def download_masks(self, request, pk=None):
        """Download masks file"""
        job = self.get_object()
        
        if not job.result_masks:
            raise Http404("Masks file not found")
        
        try:
            file_path = job.result_masks.path
            with open(file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/octet-stream')
                response['Content-Disposition'] = f'attachment; filename="masks_{job.id}.npy"'
                return response
        except FileNotFoundError:
            raise Http404("Masks file not found")
    
    @action(detail=True, methods=['get'])
    def download_flows(self, request, pk=None):
        """Download flows file"""
        job = self.get_object()
        
        if not job.result_flows:
            raise Http404("Flows file not found")
        
        try:
            file_path = job.result_flows.path
            with open(file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/octet-stream')
                response['Content-Disposition'] = f'attachment; filename="flows_{job.id}.npy"'
                return response
        except FileNotFoundError:
            raise Http404("Flows file not found")
    
    @action(detail=True, methods=['get'])
    def download_segmented_image(self, request, pk=None):
        """Download segmented image"""
        job = self.get_object()
        
        if not job.result_segmented_images:
            raise Http404("Segmented image not found")
        
        try:
            file_path = job.result_segmented_images.path
            with open(file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='image/png')
                response['Content-Disposition'] = f'attachment; filename="segmented_{job.id}.png"'
                return response
        except FileNotFoundError:
            raise Http404("Segmented image not found")
    
    @action(detail=True, methods=['get'])
    def download_individual_cells(self, request, pk=None):
        """Download individual cell TIF files as ZIP"""
        job = self.get_object()
        
        if not job.result_tif_archive:
            raise Http404("Individual cells archive not found")
        
        try:
            file_path = job.result_tif_archive.path
            with open(file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/zip')
                response['Content-Disposition'] = f'attachment; filename="individual_cells_{job.id}.zip"'
                return response
        except FileNotFoundError:
            raise Http404("Individual cells archive not found")
    
    @action(detail=True, methods=['get'])
    def metrics(self, request, pk=None):
        """Get detailed metrics for all cells in the job"""
        job = self.get_object()
        
        if job.status != 'completed':
            return Response(
                {'error': 'Job not completed yet'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        metrics = CellMetrics.objects.filter(prediction_job=job)
        serializer = CellMetricsSerializer(metrics, many=True)
        
        # Calculate summary statistics
        if metrics.exists():
            areas = [m.area for m in metrics]
            aspect_ratios = [m.aspect_ratio for m in metrics]
            
            summary = {
                'total_cells': len(metrics),
                'average_area': sum(areas) / len(areas),
                'min_area': min(areas),
                'max_area': max(areas),
                'average_aspect_ratio': sum(aspect_ratios) / len(aspect_ratios),
                'min_aspect_ratio': min(aspect_ratios),
                'max_aspect_ratio': max(aspect_ratios),
            }
        else:
            summary = {'total_cells': 0}
        
        return Response({
            'summary': summary,
            'individual_metrics': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get overall statistics"""
        total_jobs = PredictionJob.objects.count()
        completed_jobs = PredictionJob.objects.filter(status='completed').count()
        failed_jobs = PredictionJob.objects.filter(status='failed').count()
        pending_jobs = PredictionJob.objects.filter(status='pending').count()
        processing_jobs = PredictionJob.objects.filter(status='processing').count()
        
        return Response({
            'total_jobs': total_jobs,
            'completed_jobs': completed_jobs,
            'failed_jobs': failed_jobs,
            'pending_jobs': pending_jobs,
            'processing_jobs': processing_jobs,
            'success_rate': (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
        })


class CellMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing cell metrics"""
    
    queryset = CellMetrics.objects.all()
    serializer_class = CellMetricsSerializer
    
    def get_queryset(self):
        queryset = CellMetrics.objects.all()
        job_id = self.request.query_params.get('job_id', None)
        if job_id is not None:
            queryset = queryset.filter(prediction_job__id=job_id)
        return queryset
    
    @action(detail=False, methods=['get'])
    def shape_analysis(self, request):
        """Get shape analysis for cells"""
        job_id = request.query_params.get('job_id')
        if not job_id:
            return Response(
                {'error': 'job_id parameter required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            job = PredictionJob.objects.get(id=job_id)
            if job.status != 'completed':
                return Response(
                    {'error': 'Job not completed yet'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Load masks and perform shape analysis
            import numpy as np
            masks = np.load(job.result_masks.path)
            analysis = MetricsService.get_cell_shape_analysis(masks)
            
            return Response({'shape_analysis': analysis})
            
        except PredictionJob.DoesNotExist:
            return Response(
                {'error': 'Job not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

