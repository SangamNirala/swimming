#!/usr/bin/env python3
"""
Visualize YOLOv8s Annotations with Bounding Boxes
Creates images with drawn bounding boxes for quality verification
"""

import os
import cv2
import json
import numpy as np
from pathlib import Path
import argparse
from typing import List, Tuple
import sys

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
    """
    try:
        # Read image
        image = cv2.imread(str(image_path))
        if image is None:
            print(f"⚠️  Could not read image: {image_path.name}")
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
                
                # Draw bounding box
                cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
                
                # Draw label background
                label_text = f"{num_boxes+1}: {label}"
                (label_width, label_height), baseline = cv2.getTextSize(
                    label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
                )
                cv2.rectangle(
                    image,
                    (x1, y1 - label_height - 10),
                    (x1 + label_width, y1),
                    color,
                    -1
                )
                
                # Draw label text
                cv2.putText(
                    image,
                    label_text,
                    (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2
                )
                
                # Draw center point
                center_pixel_x = int(center_x * width)
                center_pixel_y = int(center_y * height)
                cv2.circle(image, (center_pixel_x, center_pixel_y), 5, color, -1)
                
                num_boxes += 1
            
            # Add image info overlay
            info_text = f"{image_path.name} | {num_boxes} detection(s)"
            cv2.rectangle(image, (10, 10), (10 + len(info_text) * 10, 40), (0, 0, 0), -1)
            cv2.putText(image, info_text, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Save annotated image
        cv2.imwrite(str(output_path), image)
        return True
        
    except Exception as e:
        print(f"⚠️  Error visualizing {image_path.name}: {e}")
        return False

def visualize_sample_annotations(
    dataset_root: Path,
    annotations_root: Path,
    output_root: Path,
    num_samples: int = 50,
    splits: List[str] = None,
    classes: List[str] = None
):
    """
    Visualize sample annotations from each split and class
    
    Args:
        dataset_root: Root of image dataset
        annotations_root: Root of annotation files
        output_root: Where to save visualized images
        num_samples: Number of samples per split/class combination
        splits: List of splits to visualize (default: ['train', 'val', 'test'])
        classes: List of classes to visualize (default: ['swimming', 'drowning'])
    """
    if splits is None:
        splits = ['train', 'val', 'test']
    if classes is None:
        classes = ['swimming', 'drowning']
    
    print(f"\n🎨 Visualizing Annotations")
    print(f"📁 Dataset: {dataset_root}")
    print(f"📝 Annotations: {annotations_root}")
    print(f"💾 Output: {output_root}")
    print(f"🔢 Samples per category: {num_samples}")
    
    output_root.mkdir(parents=True, exist_ok=True)
    
    stats = {
        "total_visualized": 0,
        "by_split": {},
        "by_class": {"swimming": 0, "drowning": 0}
    }
    
    for split in splits:
        stats["by_split"][split] = {"swimming": 0, "drowning": 0}
        
        for class_name in classes:
            print(f"\n📸 Processing {split}/{class_name}...")
            
            # Find annotation files
            annotation_dir = annotations_root / split / class_name
            if not annotation_dir.exists():
                print(f"   ⚠️  Directory not found: {annotation_dir}")
                continue
            
            annotation_files = list(annotation_dir.glob("*.txt"))
            
            # Sample annotations
            num_to_process = min(num_samples, len(annotation_files))
            sampled_files = annotation_files[:num_to_process]
            
            for ann_file in sampled_files:
                # Find corresponding image in dataset
                # Check multiple possible locations
                possible_image_paths = []
                
                # Check main directory
                img_name = ann_file.stem + ".jpg"
                possible_image_paths.append(dataset_root / split / class_name / img_name)
                
                # Check part directories
                for part_num in range(1, 6):
                    possible_image_paths.append(
                        dataset_root / split / class_name / f"part{part_num}" / img_name
                    )
                
                # Find first existing image path
                image_path = None
                for path in possible_image_paths:
                    if path.exists():
                        image_path = path
                        break
                
                if image_path is None:
                    print(f"   ⚠️  Image not found for: {ann_file.name}")
                    continue
                
                # Create output path
                output_path = output_root / split / class_name / f"annotated_{img_name}"
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Draw and save
                if draw_yolo_boxes(image_path, ann_file, output_path):
                    stats["total_visualized"] += 1
                    stats["by_split"][split][class_name] += 1
                    stats["by_class"][class_name] += 1
            
            print(f"   ✅ Visualized {stats['by_split'][split][class_name]} images")
    
    # Save visualization stats
    stats_file = output_root / "visualization_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    # Print summary
    print("\n" + "="*70)
    print("🎨 VISUALIZATION COMPLETE!")
    print("="*70)
    print(f"\n📊 Summary:")
    print(f"   Total Images Visualized: {stats['total_visualized']}")
    print(f"\n🏊 By Class:")
    print(f"   Swimming: {stats['by_class']['swimming']} images")
    print(f"   Drowning: {stats['by_class']['drowning']} images")
    print(f"\n📈 By Split:")
    for split in splits:
        if split in stats['by_split']:
            split_stats = stats['by_split'][split]
            total = split_stats.get('swimming', 0) + split_stats.get('drowning', 0)
            print(f"   {split.capitalize()}: {total} images (Swimming: {split_stats.get('swimming', 0)}, Drowning: {split_stats.get('drowning', 0)})")
    
    print(f"\n💾 Output Directory: {output_root}")
    print(f"📊 Statistics File: {stats_file}")
    print("\n✅ Visualization complete! Check the output directory to view annotated images.")
    print("="*70)

def create_grid_visualization(
    visualized_root: Path,
    output_file: Path,
    grid_size: Tuple[int, int] = (5, 4),
    max_images: int = 20
):
    """
    Create a grid visualization of multiple annotated images
    
    Args:
        visualized_root: Root directory of visualized images
        output_file: Output file path for grid image
        grid_size: (rows, cols) for grid layout
        max_images: Maximum number of images to include
    """
    print(f"\n🖼️  Creating grid visualization...")
    
    try:
        # Find all visualized images
        image_files = list(visualized_root.rglob("annotated_*.jpg"))
        
        if not image_files:
            print("   ⚠️  No visualized images found")
            return
        
        # Sample images
        num_images = min(max_images, len(image_files))
        sampled_images = image_files[:num_images]
        
        # Read first image to get dimensions
        first_img = cv2.imread(str(sampled_images[0]))
        if first_img is None:
            print("   ⚠️  Could not read first image")
            return
        
        # Resize dimensions for grid
        cell_height, cell_width = 400, 600
        
        rows, cols = grid_size
        grid_image = np.zeros((rows * cell_height, cols * cell_width, 3), dtype=np.uint8)
        
        for idx, img_path in enumerate(sampled_images[:rows*cols]):
            row = idx // cols
            col = idx % cols
            
            img = cv2.imread(str(img_path))
            if img is not None:
                # Resize image to fit cell
                img_resized = cv2.resize(img, (cell_width, cell_height))
                
                # Place in grid
                y_start = row * cell_height
                y_end = (row + 1) * cell_height
                x_start = col * cell_width
                x_end = (col + 1) * cell_width
                
                grid_image[y_start:y_end, x_start:x_end] = img_resized
        
        # Save grid
        cv2.imwrite(str(output_file), grid_image)
        print(f"   ✅ Grid saved: {output_file}")
        
    except Exception as e:
        print(f"   ⚠️  Error creating grid: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Visualize YOLOv8s Annotations"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="/app/datasets",
        help="Path to dataset root directory"
    )
    parser.add_argument(
        "--annotations",
        type=str,
        default="/app/datasets/annotations/yolov8s_annotations",
        help="Path to annotations directory"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="/app/datasets/annotations/visualized_yolov8s",
        help="Path to output directory for visualized images"
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=50,
        help="Number of samples to visualize per split/class"
    )
    parser.add_argument(
        "--create-grid",
        action="store_true",
        help="Create grid visualization of samples"
    )
    
    args = parser.parse_args()
    
    dataset_root = Path(args.dataset)
    annotations_root = Path(args.annotations)
    output_root = Path(args.output)
    
    if not dataset_root.exists():
        print(f"❌ Dataset not found: {dataset_root}")
        sys.exit(1)
    
    if not annotations_root.exists():
        print(f"❌ Annotations not found: {annotations_root}")
        sys.exit(1)
    
    # Visualize samples
    visualize_sample_annotations(
        dataset_root=dataset_root,
        annotations_root=annotations_root,
        output_root=output_root,
        num_samples=args.samples
    )
    
    # Create grid if requested
    if args.create_grid:
        grid_file = output_root / "annotation_grid.jpg"
        create_grid_visualization(output_root, grid_file)

if __name__ == "__main__":
    main()
