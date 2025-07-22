# Cellpose Django REST API Tutorial

This tutorial covers the complete setup and usage of the Cellpose Django REST API, including output formats, TIF conversion, and Cellpose-SAM integration with metrics.

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd cellpose

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Cellpose
pip install cellpose[gui]
```

### 2. Django Setup

```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

## 📡 API Endpoints

### Base URL: `http://localhost:8000/api/v1/`

### 1. Create Prediction Job
```http
POST /predictions/
Content-Type: multipart/form-data

Parameters:
- input_image: Image file (PNG, JPG, TIF)
- model_type: "cpsam" (default)
- diameter: float (optional, auto-detected if None)
- flow_threshold: float (default: 0.4)
- cellprob_threshold: float (default: 0.0)
- min_size: int (default: 15)
```

**Example using curl:**
```bash
curl -X POST http://localhost:8000/api/v1/predictions/ \
  -F "input_image=@/path/to/your/image.png" \
  -F "flow_threshold=0.4" \
  -F "min_size=15"
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "input_image": "/media/input_images/image.png",
  "model_type": "cpsam",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### 2. Check Job Status
```http
GET /predictions/{job_id}/status/
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "num_cells_detected": 42,
  "processing_time": 15.3
}
```

### 3. Get Complete Results
```http
GET /predictions/{job_id}/results/
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "num_cells_detected": 42,
  "processing_time": 15.3,
  "result_masks": "/media/results/masks/masks_550e8400.npy",
  "result_flows": "/media/results/flows/flows_550e8400.npy",
  "result_segmented_images": "/media/results/segmented/segmented_550e8400.png",
  "result_tif_archive": "/media/results/tif_archive/individual_cells_550e8400.zip",
  "cell_metrics": [
    {
      "cell_id": 1,
      "area": 1250.5,
      "perimeter": 142.8,
      "aspect_ratio": 1.8,
      "eccentricity": 0.7,
      "solidity": 0.95
    }
  ]
}
```

### 4. Download Files

#### Download Segmented Image Overlay
```http
GET /predictions/{job_id}/download_segmented_image/
```

#### Download Individual Cell TIF Files (ZIP)
```http
GET /predictions/{job_id}/download_individual_cells/
```

#### Download Raw Masks (NumPy)
```http
GET /predictions/{job_id}/download_masks/
```

#### Download Flow Fields (NumPy)
```http
GET /predictions/{job_id}/download_flows/
```

### 5. Get Detailed Metrics
```http
GET /predictions/{job_id}/metrics/
```

**Response:**
```json
{
  "summary": {
    "total_cells": 42,
    "average_area": 1250.5,
    "min_area": 450.2,
    "max_area": 2100.8,
    "average_aspect_ratio": 1.6
  },
  "individual_metrics": [
    {
      "cell_id": 1,
      "area": 1250.5,
      "perimeter": 142.8,
      "centroid_x": 256.3,
      "centroid_y": 128.7,
      "aspect_ratio": 1.8,
      "eccentricity": 0.7,
      "solidity": 0.95,
      "extent": 0.82,
      "equivalent_diameter": 39.9,
      "bbox_min_row": 100,
      "bbox_min_col": 200,
      "bbox_max_row": 150,
      "bbox_max_col": 280
    }
  ]
}
```

## 📊 Output File Formats

### 1. Individual Segmented Images

The API creates individual TIF files for each detected cell:

- **Format**: 16-bit TIFF
- **Content**: Cropped cell region with background masked to 0
- **Naming**: `cell_0001.tif`, `cell_0002.tif`, etc.
- **Delivery**: ZIP archive containing all individual cells

### 2. Segmented Image Overlay

- **Format**: PNG
- **Content**: Original image with colored cell overlays and white boundaries
- **Use**: Visualization and quality assessment

### 3. Raw Masks

- **Format**: NumPy array (.npy)
- **Content**: Integer array where each cell has a unique label (1, 2, 3, ...)
- **Background**: Label 0
- **Use**: Further analysis and processing

### 4. Flow Fields

- **Format**: NumPy array (.npy)
- **Content**: Cellpose flow field outputs
- **Use**: Advanced analysis and debugging

## 🔬 Cellpose-SAM Integration & Metrics

### Available Metrics

The API calculates comprehensive metrics for each detected cell:

#### Basic Measurements
- **Area**: Number of pixels in the cell
- **Perimeter**: Length of cell boundary
- **Centroid**: Center coordinates (x, y)
- **Bounding Box**: Min/max row and column coordinates

#### Shape Analysis
- **Aspect Ratio**: Major axis / Minor axis length
- **Eccentricity**: Measure of how elongated the cell is (0 = circle, 1 = line)
- **Solidity**: Area / Convex area (measure of concavity)
- **Extent**: Area / Bounding box area
- **Equivalent Diameter**: Diameter of circle with same area

### Advanced Shape Analysis Endpoint

```http
GET /metrics/shape_analysis/?job_id={job_id}
```

**Response includes additional metrics:**
```json
{
  "shape_analysis": [
    {
      "cell_id": 1,
      "area": 1250.5,
      "perimeter": 142.8,
      "aspect_ratio": 1.8,
      "eccentricity": 0.7,
      "solidity": 0.95,
      "extent": 0.82,
      "equivalent_diameter": 39.9,
      "orientation": 0.785,
      "major_axis_length": 45.2,
      "minor_axis_length": 25.1,
      "convex_area": 1315.8,
      "filled_area": 1250.5,
      "euler_number": 1
    }
  ]
}
```

### Metric Definitions

- **Orientation**: Angle of major axis with respect to x-axis
- **Major/Minor Axis Length**: Length of major and minor axes of fitted ellipse
- **Convex Area**: Area of convex hull around the cell
- **Filled Area**: Area with holes filled
- **Euler Number**: Topological measure (1 = single object, 0 = object with hole)

## 🔧 TIF File Conversion

### Automatic TIF Generation

The API automatically generates TIF files for each segmented cell:

```python
# In services.py - _create_individual_segments method
def _create_individual_segments(self, job, img, masks):
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        unique_masks = np.unique(masks)[1:]  # Exclude background
        
        for mask_id in unique_masks:
            # Extract cell region
            cell_mask = (masks == mask_id).astype(np.uint8)
            props = measure.regionprops(cell_mask)[0]
            bbox = props.bbox
            
            # Crop to bounding box
            cell_img = img[bbox[0]:bbox[2], bbox[1]:bbox[3]]
            cell_mask_cropped = cell_mask[bbox[0]:bbox[2], bbox[1]:bbox[3]]
            
            # Apply mask
            masked_cell = cell_img * cell_mask_cropped
            
            # Save as 16-bit TIF
            tif_buffer = BytesIO()
            tifffile.imwrite(tif_buffer, masked_cell.astype(np.uint16))
            zip_file.writestr(f'cell_{mask_id:04d}.tif', tif_buffer.getvalue())
```

### Custom TIF Processing

You can also process TIF files manually:

```python
import tifffile
import numpy as np
from skimage import measure

def extract_cells_to_tif(masks, original_image, output_dir):
    """Extract individual cells and save as TIF files"""
    
    unique_masks = np.unique(masks)[1:]  # Exclude background
    
    for mask_id in unique_masks:
        # Create binary mask for this cell
        cell_mask = (masks == mask_id).astype(np.uint8)
        
        # Get properties
        props = measure.regionprops(cell_mask)[0]
        bbox = props.bbox
        
        # Extract and mask cell region
        cell_region = original_image[bbox[0]:bbox[2], bbox[1]:bbox[3]]
        mask_region = cell_mask[bbox[0]:bbox[2], bbox[1]:bbox[3]]
        
        # Apply mask
        masked_cell = cell_region * mask_region
        
        # Save as TIF
        output_path = f"{output_dir}/cell_{mask_id:04d}.tif"
        tifffile.imwrite(output_path, masked_cell.astype(np.uint16))
        
        print(f"Saved cell {mask_id} to {output_path}")
```

## 🌐 Modal Integration

### Setting up Modal Endpoint

1. **Install Modal**:
```bash
pip install modal
```

2. **Deploy the Modal function**:
```bash
modal deploy modal_integration.py
```

3. **Configure Django settings**:
```python
# In settings.py
MODAL_ENDPOINT_URL = "https://your-modal-endpoint.modal.run"
```

### Modal Function Example

The provided `modal_integration.py` shows how to:
- Receive prediction results
- Process cell count and timing data
- Trigger downstream workflows
- Send notifications

## 📈 Performance Optimization

### GPU Usage

Enable GPU acceleration:

```python
# In settings.py
CELLPOSE_DEVICE = 'cuda'  # or 'cpu'
```

### Batch Processing

For multiple images, create multiple jobs:

```python
import requests

def batch_predict(image_paths, api_url):
    job_ids = []
    
    for image_path in image_paths:
        with open(image_path, 'rb') as f:
            files = {'input_image': f}
            response = requests.post(f"{api_url}/predictions/", files=files)
            job_ids.append(response.json()['id'])
    
    return job_ids
```

### Monitoring Jobs

```python
def wait_for_completion(job_ids, api_url, timeout=300):
    import time
    
    completed = []
    start_time = time.time()
    
    while len(completed) < len(job_ids) and time.time() - start_time < timeout:
        for job_id in job_ids:
            if job_id not in completed:
                response = requests.get(f"{api_url}/predictions/{job_id}/status/")
                if response.json()['status'] == 'completed':
                    completed.append(job_id)
        
        time.sleep(2)  # Check every 2 seconds
    
    return completed
```

## 🐛 Troubleshooting

### Common Issues

1. **Out of Memory**: Reduce batch size or use CPU
2. **Slow Processing**: Enable GPU or reduce image size
3. **File Not Found**: Check media file permissions
4. **Model Loading Error**: Verify Cellpose installation

### Debug Mode

Enable detailed logging:

```python
# In settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
        },
    },
    'loggers': {
        'cellpose_predictions': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## 📚 Additional Resources

- [Cellpose Documentation](https://cellpose.readthedocs.io/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Modal Documentation](https://modal.com/docs)
- [scikit-image Regionprops](https://scikit-image.org/docs/stable/api/skimage.measure.html#skimage.measure.regionprops)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project is licensed under the same terms as Cellpose.

