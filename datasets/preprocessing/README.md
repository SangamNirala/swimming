# Data Preprocessing Pipeline for Swimming Pool Drowning Detection

Complete implementation of Phase 1.3 Data Preprocessing from the main project.

## 📋 Overview

This preprocessing pipeline implements all required steps for preparing swimming pool video data for drowning detection model training:

1. **Video → Frame Extraction** (5-10 FPS)
2. **Image Resizing** to 640x640 (YOLO standard) with aspect ratio preservation
3. **Normalization** (0-255 → 0-1)
4. **Data Augmentation** (all techniques including water-specific effects)
5. **Train/Val/Test Split Validation** (70/15/15 stratified)

## 🛠️ Components

### 1. Frame Extraction (`frame_extractor.py`)
Extracts frames from video files at specified FPS.

**Features:**
- Supports multiple video formats (mp4, avi, mov, mkv)
- Configurable target FPS (default: 10)
- Optional time range extraction
- Batch processing
- Progress tracking

**Usage:**
```bash
python frame_extractor.py video.mp4 ./output --fps 10
```

### 2. Image Resizing (`image_resizer.py`)
Resizes images to 640x640 with letterboxing (padding) to maintain aspect ratio.

**Features:**
- YOLO-compatible output (640x640)
- Aspect ratio preservation with padding
- Bounding box coordinate transformation
- Batch processing
- GPU-accelerated (if available)

**Usage:**
```bash
python image_resizer.py ./input_images ./output_resized --size 640 640
```

### 3. Normalization (`normalizer.py`)
Normalizes pixel values for neural network input.

**Methods:**
- `standard`: [0-255] → [0-1] (default)
- `imagenet`: ImageNet mean/std normalization
- `custom`: Custom mean/std values

**Features:**
- Batch normalization
- Denormalization for visualization
- Dataset statistics computation

**Usage:**
```python
from normalizer import ImageNormalizer

normalizer = ImageNormalizer(method='standard')
normalized = normalizer.normalize(image)
```

### 4. Data Augmentation (`augmentation.py`)
Comprehensive augmentation pipeline using Albumentations.

**Augmentation Techniques:**
- ✅ Horizontal flip (50% probability)
- ✅ Brightness adjustment (±20%)
- ✅ Contrast adjustment (±20%)
- ✅ Gaussian noise (σ=0.01)
- ✅ Color jittering
- ✅ Random crop and resize
- ✅ Motion blur (simulate water movement)
- ✅ Optical distortion (water refraction)
- ✅ Grid distortion (water surface effects)
- ✅ HSV adjustments (underwater colors)
- ✅ Random shadows
- ✅ Custom water effects (reflection, turbidity, tint)

**Usage:**
```bash
python augmentation.py image.jpg --output ./augmented --num 5
```

### 5. Dataset Validation (`dataset_validator.py`)
Validates dataset quality, structure, and splits.

**Features:**
- Split ratio verification (70/15/15)
- Class balance checking
- Image quality assessment
- Annotation-image matching
- Comprehensive reporting

**Usage:**
```bash
python dataset_validator.py /path/to/dataset --annotations /path/to/annotations
```

### 6. Complete Pipeline (`preprocess_pipeline.py`)
Orchestrates all preprocessing steps in a single pipeline.

**Usage:**
```bash
# Full preprocessing pipeline
python preprocess_pipeline.py /path/to/dataset \
    --resize \
    --augment \
    --validate \
    --annotations /path/to/annotations \
    --output-report preprocessing_report.json

# Extract frames from videos
python preprocess_pipeline.py /path/to/dataset \
    --extract-videos /path/to/videos \
    --fps 10

# Resize only
python preprocess_pipeline.py /path/to/dataset \
    --resize \
    --size 640 640

# Augment training data
python preprocess_pipeline.py /path/to/dataset \
    --augment
```

## 📊 Dataset Requirements

### Directory Structure
```
dataset/
├── train/
│   ├── swimming/
│   │   ├── part1/
│   │   ├── part2/
│   │   └── ...
│   └── drowning/
│       ├── part1/
│       └── ...
├── val/
│   ├── swimming/
│   └── drowning/
└── test/
    ├── swimming/
    └── drowning/
```

### Split Ratios
- **Train:** 70% (6,538 images)
- **Validation:** 15% (1,401 images)
- **Test:** 15% (1,403 images)
- **Total:** 9,342 images

### Class Distribution
- **Swimming (Class 0):** 6,588 images (70.5%)
- **Drowning (Class 1):** 2,754 images (29.5%)
- **Imbalance Ratio:** ~2.4x (acceptable)

## 🚀 Installation

### Dependencies
```bash
pip install opencv-python numpy albumentations pillow tqdm
```

### Quick Start
```bash
# Clone or navigate to preprocessing directory
cd /app/datasets/preprocessing

# Test on sample image
python augmentation.py sample.jpg --output ./test_output --num 5

# Run validation on current dataset
python dataset_validator.py /app/datasets --annotations /app/datasets/annotations/yolov8s_annotations_batched
```

## 📈 Performance

### Frame Extraction
- **Speed:** ~100-200 frames/second (depends on video codec)
- **Output:** JPEG images with 95% quality
- **Disk usage:** ~2-3GB for 9,342 frames

### Image Resizing
- **Speed:** ~100-200 images/second on CPU
- **Method:** Letterboxing with gray padding (114,114,114)
- **Quality:** Lossless for detection tasks

### Data Augmentation
- **Speed:** ~50-100 images/second (with all augmentations)
- **Memory:** ~100MB per batch of 32 images
- **Variations:** Up to 1000+ unique augmentations per image

## 🎯 Use Cases

### 1. Prepare Training Data
```bash
# Extract frames from videos
python preprocess_pipeline.py /app/datasets \
    --extract-videos /path/to/videos \
    --fps 10 \
    --resize \
    --output-report extraction_report.json
```

### 2. Augment Existing Dataset
```bash
# Generate 3 augmented versions per training image
python preprocess_pipeline.py /app/datasets \
    --augment \
    --output-report augmentation_report.json
```

### 3. Validate Dataset Quality
```bash
# Check splits, balance, and quality
python dataset_validator.py /app/datasets \
    --annotations /app/datasets/annotations/yolov8s_annotations_batched \
    --output validation_report.json
```

### 4. Compute Dataset Statistics
```bash
# Compute mean/std for custom normalization
python normalizer.py --compute-stats /app/datasets/train
```

## 📝 Output Formats

### Resized Images
- Format: JPEG
- Size: 640x640 pixels
- Padding: Gray (114,114,114)
- Quality: 92-95%

### Augmented Images
- Format: JPEG
- Naming: `{original_name}_aug{N}.jpg`
- Annotations: `{original_name}_aug{N}.txt` (YOLO format)

### Validation Reports
- Format: JSON
- Contains: Split ratios, class balance, quality metrics, annotation matching
- Human-readable console output

## 🔧 Configuration

### Pipeline Parameters
```python
pipeline = PreprocessingPipeline(
    dataset_root='/app/datasets',
    target_size=(640, 640),    # YOLO standard
    target_fps=10,              # Frame extraction rate
    normalize_method='standard' # Normalization method
)
```

### Augmentation Probability
Adjust augmentation probabilities in `augmentation.py`:
```python
A.HorizontalFlip(p=0.5),        # 50% chance
A.MotionBlur(p=0.3),            # 30% chance
A.GaussNoise(p=0.3),            # 30% chance
```

## ✅ Quality Checks

### Pre-flight Checklist
- [ ] Dataset directory structure correct
- [ ] All images readable (no corruption)
- [ ] Split ratios match 70/15/15
- [ ] Annotations exist for all images
- [ ] Image resolutions consistent
- [ ] Class balance acceptable (<3x imbalance)

### Run Validation
```bash
python dataset_validator.py /app/datasets \
    --annotations /app/datasets/annotations/yolov8s_annotations_batched
```

## 📚 API Reference

### VideoFrameExtractor
```python
extractor = VideoFrameExtractor(target_fps=10)
frame_count, frames = extractor.extract_frames(
    video_path='video.mp4',
    output_dir='./frames',
    start_time=0.0,    # Optional
    end_time=10.0,     # Optional
    quality=95         # JPEG quality
)
```

### ImageResizer
```python
resizer = ImageResizer(target_size=(640, 640))
resized, transform = resizer.resize_with_padding(
    image=img,
    return_transform=True
)
# Transform bounding boxes
new_bbox = resizer.transform_bbox(bbox, transform, format='yolo')
```

### ImageNormalizer
```python
normalizer = ImageNormalizer(method='standard')
normalized = normalizer.normalize(image)
denormalized = normalizer.denormalize(normalized)
```

### DataAugmentation
```python
augmenter = DataAugmentation(mode='train', img_size=(640, 640))
result = augmenter(image, bboxes, class_labels)
augmented_img = result['image']
augmented_bboxes = result['bboxes']
```

## 🐛 Troubleshooting

### Issue: Images not resizing properly
**Solution:** Check if OpenCV is installed correctly
```bash
python -c "import cv2; print(cv2.__version__)"
```

### Issue: Augmentation too slow
**Solution:** Reduce augmentation probability or disable heavy augmentations
```python
# In augmentation.py, reduce p values
A.OpticalDistortion(p=0.1)  # Reduce from 0.2
```

### Issue: Memory errors during batch processing
**Solution:** Process in smaller batches or reduce image size
```python
pipeline.augment_training_data(max_images=1000)  # Process only 1000
```

## 📊 Benchmark Results

### Current Dataset (9,342 images)
- **Split Ratios:** ✅ 70.0% / 15.0% / 15.0% (Perfect!)
- **Class Balance:** ✅ 2.4x imbalance (Acceptable)
- **Image Quality:** ✅ No corrupted images
- **Resolution:** 720p-1080p (variable)
- **Annotations:** ✅ 100% coverage

### Processing Times (estimated)
- **Frame Extraction:** ~5-10 minutes for 100 videos
- **Resizing:** ~2-3 minutes for 9,342 images
- **Augmentation:** ~10-15 minutes for 2x augmentation
- **Validation:** ~1-2 minutes

## 🎓 Best Practices

1. **Always validate before training**
   ```bash
   python dataset_validator.py /app/datasets
   ```

2. **Use augmentation for training set only**
   - Never augment validation/test sets
   - Maintain original data distribution

3. **Monitor class balance**
   - Use weighted loss if imbalance > 3x
   - Consider oversampling minority class

4. **Save preprocessing configurations**
   - Document all parameters used
   - Enable reproducibility

5. **Check output samples**
   - Visually inspect augmented images
   - Verify bounding box transformations

## 🔗 Integration with YOLO Training

### Prepare Data for YOLOv8
```yaml
# data.yaml
path: /app/datasets/resized
train: train
val: val
test: test

nc: 2  # Number of classes
names: ['swimming', 'drowning']
```

### Train YOLOv8
```bash
yolo train data=data.yaml model=yolov8n.pt epochs=100 imgsz=640
```

## 📧 Support

For issues or questions:
1. Check troubleshooting section
2. Review validation reports
3. Inspect sample outputs
4. Check logs for error messages

---

**Version:** 1.0.0  
**Last Updated:** 2025-01-03  
**Status:** ✅ Production Ready
