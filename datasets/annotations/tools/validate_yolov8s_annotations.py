#!/usr/bin/env python3
"""
Validate YOLOv8s Annotations
Check annotation quality and format compliance
"""

import os
import json
from pathlib import Path
import argparse
from datetime import datetime
from typing import Dict, List
import sys

def validate_yolo_format(annotation_path: Path) -> Dict:
    """
    Validate a single YOLO annotation file
    Returns dict with validation results
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "num_boxes": 0,
        "classes": set()
    }
    
    try:
        if not annotation_path.exists():
            result["valid"] = False
            result["errors"].append("File does not exist")
            return result
        
        with open(annotation_path, 'r') as f:
            lines = f.readlines()
        
        if not lines:
            result["warnings"].append("Empty annotation file")
            return result
        
        for line_num, line in enumerate(lines, 1):
            parts = line.strip().split()
            
            # Check format
            if len(parts) != 5:
                result["valid"] = False
                result["errors"].append(f"Line {line_num}: Invalid format (expected 5 values, got {len(parts)})")
                continue
            
            try:
                class_id = int(parts[0])
                center_x = float(parts[1])
                center_y = float(parts[2])
                width = float(parts[3])
                height = float(parts[4])
                
                # Validate class ID
                if class_id not in [0, 1]:
                    result["valid"] = False
                    result["errors"].append(f"Line {line_num}: Invalid class ID {class_id} (expected 0 or 1)")
                
                result["classes"].add(class_id)
                
                # Validate coordinates (should be normalized 0-1)
                for name, value in [("center_x", center_x), ("center_y", center_y), 
                                   ("width", width), ("height", height)]:
                    if value < 0.0 or value > 1.0:
                        result["valid"] = False
                        result["errors"].append(
                            f"Line {line_num}: {name}={value:.6f} out of range [0.0, 1.0]"
                        )
                
                # Check for zero or negative dimensions
                if width <= 0 or height <= 0:
                    result["valid"] = False
                    result["errors"].append(
                        f"Line {line_num}: Invalid dimensions (width={width}, height={height})"
                    )
                
                result["num_boxes"] += 1
                
            except ValueError as e:
                result["valid"] = False
                result["errors"].append(f"Line {line_num}: Cannot parse values - {e}")
        
        result["classes"] = sorted(list(result["classes"]))
        
    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"Error reading file: {e}")
    
    return result

def validate_annotations_directory(
    annotations_root: Path,
    output_file: Path = None
) -> Dict:
    """
    Validate all annotations in directory
    """
    print(f"\n🔍 Validating Annotations")
    print(f"📁 Directory: {annotations_root}")
    
    if not annotations_root.exists():
        print(f"❌ Directory not found: {annotations_root}")
        return None
    
    stats = {
        "validation_time": datetime.now().isoformat(),
        "annotations_root": str(annotations_root),
        "total_files": 0,
        "valid_files": 0,
        "invalid_files": 0,
        "empty_files": 0,
        "total_boxes": 0,
        "total_errors": 0,
        "total_warnings": 0,
        "class_distribution": {0: 0, 1: 0},
        "split_stats": {},
        "error_samples": [],
        "files_with_errors": []
    }
    
    # Find all annotation files
    annotation_files = list(annotations_root.rglob("*.txt"))
    stats["total_files"] = len(annotation_files)
    
    print(f"📊 Found {stats['total_files']} annotation files")
    
    if stats["total_files"] == 0:
        print("⚠️  No annotation files found!")
        return stats
    
    # Validate each file
    print("\n🔍 Validating files...")
    
    for idx, ann_file in enumerate(annotation_files, 1):
        if idx % 1000 == 0:
            print(f"   Progress: {idx}/{stats['total_files']} ({idx/stats['total_files']*100:.1f}%)")
        
        # Get split and class from path
        parts = ann_file.relative_to(annotations_root).parts
        if len(parts) >= 2:
            split = parts[0]
            class_name = parts[1]
            
            if split not in stats["split_stats"]:
                stats["split_stats"][split] = {
                    "total": 0,
                    "valid": 0,
                    "invalid": 0,
                    "empty": 0,
                    "total_boxes": 0,
                    "swimming": 0,
                    "drowning": 0
                }
            
            stats["split_stats"][split]["total"] += 1
        else:
            split = "unknown"
            class_name = "unknown"
        
        # Validate file
        result = validate_yolo_format(ann_file)
        
        if result["valid"]:
            stats["valid_files"] += 1
            if split != "unknown":
                stats["split_stats"][split]["valid"] += 1
        else:
            stats["invalid_files"] += 1
            if split != "unknown":
                stats["split_stats"][split]["invalid"] += 1
            
            # Store error sample
            if len(stats["error_samples"]) < 10:
                stats["error_samples"].append({
                    "file": str(ann_file.relative_to(annotations_root)),
                    "errors": result["errors"][:5]  # First 5 errors
                })
            
            stats["files_with_errors"].append(str(ann_file.relative_to(annotations_root)))
        
        if result["num_boxes"] == 0:
            stats["empty_files"] += 1
            if split != "unknown":
                stats["split_stats"][split]["empty"] += 1
        
        stats["total_boxes"] += result["num_boxes"]
        stats["total_errors"] += len(result["errors"])
        stats["total_warnings"] += len(result["warnings"])
        
        if split != "unknown":
            stats["split_stats"][split]["total_boxes"] += result["num_boxes"]
        
        # Count class distribution
        for class_id in result["classes"]:
            if class_id in stats["class_distribution"]:
                stats["class_distribution"][class_id] += result["num_boxes"]
    
    # Calculate percentages
    if stats["total_files"] > 0:
        stats["valid_percentage"] = (stats["valid_files"] / stats["total_files"]) * 100
        stats["empty_percentage"] = (stats["empty_files"] / stats["total_files"]) * 100
    
    if stats["valid_files"] > 0:
        stats["avg_boxes_per_file"] = stats["total_boxes"] / stats["valid_files"]
    
    # Save results
    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            # Convert sets to lists for JSON serialization
            json_stats = json.loads(json.dumps(stats, default=str))
            json.dump(json_stats, f, indent=2)
        print(f"\n💾 Validation results saved: {output_file}")
    
    # Print report
    print("\n" + "="*70)
    print("🔍 VALIDATION REPORT")
    print("="*70)
    
    print(f"\n📊 Overall Statistics:")
    print(f"   Total Files: {stats['total_files']:,}")
    print(f"   Valid Files: {stats['valid_files']:,} ({stats.get('valid_percentage', 0):.1f}%)")
    print(f"   Invalid Files: {stats['invalid_files']:,}")
    print(f"   Empty Files: {stats['empty_files']:,} ({stats.get('empty_percentage', 0):.1f}%)")
    print(f"   Total Bounding Boxes: {stats['total_boxes']:,}")
    print(f"   Avg Boxes per File: {stats.get('avg_boxes_per_file', 0):.2f}")
    
    print(f"\n🏊 Class Distribution:")
    total_class_boxes = sum(stats['class_distribution'].values())
    if total_class_boxes > 0:
        print(f"   Swimming (Class 0): {stats['class_distribution'][0]:,} ({stats['class_distribution'][0]/total_class_boxes*100:.1f}%)")
        print(f"   Drowning (Class 1): {stats['class_distribution'][1]:,} ({stats['class_distribution'][1]/total_class_boxes*100:.1f}%)")
    
    print(f"\n📈 Split Statistics:")
    for split, split_data in stats["split_stats"].items():
        print(f"   {split.capitalize()}:")
        print(f"      Total Files: {split_data['total']:,}")
        print(f"      Valid: {split_data['valid']:,}")
        print(f"      Empty: {split_data['empty']:,}")
        print(f"      Total Boxes: {split_data['total_boxes']:,}")
    
    if stats["total_errors"] > 0:
        print(f"\n❌ Errors Found:")
        print(f"   Total Errors: {stats['total_errors']:,}")
        print(f"   Files with Errors: {len(stats['files_with_errors']):,}")
        
        if stats["error_samples"]:
            print(f"\n   Sample Errors (first 3):")
            for sample in stats["error_samples"][:3]:
                print(f"      📄 {sample['file']}")
                for error in sample['errors'][:2]:
                    print(f"         • {error}")
    
    if stats["total_warnings"] > 0:
        print(f"\n⚠️  Warnings: {stats['total_warnings']:,}")
    
    print("\n" + "="*70)
    
    if stats["invalid_files"] == 0 and stats["total_errors"] == 0:
        print("✅ All annotations are valid!")
    elif stats["invalid_files"] > 0:
        print(f"⚠️  Found {stats['invalid_files']} invalid files. Check the report for details.")
    
    print("="*70)
    
    return stats

def main():
    parser = argparse.ArgumentParser(
        description="Validate YOLOv8s Annotations"
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
        default="/app/datasets/annotations/validation_report_yolov8s.json",
        help="Path to output validation report"
    )
    
    args = parser.parse_args()
    
    annotations_root = Path(args.annotations)
    output_file = Path(args.output)
    
    if not annotations_root.exists():
        print(f"❌ Annotations directory not found: {annotations_root}")
        sys.exit(1)
    
    stats = validate_annotations_directory(annotations_root, output_file)
    
    if stats and stats["invalid_files"] > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
