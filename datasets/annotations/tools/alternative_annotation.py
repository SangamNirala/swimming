#!/usr/bin/env python3
"""
Alternative Annotation Interface for Swimming Pool Drowning Detection
Provides command-line and web-based annotation capabilities when GUI tools aren't available
"""

import os
import json
import cv2
import numpy as np
from pathlib import Path
import argparse
from typing import List, Dict, Tuple
import time

def display_image_with_annotations(image_path: Path, annotation_path: Path):
    """Display image with current annotations overlaid"""
    try:
        # Load image
        image = cv2.imread(str(image_path))
        if image is None:
            print(f"❌ Could not load image: {image_path}")
            return None
        
        # Load existing annotations
        annotations = []
        if annotation_path.exists():
            with open(annotation_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        parts = line.split()
                        if len(parts) == 5:
                            class_id = int(parts[0])
                            center_x = float(parts[1])
                            center_y = float(parts[2])
                            width = float(parts[3])
                            height = float(parts[4])
                            annotations.append((class_id, center_x, center_y, width, height))
        
        # Draw annotations on image
        h, w = image.shape[:2]
        for i, (class_id, center_x, center_y, width, height) in enumerate(annotations):
            # Convert normalized coordinates to pixel coordinates
            x1 = int((center_x - width/2) * w)
            y1 = int((center_y - height/2) * h)
            x2 = int((center_x + width/2) * w)
            y2 = int((center_y + height/2) * h)
            
            # Choose color based on class (green for swimming, red for drowning)
            color = (0, 255, 0) if class_id == 0 else (0, 0, 255)
            class_name = "Swimming" if class_id == 0 else "Drowning"
            
            # Draw rectangle
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{i+1}: {class_name}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(image, (x1, y1-label_size[1]-10), (x1+label_size[0], y1), color, -1)
            cv2.putText(image, label, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return image, annotations
    
    except Exception as e:
        print(f"❌ Error processing image: {e}")
        return None, []

def save_annotations(annotation_path: Path, annotations: List[Tuple]):
    """Save annotations in YOLO format"""
    try:
        with open(annotation_path, 'w') as f:
            for class_id, center_x, center_y, width, height in annotations:
                f.write(f"{class_id} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}\n")
        return True
    except Exception as e:
        print(f"❌ Error saving annotations: {e}")
        return False

def command_line_annotation_interface():
    """Command-line interface for annotation"""
    print("🎨 Command Line Annotation Interface")
    print("=" * 50)
    
    pilot_dir = Path("/app/datasets/annotations/pilot_batch")
    images_dir = pilot_dir / "images"
    annotations_dir = pilot_dir / "annotations"
    
    if not images_dir.exists():
        print("❌ Images directory not found")
        return
    
    # Get list of images
    image_files = sorted(list(images_dir.glob("*.jpg")))
    if not image_files:
        print("❌ No images found")
        return
    
    print(f"📊 Found {len(image_files)} images to annotate")
    
    current_index = 0
    
    while current_index < len(image_files):
        image_path = image_files[current_index]
        annotation_path = annotations_dir / f"{image_path.stem}.txt"
        
        # Clear screen (simple version)
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print(f"📷 Image {current_index + 1}/{len(image_files)}: {image_path.name}")
        print("=" * 60)
        
        # Load and display annotation info
        image_data, current_annotations = display_image_with_annotations(image_path, annotation_path)
        
        if current_annotations:
            print(f"\n📝 Current annotations ({len(current_annotations)}):")
            for i, (class_id, cx, cy, w, h) in enumerate(current_annotations):
                class_name = "Swimming" if class_id == 0 else "Drowning"
                print(f"  {i+1}: {class_name} - Center({cx:.3f}, {cy:.3f}) Size({w:.3f}, {h:.3f})")
        else:
            print("\n📝 No annotations found")
        
        print(f"\n💡 Commands:")
        print("  n/next     - Next image")
        print("  p/prev     - Previous image")
        print("  v/view     - View image details")
        print("  e/edit     - Edit annotations")
        print("  s/skip     - Skip this image")
        print("  q/quit     - Quit")
        print("  h/help     - Show help")
        
        # Get user input
        command = input("\n➤ Enter command: ").lower().strip()
        
        if command in ['q', 'quit']:
            break
        elif command in ['n', 'next', '']:
            current_index = min(current_index + 1, len(image_files) - 1)
        elif command in ['p', 'prev']:
            current_index = max(current_index - 1, 0)
        elif command in ['v', 'view']:
            show_image_details(image_path, annotation_path)
        elif command in ['e', 'edit']:
            edit_annotations(image_path, annotation_path)
        elif command in ['s', 'skip']:
            current_index += 1
        elif command in ['h', 'help']:
            show_help()
        else:
            print(f"❓ Unknown command: {command}")
            time.sleep(1)

def show_image_details(image_path: Path, annotation_path: Path):
    """Show detailed information about an image"""
    try:
        import cv2
        image = cv2.imread(str(image_path))
        if image is None:
            print("❌ Could not load image")
            return
        
        h, w, c = image.shape
        file_size = image_path.stat().st_size / 1024  # KB
        
        print(f"\n📊 Image Details:")
        print(f"  File: {image_path.name}")
        print(f"  Size: {w} × {h} pixels")
        print(f"  Channels: {c}")
        print(f"  File size: {file_size:.1f} KB")
        
        # Show annotation file info
        if annotation_path.exists():
            with open(annotation_path, 'r') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
            print(f"  Annotations: {len(lines)} bounding boxes")
        else:
            print(f"  Annotations: None")
        
        input("\nPress Enter to continue...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        input("Press Enter to continue...")

def edit_annotations(image_path: Path, annotation_path: Path):
    """Edit annotations for an image"""
    print(f"\n📝 Editing annotations for: {image_path.name}")
    
    # Load current annotations
    annotations = []
    if annotation_path.exists():
        with open(annotation_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split()
                    if len(parts) == 5:
                        class_id = int(parts[0])
                        center_x = float(parts[1])
                        center_y = float(parts[2])
                        width = float(parts[3])
                        height = float(parts[4])
                        annotations.append([class_id, center_x, center_y, width, height])
    
    while True:
        print(f"\n📋 Current annotations ({len(annotations)}):")
        if annotations:
            for i, ann in enumerate(annotations):
                class_name = "Swimming" if ann[0] == 0 else "Drowning"
                print(f"  {i+1}: {class_name} - Center({ann[1]:.3f}, {ann[2]:.3f}) Size({ann[3]:.3f}, {ann[4]:.3f})")
        else:
            print("  No annotations")
        
        print(f"\n💡 Edit Commands:")
        print("  a - Add new annotation")
        print("  d <num> - Delete annotation (e.g., 'd 1')")
        print("  c <num> <class> - Change class (e.g., 'c 1 0' for swimming, 'c 1 1' for drowning)")
        print("  s - Save and exit")
        print("  x - Exit without saving")
        
        command = input("\n➤ Edit command: ").strip()
        
        if command == 's':
            # Save annotations
            if save_annotations(annotation_path, annotations):
                print("✅ Annotations saved")
            else:
                print("❌ Failed to save annotations")
            break
        elif command == 'x':
            print("❌ Exiting without saving")
            break
        elif command == 'a':
            # Add new annotation
            add_new_annotation(annotations)
        elif command.startswith('d '):
            # Delete annotation
            try:
                idx = int(command.split()[1]) - 1
                if 0 <= idx < len(annotations):
                    removed = annotations.pop(idx)
                    class_name = "Swimming" if removed[0] == 0 else "Drowning"
                    print(f"✅ Deleted annotation {idx+1}: {class_name}")
                else:
                    print(f"❌ Invalid index: {idx+1}")
            except (ValueError, IndexError):
                print("❌ Invalid delete command. Use: d <number>")
        elif command.startswith('c '):
            # Change class
            try:
                parts = command.split()
                idx = int(parts[1]) - 1
                new_class = int(parts[2])
                if 0 <= idx < len(annotations) and new_class in [0, 1]:
                    old_class = annotations[idx][0]
                    annotations[idx][0] = new_class
                    old_name = "Swimming" if old_class == 0 else "Drowning"
                    new_name = "Swimming" if new_class == 0 else "Drowning"
                    print(f"✅ Changed annotation {idx+1}: {old_name} → {new_name}")
                else:
                    print(f"❌ Invalid parameters")
            except (ValueError, IndexError):
                print("❌ Invalid change command. Use: c <number> <class>")
        else:
            print(f"❓ Unknown command: {command}")

def add_new_annotation(annotations: List):
    """Add a new annotation"""
    print(f"\n➕ Adding new annotation")
    print("💡 Enter normalized coordinates (0.0 to 1.0)")
    
    try:
        # Get class
        while True:
            class_input = input("Class (0=Swimming, 1=Drowning): ").strip()
            if class_input in ['0', '1']:
                class_id = int(class_input)
                break
            else:
                print("❌ Please enter 0 or 1")
        
        # Get coordinates
        center_x = float(input("Center X (0.0-1.0): "))
        center_y = float(input("Center Y (0.0-1.0): "))
        width = float(input("Width (0.0-1.0): "))
        height = float(input("Height (0.0-1.0): "))
        
        # Validate coordinates
        if not all(0.0 <= coord <= 1.0 for coord in [center_x, center_y, width, height]):
            print("❌ All coordinates must be between 0.0 and 1.0")
            return
        
        # Add annotation
        annotations.append([class_id, center_x, center_y, width, height])
        class_name = "Swimming" if class_id == 0 else "Drowning"
        print(f"✅ Added {class_name} annotation")
        
    except ValueError:
        print("❌ Invalid input. Please enter numbers only.")

def show_help():
    """Show detailed help information"""
    help_text = """
🆘 Annotation Help

📏 YOLO Format Coordinates:
  All coordinates are normalized (0.0 to 1.0)
  - center_x: X coordinate of bounding box center
  - center_y: Y coordinate of bounding box center  
  - width: Width of bounding box
  - height: Height of bounding box

🏷️ Classes:
  - 0: Swimming (normal behavior)
  - 1: Drowning (distress behavior)

💡 Tips:
  - Make bounding boxes tight around people
  - Include full visible body when possible
  - Use 'swimming' when in doubt
  - 'Drowning' requires clear distress indicators

🎯 Quality Guidelines:
  - Vertical position + struggling = drowning
  - Brief underwater swimming = swimming
  - Multiple people = multiple boxes
  - Partial people = include visible parts only

📝 Keyboard Shortcuts:
  - Enter: Next image (same as 'n')
  - Numbers: Jump to annotation for editing
  - Letters: Command shortcuts (n, p, e, etc.)
"""
    print(help_text)
    input("\nPress Enter to continue...")

def create_annotation_status_report():
    """Create a status report of annotation progress"""
    print("📊 Creating annotation status report...")
    
    pilot_dir = Path("/app/datasets/annotations/pilot_batch")
    images_dir = pilot_dir / "images"
    annotations_dir = pilot_dir / "annotations"
    
    # Count files
    image_files = list(images_dir.glob("*.jpg"))
    annotation_files = list(annotations_dir.glob("*.txt"))
    
    # Analyze annotations
    stats = {
        "total_images": len(image_files),
        "annotated_images": len(annotation_files),
        "completion_rate": len(annotation_files) / len(image_files) * 100 if image_files else 0,
        "total_bboxes": 0,
        "swimming_count": 0,
        "drowning_count": 0,
        "empty_annotations": 0,
        "multi_person_images": 0
    }
    
    # Analyze each annotation file
    for ann_file in annotation_files:
        try:
            with open(ann_file, 'r') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
            
            if not lines:
                stats["empty_annotations"] += 1
            elif len(lines) > 1:
                stats["multi_person_images"] += 1
            
            for line in lines:
                parts = line.split()
                if len(parts) == 5:
                    class_id = int(parts[0])
                    stats["total_bboxes"] += 1
                    if class_id == 0:
                        stats["swimming_count"] += 1
                    elif class_id == 1:
                        stats["drowning_count"] += 1
        
        except Exception as e:
            print(f"⚠️ Error reading {ann_file}: {e}")
    
    # Print report
    print(f"\n📋 Annotation Status Report")
    print("=" * 40)
    print(f"Total Images: {stats['total_images']}")
    print(f"Annotated Images: {stats['annotated_images']}")
    print(f"Completion Rate: {stats['completion_rate']:.1f}%")
    print(f"Remaining: {stats['total_images'] - stats['annotated_images']}")
    
    print(f"\n📊 Annotation Quality:")
    print(f"Total Bounding Boxes: {stats['total_bboxes']}")
    print(f"Swimming Class: {stats['swimming_count']} ({stats['swimming_count']/max(stats['total_bboxes'],1)*100:.1f}%)")
    print(f"Drowning Class: {stats['drowning_count']} ({stats['drowning_count']/max(stats['total_bboxes'],1)*100:.1f}%)")
    print(f"Empty Annotations: {stats['empty_annotations']}")
    print(f"Multi-person Images: {stats['multi_person_images']}")
    
    return stats

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Alternative annotation interface")
    parser.add_argument("--mode", choices=["cli", "status"], default="cli",
                       help="Interface mode: cli (command line) or status (show status)")
    
    args = parser.parse_args()
    
    print("🏊 Swimming Pool Drowning Detection - Alternative Annotation")
    print("=" * 65)
    
    if args.mode == "status":
        create_annotation_status_report()
    else:
        print("\n💡 Since LabelImg GUI is not available, using command-line interface")
        print("This interface allows you to:")
        print("• View current annotations")
        print("• Edit YOLO format annotation files")
        print("• Add, delete, and modify bounding boxes")
        print("• Change class assignments")
        
        command_line_annotation_interface()
    
    print("\n✅ Alternative annotation interface complete!")

if __name__ == "__main__":
    main()