# Swimming Pool Drowning Detection - Annotation System

## Phase 1.2: Data Annotation for YOLO Training

### Overview
This directory contains the complete annotation system for adding bounding box annotations to 9,342 swimming pool images in YOLO format.

### Directory Structure
```
annotations/
├── README.md                    # This file
├── guidelines/
│   └── annotation_guidelines.md # Comprehensive annotation guidelines
├── tools/
│   ├── setup_labelimg.py       # LabelImg installation and setup
│   ├── pre_annotate.py         # Semi-automated pre-annotation using YOLO
│   ├── validate_annotations.py # Quality control and validation
│   └── progress_tracker.py     # Track annotation progress
├── pilot_batch/
│   ├── images/                 # 200-300 selected images
│   ├── annotations/            # YOLO format annotations (.txt)
│   └── labelimg_sessions/      # LabelImg working directories
├── quality_control/
│   ├── sample_review/          # 20-30 sample annotations for review
│   └── validation_reports/     # Quality control reports
└── workflows/
    ├── batch_processing.py     # Batch annotation workflow
    ├── convert_formats.py      # Format conversion utilities
    └── automation_scripts.py   # Workflow automation
```

### Annotation Specifications

**YOLO Format Requirements:**
- Each image needs a corresponding .txt file with same base name
- Format: `class_id center_x center_y width height` (normalized 0-1)
- Class 0: "swimming" (normal behavior, safe swimming)
- Class 1: "drowning" (distress, sinking, struggling)

**Example:**
```
# For image: swimming_train_00001.jpg
# Annotation file: swimming_train_00001.txt
0 0.523 0.634 0.145 0.287    # Swimming person at center-right
1 0.234 0.456 0.098 0.234    # Drowning person at left
```

### Workflow Process

1. **Setup Phase:**
   - Install and configure LabelImg
   - Create annotation guidelines
   - Select pilot batch (200-300 images)

2. **Pre-annotation:**
   - Run pretrained YOLO model on images
   - Generate initial bounding box predictions
   - Convert to LabelImg format

3. **Manual Correction:**
   - Open images in LabelImg
   - Review/correct pre-annotations
   - Add missing annotations
   - Adjust bounding boxes for accuracy

4. **Quality Control:**
   - Validate YOLO format
   - Check bounding box coordinates
   - Review class assignments
   - Generate quality reports

5. **Scaling:**
   - Apply to all 9,342 images in batches
   - Track progress and quality metrics
   - Maintain consistency across annotators

### Quick Start

```bash
cd /app/datasets/annotations
python tools/setup_labelimg.py          # Install LabelImg
python tools/create_pilot_batch.py      # Select 200-300 images
python tools/pre_annotate.py            # Generate initial annotations
python tools/launch_labelimg.py         # Start annotation session
```

### Status Tracking

- [ ] Phase 1.2.1: Setup and Guidelines (Target: 2025-01-15)
- [ ] Phase 1.2.2: Pilot Batch Annotation (Target: 2025-01-16) 
- [ ] Phase 1.2.3: Quality Review and Approval (Target: 2025-01-17)
- [ ] Phase 1.2.4: Full Dataset Annotation (Target: 2025-01-20)
- [ ] Phase 1.2.5: Final Validation (Target: 2025-01-21)

---

**Current Status:** Setting up infrastructure  
**Next Step:** Create annotation guidelines and setup tools