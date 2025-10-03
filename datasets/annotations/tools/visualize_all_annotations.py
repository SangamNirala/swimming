#!/usr/bin/env python3
"""
Visualize ALL YOLOv8s Annotations (9,342 images)
Creates images with drawn bounding boxes for complete manual validation
Organizes output in GitHub-friendly batches (max 1000 images per folder)
"""

import os
import cv2
import json
import numpy as np
from pathlib import Path
from typing import List, Dict
import sys
from datetime import datetime
import time

# Progress tracking
class ProgressTracker:
    def __init__(self, total_images):
        self.total_images = total_images
        self.processed = 0
        self.successful = 0
        self.failed = 0
        self.start_time = time.time()
        self.last_report = 0
        
    def update(self, success=True):
        self.processed += 1
        if success:
            self.successful += 1
        else:
            self.failed += 1
        
        # Report every 500 images
        if self.processed - self.last_report >= 500:
            self.report()
            self.last_report = self.processed
    
    def report(self):
        elapsed = time.time() - self.start_time
        speed = self.processed / elapsed if elapsed > 0 else 0
        remaining = (self.total_images - self.processed) / speed if speed > 0 else 0
        
        print(f"\n{'='*70}")
        print(f"📊 PROGRESS UPDATE")
        print(f"{'='*70}")
        print(f"✅ Processed: {self.processed:,} / {self.total_images:,} images ({self.processed/self.total_images*100:.1f}%)")
        print(f"✅ Successful: {self.successful:,}")
        print(f"❌ Failed: {self.failed}")
        print(f"⏱️  Speed: {speed:.1f} images/second")
        print(f"⏳ Estimated remaining time: {remaining/60:.1f} minutes")
        print(f"{'='*70}\n")
    
    def final_report(self):
        elapsed = time.time() - self.start_time
        print(f"\n{'='*70}")
        print(f"🎉 PROCESSING COMPLETE!")
        print(f"{'='*70}")
        print(f"✅ Total Processed: {self.processed:,}")
        print(f"✅ Successful: {self.successful:,}")
        print(f"❌ Failed: {self.failed}")
        print(f"⏱️  Total Time: {elapsed/60:.1f} minutes")
        print(f"⚡ Average Speed: {self.processed/elapsed:.1f} images/second")
        print(f"{'='*70}\n")


def draw_yolo_boxes(
    image_path: Path,
    annotation_path: Path,
    output_path: Path,
    class_names: dict = {0: "Swimming", 1: "Drowning"},
    colors: dict = {0: (0, 255, 0), 1: (0, 0, 255)}  # Green for swimming, Red for drowning
) -> bool:
    """
    Draw bounding boxes on image based on YOLO annotations
    
    Args:
        image_path: Path to original image
        annotation_path: Path to YOLO annotation file
        output_path: Path to save annotated image
        class_names: Dictionary mapping class IDs to names
        colors: Dictionary mapping class IDs to BGR colors
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Read image
        image = cv2.imread(str(image_path))
        if image is None:
            return False
        
        height, width = image.shape[:2]
        
        # Read annotations if file exists
        if annotation_path.exists():
            with open(annotation_path, 'r') as f:
                lines = f.readlines()
            
            num_boxes = 0
            for line in lines:
                parts = line.strip().split()
                if len(parts) != 5:
                    continue
                
                class_id = int(parts[0])
                center_x = float(parts[1])
                center_y = float(parts[2])
                box_width = float(parts[3])
                box_height = float(parts[4])
                
                # Convert YOLO format to pixel coordinates
                x1 = int((center_x - box_width / 2) * width)
                y1 = int((center_y - box_height / 2) * height)
                x2 = int((center_x + box_width / 2) * width)
                y2 = int((center_y + box_height / 2) * height)
                
                # Get color and label
                color = colors.get(class_id, (255, 255, 255))
                label = class_names.get(class_id, f"Class {class_id}")
                
                # Draw bounding box (thickness 3 for better visibility)
                cv2.rectangle(image, (x1, y1), (x2, y2), color, 3)
                
                # Draw label background
                label_text = f"{num_boxes+1}: {label}"
                (label_width, label_height), baseline = cv2.getTextSize(
                    label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
                )
                cv2.rectangle(
                    image,
                    (x1, y1 - label_height - 12),
                    (x1 + label_width + 10, y1),
                    color,
                    -1
                )
                
                # Draw label text
                cv2.putText(
                    image,
                    label_text,
                    (x1 + 5, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2
                )
                
                # Draw center point
                center_pixel_x = int(center_x * width)
                center_pixel_y = int(center_y * height)
                cv2.circle(image, (center_pixel_x, center_pixel_y), 5, (255, 255, 255), -1)
                
                num_boxes += 1
            
            # Add image info overlay
            info_text = f"{image_path.name} | {num_boxes} detection(s)"
            text_size = cv2.getTextSize(info_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            cv2.rectangle(image, (10, 10), (20 + text_size[0], 45), (0, 0, 0), -1)
            cv2.putText(image, info_text, (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Save annotated image with high quality
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), image, [cv2.IMWRITE_JPEG_QUALITY, 92])
        return True
        
    except Exception as e:
        print(f"⚠️  Error visualizing {image_path.name}: {e}")
        return False


def find_image_for_annotation(annotation_file: Path, dataset_root: Path, split: str, class_name: str) -> Path:
    """
    Find the corresponding image file for an annotation
    Checks multiple possible locations including part directories
    
    Args:
        annotation_file: Path to annotation .txt file
        dataset_root: Root of image dataset
        split: Dataset split (train/val/test)
        class_name: Class name (swimming/drowning)
    
    Returns:
        Path to image file or None if not found
    """
    img_name = annotation_file.stem + ".jpg"
    
    # Check main directory
    possible_paths = [dataset_root / split / class_name / img_name]
    
    # Check part directories (part1, part2, part3, part4, part5)
    for part_num in range(1, 6):
        possible_paths.append(
            dataset_root / split / class_name / f"part{part_num}" / img_name
        )
    
    # Return first existing path
    for path in possible_paths:
        if path.exists():
            return path
    
    return None


def organize_output_in_batches(files: List[Path], batch_size: int = 1000) -> Dict[int, List[Path]]:
    """
    Organize files into batches for GitHub compatibility
    
    Args:
        files: List of file paths
        batch_size: Maximum files per batch
    
    Returns:
        Dictionary mapping batch number to list of files
    """
    batches = {}
    for i, file_path in enumerate(files):
        batch_num = (i // batch_size) + 1
        if batch_num not in batches:
            batches[batch_num] = []
        batches[batch_num].append(file_path)
    return batches


def visualize_all_annotations(
    dataset_root: Path,
    annotations_root: Path,
    output_root: Path,
    batch_size: int = 1000
):
    """
    Visualize ALL annotations from the complete dataset
    Organizes output in batches for GitHub compatibility
    
    Args:
        dataset_root: Root of image dataset
        annotations_root: Root of batched annotation files
        output_root: Where to save visualized images
        batch_size: Maximum images per output batch folder
    """
    print(f"\n{'='*70}")
    print(f"🎨 STARTING FULL ANNOTATION VISUALIZATION")
    print(f"{'='*70}")
    print(f"📁 Dataset: {dataset_root}")
    print(f"📝 Annotations: {annotations_root}")
    print(f"💾 Output: {output_root}")
    print(f"📦 Batch Size: {batch_size} images per folder")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    output_root.mkdir(parents=True, exist_ok=True)
    
    splits = ['train', 'val', 'test']
    classes = ['swimming', 'drowning']
    
    # Count total annotations
    print("📊 Counting total annotations...")
    total_annotations = 0
    for split in splits:
        for class_name in classes:
            ann_dir = annotations_root / split / class_name
            if ann_dir.exists():
                for batch_dir in sorted(ann_dir.glob("batch_*")):
                    ann_files = list(batch_dir.glob("*.txt"))
                    total_annotations += len(ann_files)
    
    print(f"✅ Found {total_annotations:,} annotations to visualize\n")
    
    # Initialize progress tracker
    tracker = ProgressTracker(total_annotations)
    
    # Statistics
    stats = {
        "total_processed": 0,
        "total_successful": 0,
        "total_failed": 0,
        "by_split": {},
        "by_class": {"swimming": 0, "drowning": 0},
        "start_time": datetime.now().isoformat(),
        "failed_files": []
    }
    
    # Process each split and class
    for split in splits:
        stats["by_split"][split] = {"swimming": 0, "drowning": 0, "failed": 0}
        
        for class_name in classes:
            print(f"\n{'='*70}")
            print(f"🏊 Processing {split.upper()} / {class_name.upper()}")
            print(f"{'='*70}\n")
            
            # Find all annotation files for this split/class
            ann_dir = annotations_root / split / class_name
            if not ann_dir.exists():
                print(f"⚠️  Directory not found: {ann_dir}")
                continue
            
            all_annotations = []
            for batch_dir in sorted(ann_dir.glob("batch_*")):
                ann_files = list(batch_dir.glob("*.txt"))
                all_annotations.extend(ann_files)
            
            if not all_annotations:
                print(f"⚠️  No annotations found in {ann_dir}")
                continue
            
            print(f"📝 Found {len(all_annotations):,} annotations")
            
            # Organize into output batches
            output_batches = organize_output_in_batches(all_annotations, batch_size)
            print(f"📦 Will create {len(output_batches)} output batch(es)\n")
            
            # Process each annotation
            for batch_num, batch_annotations in output_batches.items():
                batch_name = f"batch_{batch_num:03d}"
                print(f"   📦 Processing {batch_name} ({len(batch_annotations)} images)...")
                
                batch_success = 0
                batch_failed = 0
                
                for ann_file in batch_annotations:
                    # Find corresponding image
                    image_path = find_image_for_annotation(
                        ann_file, dataset_root, split, class_name
                    )
                    
                    if image_path is None:
                        print(f"      ⚠️  Image not found: {ann_file.name}")
                        tracker.update(success=False)
                        batch_failed += 1
                        stats["failed_files"].append(str(ann_file))
                        continue
                    
                    # Create output path in batch folder
                    output_path = output_root / split / class_name / batch_name / f"visualized_{ann_file.stem}.jpg"
                    
                    # Draw and save
                    success = draw_yolo_boxes(image_path, ann_file, output_path)
                    
                    if success:
                        batch_success += 1
                        stats["by_split"][split][class_name] += 1
                        stats["by_class"][class_name] += 1
                    else:
                        batch_failed += 1
                        stats["by_split"][split]["failed"] += 1
                        stats["failed_files"].append(str(ann_file))
                    
                    tracker.update(success=success)
                
                print(f"      ✅ {batch_name}: {batch_success} successful, {batch_failed} failed")
    
    # Final statistics
    tracker.final_report()
    
    stats["total_processed"] = tracker.processed
    stats["total_successful"] = tracker.successful
    stats["total_failed"] = tracker.failed
    stats["end_time"] = datetime.now().isoformat()
    stats["processing_time_minutes"] = (time.time() - tracker.start_time) / 60
    
    # Save detailed statistics
    stats_file = output_root / "full_visualization_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    # Save processing log
    log_file = output_root / "visualization_log.txt"
    with open(log_file, 'w') as f:
        f.write(f"Full Annotation Visualization Log\n")
        f.write(f"{'='*70}\n\n")
        f.write(f"Start Time: {stats['start_time']}\n")
        f.write(f"End Time: {stats['end_time']}\n")
        f.write(f"Processing Time: {stats['processing_time_minutes']:.1f} minutes\n\n")
        f.write(f"Total Images: {stats['total_processed']:,}\n")
        f.write(f"Successful: {stats['total_successful']:,}\n")
        f.write(f"Failed: {stats['total_failed']}\n\n")
        f.write(f"By Class:\n")
        f.write(f"  Swimming: {stats['by_class']['swimming']:,}\n")
        f.write(f"  Drowning: {stats['by_class']['drowning']:,}\n\n")
        f.write(f"By Split:\n")
        for split, split_stats in stats['by_split'].items():
            total = split_stats['swimming'] + split_stats['drowning']
            f.write(f"  {split.capitalize()}: {total:,} images\n")
            f.write(f"    Swimming: {split_stats['swimming']:,}\n")
            f.write(f"    Drowning: {split_stats['drowning']:,}\n")
            f.write(f"    Failed: {split_stats['failed']}\n")
        
        if stats['failed_files']:
            f.write(f"\n\nFailed Files ({len(stats['failed_files'])}):\n")
            for failed in stats['failed_files'][:100]:  # Limit to first 100
                f.write(f"  {failed}\n")
    
    # Print final summary
    print(f"\n{'='*70}")
    print(f"🎉 VISUALIZATION COMPLETE!")
    print(f"{'='*70}")
    print(f"\n📊 Final Summary:")
    print(f"   Total Images Visualized: {stats['total_successful']:,} / {stats['total_processed']:,}")
    print(f"   Success Rate: {stats['total_successful']/stats['total_processed']*100:.1f}%")
    print(f"\n🏊 By Class:")
    print(f"   Swimming: {stats['by_class']['swimming']:,} images")
    print(f"   Drowning: {stats['by_class']['drowning']:,} images")
    print(f"\n📈 By Split:")
    for split in splits:
        if split in stats['by_split']:
            split_stats = stats['by_split'][split]
            total = split_stats['swimming'] + split_stats['drowning']
            print(f"   {split.capitalize()}: {total:,} images")
            print(f"      Swimming: {split_stats['swimming']:,}")
            print(f"      Drowning: {split_stats['drowning']:,}")
    
    print(f"\n💾 Output Directory: {output_root}")
    print(f"📊 Statistics File: {stats_file}")
    print(f"📝 Log File: {log_file}")
    print(f"\n✅ All visualizations complete!")
    print(f"{'='*70}\n")


def main():
    # Configuration
    dataset_root = Path("/app/datasets")
    annotations_root = Path("/app/datasets/annotations/yolov8s_annotations_batched")
    output_root = Path("/app/datasets/annotations/visualized_yolov8s_full")
    batch_size = 1000  # Max images per folder for GitHub compatibility
    
    # Verify paths exist
    if not dataset_root.exists():
        print(f"❌ Dataset not found: {dataset_root}")
        sys.exit(1)
    
    if not annotations_root.exists():
        print(f"❌ Annotations not found: {annotations_root}")
        sys.exit(1)
    
    # Start visualization
    visualize_all_annotations(
        dataset_root=dataset_root,
        annotations_root=annotations_root,
        output_root=output_root,
        batch_size=batch_size
    )


if __name__ == "__main__":
    main()
