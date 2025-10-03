# Swimming Pool Drowning Detection - Dataset Documentation

## Overview

This directory contains all datasets used for training the drowning detection system. The dataset is organized into training, validation, and test sets, with two classes: **swimming** (normal behavior) and **drowning** (distress/sinking).

## Directory Structure

```
datasets/
├── train/                      # Training data (70%)
│   ├── swimming/               # Normal swimming videos/images
│   └── drowning/               # Drowning/distress videos/images
├── val/                        # Validation data (15%)
│   ├── swimming/
│   └── drowning/
├── test/                       # Test data (15%)
│   ├── swimming/
│   └── drowning/
├── raw/                        # Raw downloaded datasets (before processing)
├── scripts/                    # Dataset management scripts
├── annotations/                # Annotation files (YOLO format, JSON, etc.)
└── README.md                   # This file
```

## Dataset Sources

### Primary Roboflow Datasets

1. **Maritime Swimmer Dataset**
   - URL: https://universe.roboflow.com/maritime-cumkb/swimmer--swimmer/dataset/1
   - Description: Swimmer detection dataset with bounding box annotations
   - Classes: swimmer
   - Format: YOLO, COCO, Pascal VOC

2. **Drowning Detection (Ahmad Zidan)**
   - URL: https://universe.roboflow.com/zidan-nlsjs/drowning-detection-e6kbk
   - Description: Drowning detection with swimming and drowning classes
   - Classes: swimming, drowning
   - Format: YOLO

3. **Swimming & Drowning Detection**
   - URL: https://universe.roboflow.com/kittipat-blwh5/swimming-drowning-ndf8f
   - Description: Swimming pool surveillance dataset
   - Classes: swimming, drowning
   - Format: YOLO

4. **Drowning Detection and Prevention**
   - URL: https://universe.roboflow.com/machine-learning-computer-vision/drowning-detection-and-prevention-in-swimming-pools-ooq1f
   - Description: Comprehensive pool safety dataset
   - Classes: multiple (swimmer, drowning, etc.)
   - Format: YOLO

### Additional Sources

- **YouTube**: Public swimming pool videos
- **Vimeo**: Pool surveillance footage
- **Custom Collection**: Self-recorded videos (if available)

## Setup Instructions

### 1. Install Dependencies

```bash
cd /app/datasets/scripts
pip install -r requirements.txt
```

### 2. Configure Roboflow API

You need a Roboflow API key to download datasets:

1. Sign up at https://roboflow.com
2. Go to your workspace settings
3. Copy your API key
4. Create a `.env` file in the scripts directory:

```bash
cd /app/datasets/scripts
echo "ROBOFLOW_API_KEY=your_api_key_here" > .env
```

### 3. Download Roboflow Datasets

```bash
cd /app/datasets/scripts
python download_roboflow.py
```

This script will:
- Download all 4 Roboflow datasets
- Extract them to the `raw/` directory
- Preserve original annotations

### 4. Organize Dataset

```bash
python organize_dataset.py --split 0.7 0.15 0.15
```

This script will:
- Merge all datasets
- Remove duplicates
- Split into train/val/test (70/15/15)
- Organize by class (swimming/drowning)
- Generate statistics report

### 5. Download YouTube Videos (Optional)

```bash
python download_youtube.py --playlist <playlist_url>
```

Or manually:
1. Search for "swimming pool surveillance" on YouTube
2. Download videos using yt-dlp or online tools
3. Place in `raw/youtube/` directory
4. Run annotation tool to label them

## Dataset Statistics

### Target Dataset Size

| Split | Swimming | Drowning | Total |
|-------|----------|----------|-------|
| Train | 1400+ | 1400+ | 2800+ |
| Val   | 300+ | 300+ | 600+ |
| Test  | 300+ | 300+ | 600+ |
| **Total** | **2000+** | **2000+** | **4000+** |

### Current Dataset Status

Run this command to check current statistics:

```bash
python dataset_stats.py
```

## Data Preprocessing

### For YOLO Training (Swimmer Detection)

YOLO format annotations are included:
```
image.jpg          # Image file
image.txt          # Annotation file
```

Annotation format (per line):
```
class_id center_x center_y width height
```

### For Action Classification (Swimming vs Drowning)

Video frames are organized by class:
```
train/
  swimming/
    video1_frame001.jpg
    video1_frame002.jpg
  drowning/
    video2_frame001.jpg
    video2_frame002.jpg
```

## Data Augmentation

Applied during training:
- Horizontal flip (50%)
- Brightness adjustment (±20%)
- Contrast adjustment (±20%)
- Gaussian noise (σ=0.01)
- Color jittering
- Motion blur (water simulation)
- Random crop and resize

## Quality Control

### Verification Checklist

- [ ] All images are valid (no corrupted files)
- [ ] Annotations match image dimensions
- [ ] Class balance is reasonable (swimming vs drowning)
- [ ] No duplicate images across splits
- [ ] Bounding boxes are within image bounds
- [ ] Minimum image resolution: 640×480
- [ ] Video frame rate: 5-30 FPS

### Run Quality Checks

```bash
python verify_dataset.py
```

This will:
- Check for corrupted images
- Verify annotation formats
- Check class distribution
- Identify duplicates
- Generate quality report

## Annotation Guidelines

### Swimming (Class 0)
Normal swimming behaviors:
- Person swimming on surface
- Floating calmly
- Swimming laps (brief underwater is OK)
- Playing/splashing
- Standing/sitting in pool

### Drowning (Class 1)
Distress behaviors:
- Vertical body position
- Arms flailing or not moving
- Head tilted back, mouth open
- Submerged for extended period (>3 seconds)
- Struggling, no forward progress
- Body sinking

## Dataset Updates

To add new data:

1. Place raw files in `raw/new_batch/`
2. Run annotation tool (if needed)
3. Run organize script: `python organize_dataset.py --append`
4. Verify: `python verify_dataset.py`

## Troubleshooting

### Issue: Roboflow download fails
**Solution:** Check API key, internet connection, and dataset availability

### Issue: Not enough drowning examples
**Solution:** 
- Use data augmentation heavily
- Consider simulated drowning scenarios
- Balance with class weights during training

### Issue: Annotation format mismatch
**Solution:** Use conversion script: `python convert_annotations.py --from coco --to yolo`

## Citation

If you use these datasets, please cite the original sources:

```bibtex
@misc{roboflow-swimmer-dataset,
  title={Swimmer Dataset},
  author={Maritime CUMKB},
  year={2024},
  url={https://universe.roboflow.com/maritime-cumkb/swimmer--swimmer}
}
```

## License

Datasets are subject to their original licenses. Please check individual Roboflow dataset pages for licensing information.

## Contact

For questions or issues with the dataset:
- Open an issue in the repository
- Check Roboflow dataset pages for original dataset queries

---

**Last Updated:** 2025-01-15
**Dataset Version:** 1.0
