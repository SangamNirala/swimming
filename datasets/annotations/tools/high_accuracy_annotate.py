#!/usr/bin/env python3
"""
High Accuracy Annotation System using YOLOv8s Model
Processes all images in dataset with improved detection accuracy
"""

import os
import json
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import argparse
import time
from datetime import datetime
import traceback

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
    
    try:
        import numpy as np
        print("  ✅ NumPy")
    except ImportError:
        missing_deps.append("numpy")
    
    if missing_deps:
        print(f"\n❌ Missing dependencies: {', '.join(missing_deps)}")
        print("\nInstall them with:")
        print(f"  pip install {' '.join(missing_deps)}")
        return False
    
    return True

def get_class_from_path(image_path: Path) -> int:
    """
    Determine class based on directory structure
    Returns: 0 for swimming, 1 for drowning
    """
    path_str = str(image_path).lower()
    
    # Check directory structure for class
    if 'drowning' in path_str:
        return 1  # Drowning class
    elif 'swimming' in path_str:
        return 0  # Swimming class
    else:
        # Default to swimming if unclear
        return 0

def detect_people_yolov8s(model, image_path: Path, confidence_threshold: float = 0.20):
    """
    Detect people in image using YOLOv8s model (more accurate than nano)
    Returns list of bounding boxes for detected people
    
    Args:
        model: YOLOv8s model instance
        image_path: Path to image
        confidence_threshold: Confidence threshold for detections (lower = more detections)
    """
    try:
        import cv2
        
        # Read image
        image = cv2.imread(str(image_path))
        if image is None:
            print(f"⚠️  Could not read image: {image_path.name}")
            return []
        
        # Run YOLO inference with YOLOv8s
        # Lower confidence threshold to catch more people in challenging pool scenarios
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
                        
                        # Validate bounding box
                        if x2 <= x1 or y2 <= y1:
                            continue
                        
                        # Convert to YOLO format (normalized center coordinates + width/height)
                        image_height, image_width = image.shape[:2]
                        
                        center_x = (x1 + x2) / 2 / image_width
                        center_y = (y1 + y2) / 2 / image_height
                        width = (x2 - x1) / image_width
                        height = (y2 - y1) / image_height
                        
                        # Ensure values are within valid range
                        center_x = max(0.0, min(1.0, center_x))
                        center_y = max(0.0, min(1.0, center_y))
                        width = max(0.0, min(1.0, width))
                        height = max(0.0, min(1.0, height))
                        
                        detections.append({
                            "center_x": center_x,
                            "center_y": center_y,
                            "width": width,
                            "height": height,
                            "confidence": confidence
                        })
        
        return detections
        
    except Exception as e:
        print(f"⚠️  Error processing {image_path.name}: {e}")
        return []

def create_yolo_annotation(detections: List[Dict], output_path: Path, class_id: int) -> bool:
    """
    Create YOLO format annotation file
    Format: class_id center_x center_y width height (one line per detection)
    """
    try:
        with open(output_path, 'w') as f:
            for detection in detections:
                f.write(
                    f"{class_id} "
                    f"{detection['center_x']:.6f} "
                    f"{detection['center_y']:.6f} "
                    f"{detection['width']:.6f} "
                    f"{detection['height']:.6f}\n"
                )
        return True
    except Exception as e:
        print(f"⚠️  Error writing annotation {output_path.name}: {e}")
        return False

def find_all_images(dataset_root: Path) -> List[Tuple[Path, str, str]]:
    """
    Find all images in dataset
    Returns: List of (image_path, split, class) tuples
    """
    images = []
    
    splits = ['train', 'val', 'test']
    classes = ['swimming', 'drowning']
    
    for split in splits:
        for class_name in classes:
            # Check multiple possible directory structures
            possible_dirs = [
                dataset_root / split / class_name,
                dataset_root / split / class_name / "part1",
                dataset_root / split / class_name / "part2",
                dataset_root / split / class_name / "part3",
                dataset_root / split / class_name / "part4",
                dataset_root / split / class_name / "part5"
            ]
            
            for class_dir in possible_dirs:
                if class_dir.exists():
                    for img_path in class_dir.glob("*.jpg"):
                        images.append((img_path, split, class_name))
    
    return images

def process_dataset(
    model,
    dataset_root: Path,
    output_root: Path,
    confidence_threshold: float = 0.20,
    batch_size: int = 100,
    max_images: int = None
):
    """
    Process entire dataset with YOLOv8s model
    
    Args:
        model: YOLOv8s model instance
        dataset_root: Root directory of dataset (/app/datasets)
        output_root: Root directory for annotations
        confidence_threshold: Detection confidence threshold
        batch_size: Process and report every N images
        max_images: Maximum images to process (None = all)
    """
    print(f"\n🚀 Starting High-Accuracy Annotation with YOLOv8s")
    print(f"📁 Dataset: {dataset_root}")
    print(f"💾 Output: {output_root}")
    print(f"🎯 Confidence Threshold: {confidence_threshold}")
    
    # Find all images
    print("\n🔍 Scanning dataset...")
    all_images = find_all_images(dataset_root)
    
    if not all_images:
        print("❌ No images found in dataset!")
        return False
    
    total_images = len(all_images)
    if max_images:
        all_images = all_images[:max_images]
        total_images = len(all_images)
    
    print(f"✅ Found {total_images} images to process")
    
    # Statistics
    stats = {
        "start_time": datetime.now().isoformat(),
        "model": "YOLOv8s",
        "confidence_threshold": confidence_threshold,
        "total_images": total_images,
        "processed_images": 0,
        "images_with_detections": 0,
        "total_detections": 0,
        "failed_images": 0,
        "swimming_images": 0,
        "drowning_images": 0,
        "swimming_detections": 0,
        "drowning_detections": 0,
        "split_stats": {
            "train": {"total": 0, "with_detections": 0, "detections": 0},
            "val": {"total": 0, "with_detections": 0, "detections": 0},
            "test": {"total": 0, "with_detections": 0, "detections": 0}
        }
    }
    
    start_time = time.time()
    
    # Process each image
    for idx, (image_path, split, class_name) in enumerate(all_images, 1):
        try:
            # Progress report every batch_size images
            if idx % batch_size == 0 or idx == 1:
                elapsed = time.time() - start_time
                speed = idx / elapsed if elapsed > 0 else 0
                remaining = (total_images - idx) / speed if speed > 0 else 0
                print(f"\n📊 Progress: {idx}/{total_images} ({idx/total_images*100:.1f}%)")
                print(f"   Speed: {speed:.1f} images/sec | Est. remaining: {remaining/60:.1f} min")
            
            # Determine class from directory structure
            class_id = 1 if class_name == 'drowning' else 0
            
            # Update split stats
            stats["split_stats"][split]["total"] += 1
            
            # Detect people
            detections = detect_people_yolov8s(model, image_path, confidence_threshold)
            
            # Create output directory structure
            output_dir = output_root / split / class_name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create annotation file
            annotation_path = output_dir / f"{image_path.stem}.txt"
            
            if create_yolo_annotation(detections, annotation_path, class_id):
                stats["processed_images"] += 1
                
                num_detections = len(detections)
                if num_detections > 0:
                    stats["images_with_detections"] += 1
                    stats["total_detections"] += num_detections
                    stats["split_stats"][split]["with_detections"] += 1
                    stats["split_stats"][split]["detections"] += num_detections
                    
                    if class_id == 0:
                        stats["swimming_images"] += 1
                        stats["swimming_detections"] += num_detections
                    else:
                        stats["drowning_images"] += 1
                        stats["drowning_detections"] += num_detections
            else:
                stats["failed_images"] += 1
                
        except Exception as e:
            print(f"❌ Error processing {image_path.name}: {e}")
            stats["failed_images"] += 1
            traceback.print_exc()
    
    # Final statistics
    elapsed_total = time.time() - start_time
    stats["end_time"] = datetime.now().isoformat()
    stats["processing_time_seconds"] = elapsed_total
    stats["processing_time_minutes"] = elapsed_total / 60
    stats["images_per_second"] = stats["processed_images"] / elapsed_total if elapsed_total > 0 else 0
    stats["detection_rate"] = (stats["images_with_detections"] / stats["processed_images"] * 100) if stats["processed_images"] > 0 else 0
    stats["avg_detections_per_image"] = stats["total_detections"] / stats["processed_images"] if stats["processed_images"] > 0 else 0
    
    # Save statistics
    stats_file = output_root / "annotation_statistics.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    # Print final report
    print("\n" + "="*70)
    print("🎉 ANNOTATION COMPLETE!")
    print("="*70)
    print(f"\n📊 Overall Statistics:")
    print(f"   Total Images Processed: {stats['processed_images']:,}")
    print(f"   Images with Detections: {stats['images_with_detections']:,} ({stats['detection_rate']:.1f}%)")
    print(f"   Total Detections: {stats['total_detections']:,}")
    print(f"   Avg Detections per Image: {stats['avg_detections_per_image']:.2f}")
    print(f"   Failed Images: {stats['failed_images']}")
    
    print(f"\n🏊 Class Distribution:")
    print(f"   Swimming: {stats['swimming_images']:,} images, {stats['swimming_detections']:,} detections")
    print(f"   Drowning: {stats['drowning_images']:,} images, {stats['drowning_detections']:,} detections")
    
    print(f"\n📈 Split Statistics:")
    for split in ['train', 'val', 'test']:
        split_data = stats['split_stats'][split]
        if split_data['total'] > 0:
            detection_rate = (split_data['with_detections'] / split_data['total'] * 100)
            print(f"   {split.capitalize()}: {split_data['total']:,} images, "
                  f"{split_data['with_detections']:,} with detections ({detection_rate:.1f}%), "
                  f"{split_data['detections']:,} total detections")
    
    print(f"\n⏱️  Performance:")
    print(f"   Total Time: {stats['processing_time_minutes']:.1f} minutes")
    print(f"   Speed: {stats['images_per_second']:.1f} images/second")
    
    print(f"\n💾 Output:")
    print(f"   Annotations: {output_root}")
    print(f"   Statistics: {stats_file}")
    
    print("\n✅ High-accuracy annotation system complete!")
    print("="*70)
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description="High-Accuracy Annotation using YOLOv8s Model"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="/app/datasets",
        help="Path to dataset root directory"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="/app/datasets/annotations/yolov8s_annotations",
        help="Path to output annotations directory"
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.20,
        help="Confidence threshold for detections (0.0-1.0, lower=more detections)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Report progress every N images"
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=None,
        help="Maximum number of images to process (None=all)"
    )
    parser.add_argument(
        "--download-model",
        action="store_true",
        help="Only download YOLOv8s model and exit"
    )
    
    args = parser.parse_args()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    print("\n🤖 Initializing YOLOv8s Model...")
    print("   (This will download the model if not already cached)")
    
    try:
        from ultralytics import YOLO
        
        # Load YOLOv8s model (more accurate than nano)
        model = YOLO('yolov8s.pt')
        print("✅ YOLOv8s model loaded successfully!")
        
        if args.download_model:
            print("\n✅ Model downloaded successfully. Exiting.")
            return
        
        # Process dataset
        dataset_root = Path(args.dataset)
        output_root = Path(args.output)
        
        if not dataset_root.exists():
            print(f"❌ Dataset directory not found: {dataset_root}")
            sys.exit(1)
        
        # Create output directory
        output_root.mkdir(parents=True, exist_ok=True)
        
        success = process_dataset(
            model=model,
            dataset_root=dataset_root,
            output_root=output_root,
            confidence_threshold=args.confidence,
            batch_size=args.batch_size,
            max_images=args.max_images
        )
        
        if not success:
            sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
