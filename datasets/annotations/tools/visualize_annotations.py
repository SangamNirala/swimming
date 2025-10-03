#!/usr/bin/env python3
"""
Annotation Visualizer
Creates visual images with bounding boxes drawn to inspect annotation quality
"""

import cv2
import numpy as np
from pathlib import Path
import argparse
import json
from typing import List, Tuple
import os

def draw_bounding_boxes(image_path: Path, annotation_path: Path, output_path: Path = None):
    """Draw bounding boxes on image and save annotated version"""
    
    # Load image
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"❌ Could not load image: {image_path}")
        return None
    
    image_height, image_width = image.shape[:2]
    
    # Load annotations
    annotations = []
    if annotation_path.exists():
        with open(annotation_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    parts = line.split()
                    if len(parts) == 5:
                        try:
                            class_id = int(parts[0])
                            center_x = float(parts[1])
                            center_y = float(parts[2])
                            width = float(parts[3])
                            height = float(parts[4])
                            annotations.append((class_id, center_x, center_y, width, height, line_num))
                        except ValueError:
                            print(f"⚠️  Invalid annotation at line {line_num} in {annotation_path}")
    
    # Draw bounding boxes
    annotated_image = image.copy()
    
    for i, (class_id, center_x, center_y, width, height, line_num) in enumerate(annotations):
        # Convert normalized coordinates to pixel coordinates
        x1 = int((center_x - width/2) * image_width)
        y1 = int((center_y - height/2) * image_height)
        x2 = int((center_x + width/2) * image_width)
        y2 = int((center_y + height/2) * image_height)
        
        # Ensure coordinates are within image bounds
        x1 = max(0, min(x1, image_width-1))
        y1 = max(0, min(y1, image_height-1))
        x2 = max(0, min(x2, image_width-1))
        y2 = max(0, min(y2, image_height-1))
        
        # Choose colors and labels
        if class_id == 0:  # Swimming
            color = (0, 255, 0)  # Green
            class_name = "Swimming"
        elif class_id == 1:  # Drowning
            color = (0, 0, 255)  # Red
            class_name = "Drowning"
        else:
            color = (255, 0, 255)  # Magenta for unknown
            class_name = f"Class_{class_id}"
        
        # Draw rectangle
        thickness = 3
        cv2.rectangle(annotated_image, (x1, y1), (x2, y2), color, thickness)
        
        # Create label with ID and class
        label = f"{i+1}: {class_name}"
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        
        # Draw label background
        label_bg_x1 = x1
        label_bg_y1 = y1 - label_size[1] - 10
        label_bg_x2 = x1 + label_size[0] + 10
        label_bg_y2 = y1
        
        # Ensure label background is within image
        if label_bg_y1 < 0:
            label_bg_y1 = y2
            label_bg_y2 = y2 + label_size[1] + 10
        
        cv2.rectangle(annotated_image, (label_bg_x1, label_bg_y1), (label_bg_x2, label_bg_y2), color, -1)
        
        # Draw label text
        text_x = x1 + 5
        text_y = label_bg_y1 + label_size[1] + 5 if label_bg_y1 >= 0 else y2 + label_size[1] + 5
        cv2.putText(annotated_image, label, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Draw center point
        center_pixel_x = int(center_x * image_width)
        center_pixel_y = int(center_y * image_height)
        cv2.circle(annotated_image, (center_pixel_x, center_pixel_y), 5, color, -1)
    
    # Add image info overlay
    info_text = f"Image: {image_path.name} | Annotations: {len(annotations)}"
    cv2.putText(annotated_image, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(annotated_image, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 1)
    
    # Add legend
    legend_y = 60
    cv2.putText(annotated_image, "Green = Swimming | Red = Drowning", (10, legend_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(annotated_image, "Green = Swimming | Red = Drowning", (10, legend_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    
    # Save annotated image
    if output_path:
        success = cv2.imwrite(str(output_path), annotated_image)
        if not success:
            print(f"❌ Failed to save annotated image: {output_path}")
            return None
    
    return annotated_image, annotations

def visualize_pilot_batch():
    """Create visualized versions of all pilot batch images"""
    print("🎨 Creating visual annotations for pilot batch...")
    
    pilot_dir = Path("/app/datasets/annotations/pilot_batch")
    images_dir = pilot_dir / "images"
    annotations_dir = pilot_dir / "annotations"
    visualized_dir = pilot_dir / "visualized"
    
    # Create output directory
    visualized_dir.mkdir(exist_ok=True)
    
    # Get list of images
    image_files = sorted(list(images_dir.glob("*.jpg")))
    
    if not image_files:
        print("❌ No images found in pilot batch")
        return
    
    print(f"📊 Processing {len(image_files)} images...")
    
    stats = {
        "total_images": len(image_files),
        "images_with_annotations": 0,
        "total_bboxes": 0,
        "swimming_count": 0,
        "drowning_count": 0,
        "processed_successfully": 0,
        "failed_images": []
    }
    
    for i, image_path in enumerate(image_files):
        if i % 25 == 0:
            print(f"  Processing image {i+1}/{len(image_files)}...")
        
        # Get corresponding annotation file
        annotation_path = annotations_dir / f"{image_path.stem}.txt"
        output_path = visualized_dir / f"annotated_{image_path.name}"
        
        try:
            # Create visualized image
            result = draw_bounding_boxes(image_path, annotation_path, output_path)
            
            if result:
                annotated_image, annotations = result
                stats["processed_successfully"] += 1
                
                if annotations:
                    stats["images_with_annotations"] += 1
                    stats["total_bboxes"] += len(annotations)
                    
                    for class_id, _, _, _, _, _ in annotations:
                        if class_id == 0:
                            stats["swimming_count"] += 1
                        elif class_id == 1:
                            stats["drowning_count"] += 1
            else:
                stats["failed_images"].append(image_path.name)
                
        except Exception as e:
            print(f"❌ Error processing {image_path.name}: {e}")
            stats["failed_images"].append(image_path.name)
    
    # Save statistics
    stats_file = visualized_dir / "visualization_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    # Print summary
    print(f"\n✅ Visualization complete!")
    print(f"📊 Summary:")
    print(f"  Total images: {stats['total_images']}")
    print(f"  Successfully processed: {stats['processed_successfully']}")
    print(f"  Images with annotations: {stats['images_with_annotations']}")
    print(f"  Total bounding boxes: {stats['total_bboxes']}")
    print(f"  Swimming (green): {stats['swimming_count']}")
    print(f"  Drowning (red): {stats['drowning_count']}")
    print(f"  Failed images: {len(stats['failed_images'])}")
    
    if stats["failed_images"]:
        print(f"⚠️  Failed images: {stats['failed_images'][:5]}...")
    
    print(f"\n📁 Visualized images saved to: {visualized_dir}")
    print(f"📊 Statistics saved to: {stats_file}")
    
    return stats

def create_annotation_grid():
    """Create a grid view of multiple annotated images"""
    print("🖼️  Creating annotation grid view...")
    
    pilot_dir = Path("/app/datasets/annotations/pilot_batch")
    visualized_dir = pilot_dir / "visualized"
    
    if not visualized_dir.exists():
        print("❌ No visualized images found. Run visualization first.")
        return
    
    # Get annotated images
    annotated_images = sorted(list(visualized_dir.glob("annotated_*.jpg")))
    
    if len(annotated_images) < 4:
        print("❌ Need at least 4 images for grid view")
        return
    
    # Select first 12 images for grid (3x4)
    grid_images = annotated_images[:12]
    
    # Load and resize images
    grid_size = (3, 4)  # 3 rows, 4 columns
    target_size = (300, 200)  # Resize each image to this size
    
    # Create grid
    grid_rows = []
    
    for row in range(grid_size[0]):
        row_images = []
        for col in range(grid_size[1]):
            idx = row * grid_size[1] + col
            if idx < len(grid_images):
                img = cv2.imread(str(grid_images[idx]))
                if img is not None:
                    img_resized = cv2.resize(img, target_size)
                    row_images.append(img_resized)
                else:
                    # Create blank image if loading fails
                    blank = np.zeros((target_size[1], target_size[0], 3), dtype=np.uint8)
                    row_images.append(blank)
            else:
                # Create blank image for empty slots
                blank = np.zeros((target_size[1], target_size[0], 3), dtype=np.uint8)
                row_images.append(blank)
        
        # Combine row images horizontally
        row_combined = np.hstack(row_images)
        grid_rows.append(row_combined)
    
    # Combine all rows vertically
    grid_image = np.vstack(grid_rows)
    
    # Add title
    title_height = 50
    title_img = np.ones((title_height, grid_image.shape[1], 3), dtype=np.uint8) * 255
    title_text = "Swimming Pool Drowning Detection - Annotation Samples"
    cv2.putText(title_img, title_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
    
    # Combine title and grid
    final_image = np.vstack([title_img, grid_image])
    
    # Save grid
    grid_path = visualized_dir / "annotation_grid.jpg"
    cv2.imwrite(str(grid_path), final_image)
    
    print(f"✅ Grid view created: {grid_path}")
    return grid_path

def create_sample_viewer():
    """Create an HTML viewer for browsing annotated images"""
    print("🌐 Creating web viewer for annotations...")
    
    pilot_dir = Path("/app/datasets/annotations/pilot_batch")
    visualized_dir = pilot_dir / "visualized"
    
    if not visualized_dir.exists():
        print("❌ No visualized images found. Run visualization first.")
        return
    
    # Get all annotated images
    annotated_images = sorted(list(visualized_dir.glob("annotated_*.jpg")))
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Swimming Pool Drowning Detection - Annotation Viewer</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .stats {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin: 20px 0;
        }
        .stat-box {
            background: #e3f2fd;
            padding: 10px 20px;
            border-radius: 5px;
            text-align: center;
        }
        .legend {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin: 20px 0;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .color-box {
            width: 20px;
            height: 20px;
            border: 2px solid #333;
        }
        .swimming { background-color: #4CAF50; }
        .drowning { background-color: #F44336; }
        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
        }
        .image-card {
            background: white;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            text-align: center;
        }
        .image-card img {
            max-width: 100%;
            height: auto;
            border-radius: 5px;
            border: 1px solid #ddd;
        }
        .image-info {
            margin-top: 10px;
            font-size: 14px;
            color: #666;
        }
        .controls {
            text-align: center;
            margin: 20px 0;
        }
        .btn {
            background: #2196F3;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
        }
        .btn:hover {
            background: #1976D2;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏊 Swimming Pool Drowning Detection</h1>
        <h2>Annotation Quality Review</h2>
        
        <div class="stats">
            <div class="stat-box">
                <strong>{total_images}</strong><br>Total Images
            </div>
            <div class="stat-box">
                <strong>{images_with_annotations}</strong><br>With Annotations
            </div>
            <div class="stat-box">
                <strong>{total_bboxes}</strong><br>Bounding Boxes
            </div>
        </div>
        
        <div class="legend">
            <div class="legend-item">
                <div class="color-box swimming"></div>
                <span>Swimming (Normal Behavior)</span>
            </div>
            <div class="legend-item">
                <div class="color-box drowning"></div>
                <span>Drowning (Distress Behavior)</span>
            </div>
        </div>
        
        <div class="controls">
            <button class="btn" onclick="showAll()">Show All</button>
            <button class="btn" onclick="showWithAnnotations()">With Annotations Only</button>
            <button class="btn" onclick="showWithoutAnnotations()">Without Annotations</button>
        </div>
    </div>

    <div class="gallery" id="gallery">
"""
    
    # Load statistics
    stats_file = visualized_dir / "visualization_stats.json"
    stats = {"total_images": 0, "images_with_annotations": 0, "total_bboxes": 0}
    if stats_file.exists():
        with open(stats_file, 'r') as f:
            stats = json.load(f)
    
    # Add image cards
    for img_path in annotated_images:
        # Get original filename
        original_name = img_path.name.replace("annotated_", "")
        
        # Check if has annotations
        annotation_file = pilot_dir / "annotations" / f"{img_path.stem.replace('annotated_', '')}.txt"
        has_annotations = "Yes" if annotation_file.exists() and annotation_file.stat().st_size > 0 else "No"
        
        html_content += f"""
        <div class="image-card" data-has-annotations="{has_annotations}">
            <img src="{img_path.name}" alt="{original_name}">
            <div class="image-info">
                <strong>{original_name}</strong><br>
                Annotations: {has_annotations}
            </div>
        </div>
        """
    
    # Add JavaScript and closing tags
    html_content += """
    </div>

    <script>
        function showAll() {
            const cards = document.querySelectorAll('.image-card');
            cards.forEach(card => card.style.display = 'block');
        }
        
        function showWithAnnotations() {
            const cards = document.querySelectorAll('.image-card');
            cards.forEach(card => {
                if (card.getAttribute('data-has-annotations') === 'Yes') {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        }
        
        function showWithoutAnnotations() {
            const cards = document.querySelectorAll('.image-card');
            cards.forEach(card => {
                if (card.getAttribute('data-has-annotations') === 'No') {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        }
    </script>
</body>
</html>
    """
    
    # Replace placeholders
    html_content = html_content.replace('{total_images}', str(stats.get('total_images', 0)))
    html_content = html_content.replace('{images_with_annotations}', str(stats.get('images_with_annotations', 0)))
    html_content = html_content.replace('{total_bboxes}', str(stats.get('total_bboxes', 0)))
    
    # Save HTML file
    html_file = visualized_dir / "annotation_viewer.html"
    with open(html_file, 'w') as f:
        f.write(html_content)
    
    print(f"✅ Web viewer created: {html_file}")
    print(f"🌐 Open in browser to view annotated images")
    
    return html_file

def main():
    """Main visualization function"""
    parser = argparse.ArgumentParser(description="Visualize YOLO annotations")
    parser.add_argument("--mode", choices=["all", "single", "grid", "web"], default="all",
                       help="Visualization mode")
    parser.add_argument("--image", help="Single image to visualize (for single mode)")
    
    args = parser.parse_args()
    
    print("🎨 Swimming Pool Drowning Detection - Annotation Visualizer")
    print("=" * 65)
    
    if args.mode == "single":
        if not args.image:
            print("❌ Please specify --image for single mode")
            return
        
        pilot_dir = Path("/app/datasets/annotations/pilot_batch")
        image_path = pilot_dir / "images" / args.image
        annotation_path = pilot_dir / "annotations" / f"{Path(args.image).stem}.txt"
        output_path = pilot_dir / "visualized" / f"annotated_{args.image}"
        
        Path(output_path).parent.mkdir(exist_ok=True)
        
        result = draw_bounding_boxes(image_path, annotation_path, output_path)
        if result:
            print(f"✅ Visualized: {output_path}")
        else:
            print("❌ Failed to create visualization")
    
    elif args.mode == "grid":
        visualize_pilot_batch()  # Ensure images are visualized first
        create_annotation_grid()
    
    elif args.mode == "web":
        visualize_pilot_batch()  # Ensure images are visualized first
        create_sample_viewer()
    
    else:  # "all" mode
        # Create visualizations
        stats = visualize_pilot_batch()
        
        # Create grid view
        create_annotation_grid()
        
        # Create web viewer
        create_sample_viewer()
        
        # Summary
        print("\n" + "=" * 65)
        print("🎉 Complete Visualization Suite Created!")
        
        visualized_dir = Path("/app/datasets/annotations/pilot_batch/visualized")
        print(f"\n📁 Output Files:")
        print(f"  📷 Individual images: {visualized_dir}/annotated_*.jpg")
        print(f"  🖼️  Grid view: {visualized_dir}/annotation_grid.jpg")
        print(f"  🌐 Web viewer: {visualized_dir}/annotation_viewer.html")
        print(f"  📊 Statistics: {visualized_dir}/visualization_stats.json")
        
        print(f"\n💡 How to View:")
        print(f"  1. Browse individual images in: {visualized_dir}")
        print(f"  2. View grid: open annotation_grid.jpg")
        print(f"  3. Interactive viewer: open annotation_viewer.html in browser")
        
        print(f"\n📊 Quick Stats:")
        if stats:
            print(f"  Total images: {stats['total_images']}")
            print(f"  With annotations: {stats['images_with_annotations']}")
            print(f"  Total bounding boxes: {stats['total_bboxes']}")
            print(f"  Swimming (green boxes): {stats['swimming_count']}")
            print(f"  Drowning (red boxes): {stats['drowning_count']}")

if __name__ == "__main__":
    main()