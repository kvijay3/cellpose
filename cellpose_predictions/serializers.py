from rest_framework import serializers
from .models import PredictionJob, CellMetrics


class CellMetricsSerializer(serializers.ModelSerializer):
    """Serializer for individual cell metrics"""
    
    class Meta:
        model = CellMetrics
        fields = [
            'cell_id', 'area', 'perimeter', 'centroid_x', 'centroid_y',
            'aspect_ratio', 'eccentricity', 'solidity', 'extent',
            'bbox_min_row', 'bbox_min_col', 'bbox_max_row', 'bbox_max_col',
            'equivalent_diameter'
        ]


class PredictionJobSerializer(serializers.ModelSerializer):
    """Serializer for prediction jobs"""
    
    cell_metrics = CellMetricsSerializer(many=True, read_only=True)
    
    class Meta:
        model = PredictionJob
        fields = [
            'id', 'input_image', 'model_type', 'diameter', 'flow_threshold',
            'cellprob_threshold', 'min_size', 'status', 'created_at', 'updated_at',
            'result_masks', 'result_flows', 'result_segmented_images', 'result_tif_archive',
            'num_cells_detected', 'processing_time', 'error_message', 'cell_metrics'
        ]
        read_only_fields = [
            'id', 'status', 'created_at', 'updated_at', 'result_masks', 
            'result_flows', 'result_segmented_images', 'result_tif_archive',
            'num_cells_detected', 'processing_time', 'error_message'
        ]


class PredictionJobCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating prediction jobs"""
    
    class Meta:
        model = PredictionJob
        fields = [
            'input_image', 'model_type', 'diameter', 'flow_threshold',
            'cellprob_threshold', 'min_size'
        ]
    
    def validate_input_image(self, value):
        """Validate uploaded image"""
        if value.size > 500 * 1024 * 1024:  # 500MB limit
            raise serializers.ValidationError("Image file too large. Maximum size is 500MB.")
        
        # Check file extension
        allowed_extensions = ['.png', '.jpg', '.jpeg', '.tif', '.tiff']
        if not any(value.name.lower().endswith(ext) for ext in allowed_extensions):
            raise serializers.ValidationError(
                f"Unsupported file format. Allowed formats: {', '.join(allowed_extensions)}"
            )
        
        return value


class PredictionJobStatusSerializer(serializers.ModelSerializer):
    """Lightweight serializer for job status checks"""
    
    class Meta:
        model = PredictionJob
        fields = ['id', 'status', 'created_at', 'updated_at', 'num_cells_detected', 'processing_time']
