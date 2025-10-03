#!/usr/bin/env python3
"""
Semi-Automated Pre-Annotation Using Pretrained YOLO
Generates initial bounding box annotations to speed up manual annotation process
"""

import os
import json
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict
import argparse
import time

def check_dependencies():
    """Check if required libraries are available"""
    print("🔍 Checking dependencies...")
    
    missing_deps = []
    
    try:
        import cv2
        print("  ✅ OpenCV")
    except ImportError:
        missing_deps.append("opencv-python")
    
    try:
        from ultralytics import YOLO
        print("  ✅ Ultralytics YOLO")
    except ImportError:
        missing_deps.append("ultralytics")
    
    try:
        import torch
        print("  ✅ PyTorch")
    except ImportError:
        missing_deps.append("torch")
    
    if missing_deps:
        print(f"\n❌ Missing dependencies: {', '.join(missing_deps)}")
        print("Install with: pip install " + " ".join(missing_deps))
        return False
    
    return True

def download_pretrained_model():
    """Download pretrained YOLO model for person detection"""
    print("\n🤖 Setting up pretrained YOLO model...")
    
    try:
        from ultralytics import YOLO
        
        # Use YOLOv8n for faster inference on CPU
        model_name = "yolov8n.pt"  # Nano model - fastest
        
        print(f"📥 Loading {model_name} (this may download the model)...")
        model = YOLO(model_name)
        
        print("✅ Model loaded successfully")
        return model
        
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return None

def detect_people_in_image(model, image_path: Path, confidence_threshold: float = 0.25):
    """
    Detect people in image using YOLO model
    Returns list of bounding boxes for detected people
    """
    try:
        import cv2
        
        # Read image
        image = cv2.imread(str(image_path))
        if image is None:
            print(f"❌ Could not read image: {image_path}")
            return []
        
        # Run YOLO inference
        results = model(image, conf=confidence_threshold, verbose=False)
        
        # Extract person detections (class_id = 0 in COCO dataset)
        detections = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    # Get class ID and confidence
                    class_id = int(box.cls.item())
                    confidence = float(box.conf.item())
                    
                    # Only keep person detections (class 0 in COCO)
                    if class_id == 0:  # Person class in COCO
                        # Get bounding box coordinates (xyxy format)
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        
                        # Convert to YOLO format (normalized center coordinates + width/height)
                        image_height, image_width = image.shape[:2]
                        
                        center_x = (x1 + x2) / 2 / image_width
                        center_y = (y1 + y2) / 2 / image_height
                        width = (x2 - x1) / image_width
                        height = (y2 - y1) / image_height
                        
                        detections.append({
                            "center_x": center_x,
                            "center_y": center_y,
                            "width": width,
                            "height": height,
                            "confidence": confidence
                        })
        
        return detections
        
    except Exception as e:
        print(f"❌ Error processing {image_path}: {e}")
        return []

def create_yolo_annotation_file(detections: List[Dict], output_path: Path, default_class: int = 0):
    """
    Create YOLO format annotation file from detections
    Default class is 0 (swimming) - annotators will correct to 1 (drowning) if needed
    """
    try:
        with open(output_path, 'w') as f:
            for detection in detections:
                # Format: class_id center_x center_y width height
                f.write(f"{default_class} {detection['center_x']:.6f} {detection['center_y']:.6f} "
                       f"{detection['width']:.6f} {detection['height']:.6f}\n")
        return True
    except Exception as e:
        print(f"❌ Error writing annotation file {output_path}: {e}")
        return False

def pre_annotate_pilot_batch(model, confidence_threshold: float = 0.25, default_class: int = 0):
    """Pre-annotate all images in pilot batch"""
    print(f"\n🎯 Pre-annotating pilot batch images...")
    
    pilot_dir = Path("/app/datasets/annotations/pilot_batch")
    images_dir = pilot_dir / "images"
    annotations_dir = pilot_dir / "annotations"
    
    # Create annotations directory if it doesn't exist
    annotations_dir.mkdir(parents=True, exist_ok=True)
    
    # Get list of images
    image_files = list(images_dir.glob("*.jpg"))
    total_images = len(image_files)
    
    if total_images == 0:
        print("❌ No images found in pilot batch. Run create_pilot_batch.py first.")
        return False
    
    print(f"📊 Processing {total_images} images...")
    
    processed_count = 0
    annotation_stats = {
        "total_images": total_images,
        "processed_images": 0,
        "images_with_detections": 0,
        "total_detections": 0,
        "failed_images": 0,
        "average_detections_per_image": 0.0
    }
    
    start_time = time.time()
    
    for i, image_path in enumerate(image_files):
        # Progress indicator
        if i % 10 == 0:
            print(f"  Processing image {i+1}/{total_images}...")
        
        # Create annotation filename
        annotation_path = annotations_dir / f"{image_path.stem}.txt"
        
        # Skip if annotation already exists (unless forcing overwrite)
        if annotation_path.exists():
            print(f"  ⏭️  Skipping {image_path.name} (annotation exists)")
            processed_count += 1
            continue
        
        # Detect people in image
        detections = detect_people_in_image(model, image_path, confidence_threshold)
        
        # Create annotation file (even if no detections - creates empty file)
        if create_yolo_annotation_file(detections, annotation_path, default_class):
            processed_count += 1
            annotation_stats["total_detections"] += len(detections)
            if len(detections) > 0:
                annotation_stats["images_with_detections"] += 1
        else:
            annotation_stats["failed_images"] += 1
    
    # Calculate final statistics
    annotation_stats["processed_images"] = processed_count
    annotation_stats["average_detections_per_image"] = (
        annotation_stats["total_detections"] / max(processed_count, 1)
    )
    
    elapsed_time = time.time() - start_time
    
    # Save statistics
    stats_file = pilot_dir / "pre_annotation_stats.json"
    annotation_stats["processing_time_seconds"] = elapsed_time
    annotation_stats["confidence_threshold"] = confidence_threshold
    annotation_stats["default_class"] = default_class
    
    with open(stats_file, 'w') as f:
        json.dump(annotation_stats, f, indent=2)
    
    # Print summary
    print(f"\n✅ Pre-annotation complete!")
    print(f"📊 Statistics:")
    print(f"  Processed: {processed_count}/{total_images} images")
    print(f"  Images with detections: {annotation_stats['images_with_detections']}")
    print(f"  Total detections: {annotation_stats['total_detections']}")
    print(f"  Average detections/image: {annotation_stats['average_detections_per_image']:.1f}")
    print(f"  Failed: {annotation_stats['failed_images']}")
    print(f"  Processing time: {elapsed_time:.1f} seconds")
    print(f"📁 Statistics saved: {stats_file}")
    
    return True

def create_pre_annotation_report():
    """Create a report explaining the pre-annotation results"""
    print(f"\n📄 Creating pre-annotation report...")
    
    pilot_dir = Path("/app/datasets/annotations/pilot_batch")
    report_file = pilot_dir / "PRE_ANNOTATION_REPORT.md"
    
    report_content = """# Pre-Annotation Report

## 🤖 Automated Pre-Annotation Complete

This report summarizes the automated pre-annotation process using a pretrained YOLO model.

### What Was Done
1. **Model Used:** YOLOv8n (nano) - optimized for CPU inference
2. **Detection Target:** Person class (COCO class ID 0)
3. **Default Class:** All detections labeled as "swimming" (class 0)
4. **Output Format:** YOLO format (.txt files)

### Why Pre-Annotation?
- **Speed up manual work:** Provides starting point for annotators
- **Consistency:** Ensures standard bounding box format
- **Coverage:** Reduces chance of missing people in images

### Important Notes
⚠️ **All detections are initially labeled as "swimming" (class 0)**

**Annotators must:**
- Review each bounding box for accuracy
- Adjust boxes to be tighter around people
- **Change class to "drowning" (class 1) where appropriate**
- Add any missed people
- Remove false positive detections

### Next Steps
1. **Review pre-annotations in LabelImg**
2. **Correct bounding boxes** (make tighter, adjust position)
3. **Update class labels** (swimming vs drowning based on behavior)
4. **Add missed detections** (people not found by YOLO)
5. **Remove false positives** (non-people detected as people)

### Quality Control
- Pre-annotations are a **starting point only**
- **Manual review is essential** for quality
- Focus on **behavior-based class assignment**
- Ensure **tight, accurate bounding boxes**

### Files Generated
- `.txt` files for each image (YOLO format)
- `pre_annotation_stats.json` (processing statistics)
- This report file

---

**Remember:** Pre-annotations speed up work but require careful manual review!
"""
    
    with open(report_file, 'w') as f:
        f.write(report_content)
    
    print(f"✅ Report saved: {report_file}")
    return report_file

def validate_pre_annotations():
    """Validate the generated pre-annotations"""
    print(f"\n🔍 Validating pre-annotations...")
    
    pilot_dir = Path("/app/datasets/annotations/pilot_batch")
    images_dir = pilot_dir / "images"
    annotations_dir = pilot_dir / "annotations"
    
    # Check if directories exist
    if not images_dir.exists():
        print("❌ Images directory not found")
        return False
    
    if not annotations_dir.exists():
        print("❌ Annotations directory not found")
        return False
    
    # Get image and annotation files
    image_files = set(f.stem for f in images_dir.glob("*.jpg"))
    annotation_files = set(f.stem for f in annotations_dir.glob("*.txt"))
    
    # Check matching files
    missing_annotations = image_files - annotation_files
    extra_annotations = annotation_files - image_files
    
    validation_results = {
        "total_images": len(image_files),
        "total_annotations": len(annotation_files),
        "missing_annotations": len(missing_annotations),
        "extra_annotations": len(extra_annotations),
        "format_errors": 0,
        "coordinate_errors": 0
    }
    
    # Validate annotation file formats
    format_errors = []
    coordinate_errors = []
    
    for annotation_file in annotations_dir.glob("*.txt"):
        try:
            with open(annotation_file, 'r') as f:
                lines = f.readlines()
                
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                
                parts = line.split()
                
                # Check format: class_id center_x center_y width height
                if len(parts) != 5:
                    format_errors.append(f"{annotation_file.name}:{line_num} - Wrong number of values")
                    continue
                
                try:
                    class_id = int(parts[0])
                    center_x = float(parts[1])
                    center_y = float(parts[2])
                    width = float(parts[3])
                    height = float(parts[4])
                    
                    # Validate coordinate ranges (should be 0.0 to 1.0)
                    if not (0.0 <= center_x <= 1.0 and 0.0 <= center_y <= 1.0 and
                            0.0 <= width <= 1.0 and 0.0 <= height <= 1.0):
                        coordinate_errors.append(f"{annotation_file.name}:{line_num} - Coordinates out of range")
                    
                    # Validate class ID (should be 0 or 1)
                    if class_id not in [0, 1]:
                        format_errors.append(f"{annotation_file.name}:{line_num} - Invalid class ID: {class_id}")
                
                except ValueError:
                    format_errors.append(f"{annotation_file.name}:{line_num} - Non-numeric values")
        
        except Exception as e:
            format_errors.append(f"{annotation_file.name} - Could not read file: {e}")
    
    validation_results["format_errors"] = len(format_errors)
    validation_results["coordinate_errors"] = len(coordinate_errors)
    
    # Print validation results
    print(f"📊 Validation Results:")
    print(f"  Images: {validation_results['total_images']}")
    print(f"  Annotations: {validation_results['total_annotations']}")
    print(f"  Missing annotations: {validation_results['missing_annotations']}")
    print(f"  Extra annotations: {validation_results['extra_annotations']}")
    print(f"  Format errors: {validation_results['format_errors']}")
    print(f"  Coordinate errors: {validation_results['coordinate_errors']}")
    
    # Report specific errors if any
    if format_errors:
        print(f"\n❌ Format Errors:")
        for error in format_errors[:5]:  # Show first 5 errors
            print(f"  {error}")
        if len(format_errors) > 5:
            print(f"  ... and {len(format_errors) - 5} more")
    
    if coordinate_errors:
        print(f"\n❌ Coordinate Errors:")
        for error in coordinate_errors[:5]:  # Show first 5 errors
            print(f"  {error}")
        if len(coordinate_errors) > 5:
            print(f"  ... and {len(coordinate_errors) - 5} more")
    
    if missing_annotations:
        print(f"\n⚠️  Missing Annotations:")
        for missing in list(missing_annotations)[:5]:  # Show first 5
            print(f"  {missing}.jpg")
        if len(missing_annotations) > 5:
            print(f"  ... and {len(missing_annotations) - 5} more")
    
    # Save validation results
    validation_file = pilot_dir / "validation_results.json"
    with open(validation_file, 'w') as f:
        json.dump(validation_results, f, indent=2)
    
    print(f"\n✅ Validation complete. Results saved: {validation_file}")
    
    # Return success if no critical errors
    return (validation_results["format_errors"] == 0 and 
            validation_results["coordinate_errors"] == 0 and
            validation_results["missing_annotations"] == 0)

def main():
    """Main pre-annotation function"""
    parser = argparse.ArgumentParser(description="Pre-annotate images using YOLO")
    parser.add_argument("--confidence", type=float, default=0.25, 
                       help="Confidence threshold for detections (0.0-1.0)")
    parser.add_argument("--default-class", type=int, default=0,
                       help="Default class for all detections (0=swimming, 1=drowning)")
    parser.add_argument("--validate-only", action="store_true",
                       help="Only validate existing annotations")
    
    args = parser.parse_args()
    
    print("🤖 Swimming Pool Drowning Detection - Pre-Annotation")
    print("=" * 60)
    
    if args.validate_only:
        print("🔍 Validation-only mode")
        success = validate_pre_annotations()
        print("\n✅ Validation complete!" if success else "\n❌ Validation found issues!")
        return
    
    # Step 1: Check dependencies
    if not check_dependencies():
        print("❌ Cannot proceed without required dependencies")
        return
    
    # Step 2: Load pretrained model
    model = download_pretrained_model()
    if model is None:
        print("❌ Cannot proceed without YOLO model")
        return
    
    # Step 3: Pre-annotate pilot batch
    success = pre_annotate_pilot_batch(model, args.confidence, args.default_class)
    if not success:
        print("❌ Pre-annotation failed")
        return
    
    # Step 4: Create report
    report_file = create_pre_annotation_report()
    
    # Step 5: Validate results
    validation_success = validate_pre_annotations()
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 Pre-Annotation Complete!")
    
    if validation_success:
        print("✅ All validations passed")
    else:
        print("⚠️  Some validation issues found - check validation_results.json")
    
    print(f"\n📋 What was created:")
    print("• YOLO format annotation files (.txt)")
    print("• Pre-annotation statistics (JSON)")
    print("• Validation results (JSON)")  
    print(f"• Pre-annotation report: {report_file}")
    
    print(f"\n🎯 Next Steps:")
    print("1. Launch LabelImg: python tools/launch_labelimg.py")
    print("2. Review and correct pre-annotations:")
    print("   • Adjust bounding box sizes and positions")
    print("   • Change classes from 'swimming' to 'drowning' where appropriate")
    print("   • Add any missed people")
    print("   • Remove false positive detections")
    print("3. Follow annotation guidelines for consistency")
    print("4. Quality review after 50-100 images")
    
    print(f"\n💡 Remember:")
    print("• All detections start as 'swimming' class")
    print("• You must manually assign 'drowning' class where appropriate")
    print("• Pre-annotations are just a starting point!")

if __name__ == "__main__":
    main()