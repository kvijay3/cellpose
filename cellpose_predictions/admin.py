from django.contrib import admin
from .models import PredictionJob, CellMetrics


@admin.register(PredictionJob)
class PredictionJobAdmin(admin.ModelAdmin):
    list_display = ['id', 'status', 'model_type', 'num_cells_detected', 'processing_time', 'created_at']
    list_filter = ['status', 'model_type', 'created_at']
    search_fields = ['id', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at', 'processing_time', 'num_cells_detected']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'user', 'status', 'created_at', 'updated_at')
        }),
        ('Input Parameters', {
            'fields': ('input_image', 'model_type', 'diameter', 'flow_threshold', 'cellprob_threshold', 'min_size')
        }),
        ('Results', {
            'fields': ('result_masks', 'result_flows', 'result_segmented_images', 'result_tif_archive')
        }),
        ('Metrics', {
            'fields': ('num_cells_detected', 'processing_time', 'error_message')
        }),
    )


@admin.register(CellMetrics)
class CellMetricsAdmin(admin.ModelAdmin):
    list_display = ['prediction_job', 'cell_id', 'area', 'aspect_ratio', 'eccentricity']
    list_filter = ['prediction_job__status', 'prediction_job__created_at']
    search_fields = ['prediction_job__id', 'cell_id']
    readonly_fields = ['prediction_job', 'cell_id']

