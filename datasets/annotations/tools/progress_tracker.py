#!/usr/bin/env python3
"""
Annotation Progress Tracker
Tracks annotation progress, quality metrics, and provides real-time status updates
"""

import os
import json
import time
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import argparse

def load_pilot_metadata():
    """Load pilot batch metadata"""
    pilot_dir = Path("/app/datasets/annotations/pilot_batch")
    metadata_file = pilot_dir / "pilot_metadata.json"
    
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            return json.load(f)
    else:
        # Create basic metadata structure
        return {
            "creation_date": datetime.now().strftime("%Y-%m-%d"),
            "total_images": 0,
            "images": [],
            "annotation_progress": {
                "total": 0,
                "completed": 0,
                "reviewed": 0,
                "quality_approved": False
            }
        }

def update_progress_tracking():
    """Update annotation progress tracking"""
    print("📊 Updating progress tracking...")
    
    pilot_dir = Path("/app/datasets/annotations/pilot_batch")
    images_dir = pilot_dir / "images"
    annotations_dir = pilot_dir / "annotations"
    
    # Count files
    image_files = list(images_dir.glob("*.jpg")) if images_dir.exists() else []
    annotation_files = list(annotations_dir.glob("*.txt")) if annotations_dir.exists() else []
    
    # Create file mapping
    image_stems = {f.stem for f in image_files}
    annotation_stems = {f.stem for f in annotation_files}
    
    # Load metadata
    metadata = load_pilot_metadata()
    
    # Update file list in metadata if needed
    if len(metadata.get("images", [])) != len(image_files):
        metadata["images"] = [
            {
                "filename": f.name,
                "stem": f.stem,
                "annotated": f.stem in annotation_stems,
                "reviewed": False,
                "last_modified": f.stat().st_mtime if f.exists() else 0
            }
            for f in image_files
        ]
    else:
        # Update annotation status for existing entries
        for img_info in metadata["images"]:
            img_info["annotated"] = img_info["stem"] in annotation_stems
    
    # Update progress summary
    completed_count = len(annotation_stems)
    metadata["annotation_progress"] = {
        "total": len(image_files),
        "completed": completed_count,
        "reviewed": sum(1 for img in metadata["images"] if img.get("reviewed", False)),
        "completion_rate": completed_count / len(image_files) * 100 if image_files else 0,
        "last_updated": datetime.now().isoformat()
    }
    
    # Save updated metadata
    metadata_file = pilot_dir / "pilot_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return metadata

def analyze_annotation_quality():
    """Analyze quality of completed annotations"""
    print("🔍 Analyzing annotation quality...")
    
    pilot_dir = Path("/app/datasets/annotations/pilot_batch")
    annotations_dir = pilot_dir / "annotations"
    
    if not annotations_dir.exists():
        return {"error": "Annotations directory not found"}
    
    quality_metrics = {
        "total_files": 0,
        "total_bboxes": 0,
        "class_distribution": Counter(),
        "bbox_size_stats": {
            "widths": [],
            "heights": [],
            "areas": []
        },
        "files_with_no_annotations": 0,
        "files_with_multiple_people": 0,
        "average_people_per_image": 0.0
    }
    
    annotation_files = list(annotations_dir.glob("*.txt"))
    quality_metrics["total_files"] = len(annotation_files)
    
    bbox_counts = []
    
    for annotation_file in annotation_files:
        try:
            with open(annotation_file, 'r') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
            
            bbox_count = len(lines)
            bbox_counts.append(bbox_count)
            
            if bbox_count == 0:
                quality_metrics["files_with_no_annotations"] += 1
            elif bbox_count > 1:
                quality_metrics["files_with_multiple_people"] += 1
            
            for line in lines:
                parts = line.split()
                if len(parts) == 5:
                    try:
                        class_id = int(parts[0])
                        center_x = float(parts[1])
                        center_y = float(parts[2])
                        width = float(parts[3])
                        height = float(parts[4])
                        
                        quality_metrics["class_distribution"][class_id] += 1
                        quality_metrics["bbox_size_stats"]["widths"].append(width)
                        quality_metrics["bbox_size_stats"]["heights"].append(height)
                        quality_metrics["bbox_size_stats"]["areas"].append(width * height)
                        
                    except ValueError:
                        continue  # Skip invalid lines
        
        except Exception as e:
            print(f"⚠️  Error reading {annotation_file}: {e}")
    
    quality_metrics["total_bboxes"] = sum(quality_metrics["class_distribution"].values())
    quality_metrics["average_people_per_image"] = (
        sum(bbox_counts) / len(bbox_counts) if bbox_counts else 0.0
    )
    
    # Calculate statistics for bbox sizes
    if quality_metrics["bbox_size_stats"]["widths"]:
        widths = quality_metrics["bbox_size_stats"]["widths"]
        heights = quality_metrics["bbox_size_stats"]["heights"]
        areas = quality_metrics["bbox_size_stats"]["areas"]
        
        quality_metrics["bbox_size_stats"]["avg_width"] = sum(widths) / len(widths)
        quality_metrics["bbox_size_stats"]["avg_height"] = sum(heights) / len(heights)
        quality_metrics["bbox_size_stats"]["avg_area"] = sum(areas) / len(areas)
        quality_metrics["bbox_size_stats"]["min_width"] = min(widths)
        quality_metrics["bbox_size_stats"]["max_width"] = max(widths)
        quality_metrics["bbox_size_stats"]["min_height"] = min(heights)
        quality_metrics["bbox_size_stats"]["max_height"] = max(heights)
    
    return quality_metrics

def estimate_completion_time(metadata):
    """Estimate completion time based on current progress"""
    progress = metadata.get("annotation_progress", {})
    
    completed = progress.get("completed", 0)
    total = progress.get("total", 0)
    
    if completed == 0 or total == 0:
        return {"error": "Insufficient data for estimation"}
    
    # Try to estimate based on annotation timestamps
    images_with_annotations = [
        img for img in metadata.get("images", []) 
        if img.get("annotated", False)
    ]
    
    if len(images_with_annotations) < 2:
        return {"error": "Need at least 2 annotations for time estimation"}
    
    # Simple estimation based on completion rate
    completion_rate = completed / total
    remaining = total - completed
    
    # Assume average annotation rate
    estimated_minutes_per_image = 2.5  # Conservative estimate
    estimated_remaining_minutes = remaining * estimated_minutes_per_image
    
    return {
        "remaining_images": remaining,
        "completion_rate": completion_rate * 100,
        "estimated_time_remaining": {
            "minutes": estimated_remaining_minutes,
            "hours": estimated_remaining_minutes / 60,
            "formatted": f"{int(estimated_remaining_minutes // 60)}h {int(estimated_remaining_minutes % 60)}m"
        },
        "estimated_completion_date": (
            datetime.now() + timedelta(minutes=estimated_remaining_minutes)
        ).strftime("%Y-%m-%d %H:%M")
    }

def generate_progress_report():
    """Generate comprehensive progress report"""
    print("📋 Generating progress report...")
    
    # Update progress first
    metadata = update_progress_tracking()
    
    # Analyze quality
    quality_metrics = analyze_annotation_quality()
    
    # Estimate completion time
    time_estimation = estimate_completion_time(metadata)
    
    # Create report
    pilot_dir = Path("/app/datasets/annotations/pilot_batch")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = pilot_dir / f"progress_report_{timestamp}.md"
    
    progress = metadata["annotation_progress"]
    
    report_content = f"""# Annotation Progress Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Phase:** Pilot Batch Annotation  
**Dataset:** Swimming Pool Drowning Detection

## 📊 Overall Progress

| Metric | Value |
|--------|-------|
| Total Images | {progress['total']} |
| Completed Annotations | {progress['completed']} |
| Completion Rate | {progress.get('completion_rate', 0):.1f}% |
| Remaining Images | {progress['total'] - progress['completed']} |
| Reviewed Annotations | {progress.get('reviewed', 0)} |

## 📈 Progress Visualization

```
Progress: [{('█' * int(progress.get('completion_rate', 0) // 2)).ljust(50)}] {progress.get('completion_rate', 0):.1f}%
```

## 🎯 Annotation Quality Metrics

"""
    
    if "error" not in quality_metrics:
        swimming_count = quality_metrics["class_distribution"].get(0, 0)
        drowning_count = quality_metrics["class_distribution"].get(1, 0)
        total_bboxes = quality_metrics["total_bboxes"]
        
        report_content += f"""| Metric | Value |
|--------|-------|
| Total Bounding Boxes | {total_bboxes} |
| Swimming Class (0) | {swimming_count} ({swimming_count/max(total_bboxes,1)*100:.1f}%) |
| Drowning Class (1) | {drowning_count} ({drowning_count/max(total_bboxes,1)*100:.1f}%) |
| Average People per Image | {quality_metrics['average_people_per_image']:.1f} |
| Images with No Annotations | {quality_metrics['files_with_no_annotations']} |
| Images with Multiple People | {quality_metrics['files_with_multiple_people']} |
"""
        
        if quality_metrics["bbox_size_stats"]["widths"]:
            bbox_stats = quality_metrics["bbox_size_stats"]
            report_content += f"""
### Bounding Box Size Statistics

| Dimension | Average | Min | Max |
|-----------|---------|-----|-----|
| Width | {bbox_stats['avg_width']:.3f} | {bbox_stats['min_width']:.3f} | {bbox_stats['max_width']:.3f} |
| Height | {bbox_stats['avg_height']:.3f} | {bbox_stats['min_height']:.3f} | {bbox_stats['max_height']:.3f} |
| Area | {bbox_stats['avg_area']:.3f} | - | - |
"""
    
    # Add time estimation
    if "error" not in time_estimation:
        report_content += f"""
## ⏱️ Time Estimation

| Metric | Value |
|--------|-------|
| Remaining Images | {time_estimation['remaining_images']} |
| Estimated Time Remaining | {time_estimation['estimated_time_remaining']['formatted']} |
| Estimated Completion | {time_estimation['estimated_completion_date']} |
| Current Completion Rate | {time_estimation['completion_rate']:.1f}% |
"""
    
    # Add recommendations
    report_content += """
## 💡 Recommendations

### Quality Control:
"""
    
    if quality_metrics.get("files_with_no_annotations", 0) > 0:
        report_content += f"- Review {quality_metrics['files_with_no_annotations']} images with no annotations\n"
    
    completion_rate = progress.get('completion_rate', 0)
    if completion_rate < 25:
        report_content += "- Continue steady annotation pace\n"
        report_content += "- Focus on establishing consistent quality standards\n"
    elif completion_rate < 75:
        report_content += "- Consider quality review of completed annotations\n"
        report_content += "- Check for consistent class assignments\n"
    else:
        report_content += "- Prepare for final quality review\n"
        report_content += "- Plan transition to full dataset annotation\n"
    
    drowning_rate = quality_metrics["class_distribution"].get(1, 0) / max(quality_metrics["total_bboxes"], 1)
    if drowning_rate < 0.15:
        report_content += "- Consider if more images should be labeled as 'drowning'\n"
    elif drowning_rate > 0.40:
        report_content += "- Review drowning class assignments for accuracy\n"
    
    report_content += """
### Next Steps:
1. Continue annotation following guidelines
2. Regular quality checks every 50 images
3. Peer review for challenging cases
4. Prepare for scaling to full dataset

## 📁 Files and Progress

### Completed Files:
"""
    
    completed_files = [
        img for img in metadata.get("images", []) 
        if img.get("annotated", False)
    ]
    
    # Show first 10 completed files
    for i, img_info in enumerate(completed_files[:10]):
        report_content += f"- {img_info['filename']}\n"
    
    if len(completed_files) > 10:
        report_content += f"- ... and {len(completed_files) - 10} more completed files\n"
    
    # Show remaining files
    remaining_files = [
        img for img in metadata.get("images", []) 
        if not img.get("annotated", False)
    ]
    
    if remaining_files:
        report_content += "\n### Remaining Files:\n"
        for i, img_info in enumerate(remaining_files[:5]):
            report_content += f"- {img_info['filename']}\n"
        
        if len(remaining_files) > 5:
            report_content += f"- ... and {len(remaining_files) - 5} more remaining files\n"
    
    report_content += f"""
---

**Last Updated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Report Generated By:** Progress Tracker v1.0
"""
    
    # Save report
    with open(report_file, 'w') as f:
        f.write(report_content)
    
    print(f"✅ Progress report saved: {report_file}")
    return report_file

def display_live_progress():
    """Display live progress in terminal"""
    metadata = update_progress_tracking()
    progress = metadata["annotation_progress"]
    
    print(f"\n📊 Live Progress Status")
    print("=" * 50)
    
    # Progress bar
    completion_rate = progress.get('completion_rate', 0)
    bar_length = 30
    filled_length = int(bar_length * completion_rate // 100)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    
    print(f"Progress: |{bar}| {completion_rate:.1f}%")
    print(f"Completed: {progress['completed']}/{progress['total']} images")
    print(f"Remaining: {progress['total'] - progress['completed']} images")
    
    # Quality summary
    quality_metrics = analyze_annotation_quality()
    if "error" not in quality_metrics:
        total_bboxes = quality_metrics["total_bboxes"]
        swimming_count = quality_metrics["class_distribution"].get(0, 0)
        drowning_count = quality_metrics["class_distribution"].get(1, 0)
        
        print(f"\nAnnotation Summary:")
        print(f"  Total bounding boxes: {total_bboxes}")
        print(f"  Swimming: {swimming_count} ({swimming_count/max(total_bboxes,1)*100:.1f}%)")
        print(f"  Drowning: {drowning_count} ({drowning_count/max(total_bboxes,1)*100:.1f}%)")
        print(f"  Avg people/image: {quality_metrics['average_people_per_image']:.1f}")
    
    # Time estimation
    time_estimation = estimate_completion_time(metadata)
    if "error" not in time_estimation:
        print(f"\nTime Estimation:")
        print(f"  Remaining: {time_estimation['estimated_time_remaining']['formatted']}")
        print(f"  Est. completion: {time_estimation['estimated_completion_date']}")

def main():
    """Main progress tracking function"""
    parser = argparse.ArgumentParser(description="Track annotation progress")
    parser.add_argument("--live", action="store_true", help="Show live progress")
    parser.add_argument("--report", action="store_true", help="Generate full report")
    parser.add_argument("--update", action="store_true", help="Update progress only")
    
    args = parser.parse_args()
    
    print("📈 Swimming Pool Drowning Detection - Progress Tracker")
    print("=" * 55)
    
    if args.live:
        display_live_progress()
    elif args.report:
        report_file = generate_progress_report()
        print(f"\n📄 Full report generated: {report_file}")
    elif args.update:
        metadata = update_progress_tracking()
        print(f"✅ Progress updated")
        print(f"  Completed: {metadata['annotation_progress']['completed']}")
        print(f"  Rate: {metadata['annotation_progress']['completion_rate']:.1f}%")
    else:
        # Default: show live progress
        display_live_progress()
        
        print(f"\n💡 Commands:")
        print("  python progress_tracker.py --live     # Live status")
        print("  python progress_tracker.py --report   # Full report")
        print("  python progress_tracker.py --update   # Update only")

if __name__ == "__main__":
    main()