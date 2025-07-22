# Cellpose Django REST API

A comprehensive Django REST Framework API for Cellpose cellular segmentation with Modal integration, individual cell extraction, and detailed metrics analysis.

## 🌟 Features

- **RESTful API** for Cellpose predictions
- **Individual cell extraction** as TIF files
- **Comprehensive metrics** including aspect ratio, eccentricity, solidity
- **Modal integration** for cloud processing
- **Real-time job tracking** with status updates
- **Batch processing** support
- **File downloads** for all result types
- **Admin interface** for job management

## 🚀 Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Start server
python manage.py runserver
```

### 2. Submit a Prediction

```python
import requests

# Submit image
with open('your_image.png', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/predictions/',
        files={'input_image': f},
        data={'flow_threshold': 0.4, 'min_size': 15}
    )

job = response.json()
job_id = job['id']
```

### 3. Get Results

```python
# Check status
status = requests.get(f'http://localhost:8000/api/v1/predictions/{job_id}/status/')

# Get complete results with metrics
results = requests.get(f'http://localhost:8000/api/v1/predictions/{job_id}/results/')

# Download individual cell TIF files
tif_response = requests.get(f'http://localhost:8000/api/v1/predictions/{job_id}/download_individual_cells/')
with open('cells.zip', 'wb') as f:
    f.write(tif_response.content)
```

## 📊 Output Formats

### 1. Individual Cell TIF Files ✅

Each detected cell is extracted and saved as a separate 16-bit TIF file:

- **Format**: 16-bit TIFF
- **Content**: Cropped cell region with background masked to 0
- **Naming**: `cell_0001.tif`, `cell_0002.tif`, etc.
- **Delivery**: ZIP archive containing all cells
- **Use case**: Individual cell analysis, machine learning training data

### 2. Segmented Image Overlay

- **Format**: PNG with colored overlays
- **Content**: Original image + colored cell masks + white boundaries
- **Use case**: Visualization and quality assessment

### 3. Raw Segmentation Masks

- **Format**: NumPy array (.npy)
- **Content**: Integer labels for each cell (0=background, 1,2,3...=cells)
- **Use case**: Further computational analysis

### 4. Flow Fields

- **Format**: NumPy array (.npy)
- **Content**: Cellpose flow field outputs
- **Use case**: Advanced analysis and debugging

## 🔬 Comprehensive Metrics

### Basic Measurements
- **Area**: Cell area in pixels
- **Perimeter**: Boundary length
- **Centroid**: Center coordinates
- **Bounding Box**: Min/max coordinates

### Shape Analysis ✅
- **Aspect Ratio**: Major/minor axis ratio (elongation measure)
- **Eccentricity**: 0=circle, 1=line (shape measure)
- **Solidity**: Area/convex area (concavity measure)
- **Extent**: Area/bounding box area (fill measure)
- **Equivalent Diameter**: Diameter of equal-area circle

### Advanced Metrics
- **Orientation**: Major axis angle
- **Major/Minor Axis Lengths**: Fitted ellipse dimensions
- **Convex Area**: Convex hull area
- **Euler Number**: Topological measure (holes detection)

## 🌐 Modal Integration

### Setup Modal Endpoint

1. **Deploy Modal function**:
```bash
modal deploy modal_integration.py
```

2. **Configure Django**:
```python
# settings.py
MODAL_ENDPOINT_URL = "https://your-modal-endpoint.modal.run"
```

3. **Automatic forwarding**: Results are automatically sent to Modal after processing

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/predictions/` | POST | Submit new prediction job |
| `/api/v1/predictions/{id}/status/` | GET | Get job status |
| `/api/v1/predictions/{id}/results/` | GET | Get complete results |
| `/api/v1/predictions/{id}/metrics/` | GET | Get detailed cell metrics |
| `/api/v1/predictions/{id}/download_individual_cells/` | GET | Download TIF files (ZIP) |
| `/api/v1/predictions/{id}/download_segmented_image/` | GET | Download overlay image |
| `/api/v1/predictions/{id}/download_masks/` | GET | Download raw masks |
| `/api/v1/predictions/{id}/download_flows/` | GET | Download flow fields |
| `/api/v1/metrics/shape_analysis/` | GET | Advanced shape analysis |

## 🔧 Configuration

### Environment Variables

```bash
# Django settings
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Cellpose settings
CELLPOSE_MODEL_PATH=cpsam
CELLPOSE_DEVICE=cuda  # or cpu

# Modal integration
MODAL_ENDPOINT_URL=https://your-modal-endpoint.modal.run
```

### GPU Support

Enable GPU acceleration:

```python
# settings.py
CELLPOSE_DEVICE = 'cuda'
```

## 📈 Example Usage

See `example_client.py` for a complete example:

```python
from example_client import CellposeAPIClient

client = CellposeAPIClient()

# Submit image
job = client.submit_image("cell_image.png", flow_threshold=0.4)

# Wait for completion
status = client.wait_for_completion(job['id'])

# Download results
client.download_file(job['id'], 'individual_cells', 'cells.zip')

# Get metrics
metrics = client.get_metrics(job['id'])
print(f"Detected {metrics['summary']['total_cells']} cells")
```

## 🧪 Cellpose-SAM Tutorial

### What is Cellpose-SAM?

Cellpose-SAM combines Cellpose's segmentation capabilities with SAM (Segment Anything Model) for enhanced accuracy. The API uses the `cpsam` model by default.

### Key Features:
- **Better boundary detection** than standard Cellpose
- **Improved small cell detection**
- **Enhanced accuracy** on diverse cell types
- **Same API interface** as standard Cellpose

### Usage:

```python
# The API automatically uses Cellpose-SAM (cpsam model)
job = client.submit_image(
    "image.png",
    model_type="cpsam",  # This is the default
    flow_threshold=0.4,
    cellprob_threshold=0.0
)
```

### Metrics for Segmentation Quality:

```python
# Get shape analysis
response = requests.get(
    f'http://localhost:8000/api/v1/metrics/shape_analysis/?job_id={job_id}'
)

shape_data = response.json()
for cell in shape_data['shape_analysis']:
    print(f"Cell {cell['cell_id']}:")
    print(f"  Aspect ratio: {cell['aspect_ratio']:.2f}")
    print(f"  Eccentricity: {cell['eccentricity']:.2f}")
    print(f"  Solidity: {cell['solidity']:.2f}")
```

## 🔍 Quality Assessment

### Segmentation Quality Metrics

The API provides tools to assess segmentation quality:

```python
from cellpose_predictions.services import MetricsService

# Compare with ground truth (if available)
quality_metrics = MetricsService.calculate_segmentation_quality(
    masks_true, masks_predicted
)

print(f"Average Precision @0.5: {quality_metrics['average_precision_50']}")
print(f"Jaccard Index: {quality_metrics['aggregated_jaccard_index']}")
```

### Visual Quality Check

- Download the segmented overlay image
- Check for over-segmentation (too many small objects)
- Check for under-segmentation (merged cells)
- Adjust `flow_threshold` and `cellprob_threshold` as needed

## 🐛 Troubleshooting

### Common Issues

1. **Out of Memory**: 
   - Use CPU instead of GPU: `CELLPOSE_DEVICE=cpu`
   - Reduce image size before processing

2. **Slow Processing**:
   - Enable GPU: `CELLPOSE_DEVICE=cuda`
   - Ensure CUDA is properly installed

3. **Poor Segmentation**:
   - Adjust `flow_threshold` (lower = more cells)
   - Adjust `cellprob_threshold` (lower = larger cells)
   - Try different `diameter` values

4. **File Download Issues**:
   - Check file permissions in media directory
   - Ensure job completed successfully

### Debug Mode

Enable detailed logging:

```python
# settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'level': 'DEBUG'},
    },
    'loggers': {
        'cellpose_predictions': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## 📚 Documentation

- **Full Tutorial**: See `CELLPOSE_API_TUTORIAL.md`
- **Example Client**: See `example_client.py`
- **Modal Integration**: See `modal_integration.py`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project follows the same license as Cellpose.

---

**Ready to segment some cells?** 🔬✨

Start with the example client and explore the comprehensive API for all your cellular analysis needs!

