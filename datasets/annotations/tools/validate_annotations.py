#!/usr/bin/env python3
"""
Annotation Validation and Quality Control
Validates YOLO format annotations and performs quality control checks
"""

import os
import json
import numpy as np
from pathlib import Path
from collections import defaultdict, Counter
import argparse
import time
from typing import Dict, List, Tuple

def validate_yolo_format(annotation_file: Path) -> Dict:
    """Validate a single YOLO annotation file"""
    validation_result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "bbox_count": 0,
        "class_distribution": Counter()
    }
    
    try:
        with open(annotation_file, 'r') as f:
            lines = f.readlines()
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            parts = line.split()
            
            # Check format: class_id center_x center_y width height
            if len(parts) != 5:
                validation_result["errors"].append(
                    f"Line {line_num}: Expected 5 values, got {len(parts)}"
                )
                validation_result["valid"] = False
                continue
            
            try:
                class_id = int(parts[0])
                center_x = float(parts[1])
                center_y = float(parts[2])
                width = float(parts[3])
                height = float(parts[4])
                
                # Validate class ID (0=swimming, 1=drowning)
                if class_id not in [0, 1]:
                    validation_result["errors"].append(
                        f"Line {line_num}: Invalid class ID {class_id} (must be 0 or 1)"
                    )
                    validation_result["valid"] = False
                
                # Validate coordinate ranges (0.0 to 1.0)
                coords = [center_x, center_y, width, height]
                coord_names = ["center_x", "center_y", "width", "height"]
                
                for coord, name in zip(coords, coord_names):
                    if not (0.0 <= coord <= 1.0):
                        validation_result["errors"].append(
                            f"Line {line_num}: {name}={coord:.3f} out of range [0.0, 1.0]"
                        )
                        validation_result["valid"] = False
                
                # Check for reasonable bounding box dimensions
                if width < 0.005:  # Very small width
                    validation_result["warnings"].append(
                        f"Line {line_num}: Very small width {width:.3f}"
                    )
                
                if height < 0.005:  # Very small height
                    validation_result["warnings"].append(
                        f"Line {line_num}: Very small height {height:.3f}"
                    )
                
                if width > 0.8 or height > 0.8:  # Very large bbox
                    validation_result["warnings"].append(
                        f"Line {line_num}: Very large bbox ({width:.3f}, {height:.3f})"
                    )
                
                # Check if bbox extends outside image boundaries
                x1 = center_x - width/2
                y1 = center_y - height/2
                x2 = center_x + width/2
                y2 = center_y + height/2
                
                if x1 < 0 or y1 < 0 or x2 > 1 or y2 > 1:
                    validation_result["warnings"].append(
                        f"Line {line_num}: Bbox may extend outside image boundaries"
                    )
                
                # Update statistics
                validation_result["bbox_count"] += 1
                validation_result["class_distribution"][class_id] += 1
                
            except ValueError as e:
                validation_result["errors"].append(
                    f"Line {line_num}: Could not parse numbers - {e}"
                )
                validation_result["valid"] = False
    
    except Exception as e:
        validation_result["errors"].append(f"Could not read file: {e}")
        validation_result["valid"] = False
    
    return validation_result

def validate_pilot_batch():
    """Validate all annotations in pilot batch"""
    print("🔍 Validating pilot batch annotations...")
    
    pilot_dir = Path("/app/datasets/annotations/pilot_batch")
    images_dir = pilot_dir / "images"
    annotations_dir = pilot_dir / "annotations"
    
    if not images_dir.exists():
        print("❌ Images directory not found")
        return None
    
    if not annotations_dir.exists():
        print("❌ Annotations directory not found")
        return None
    
    # Get all image and annotation files
    image_files = {f.stem for f in images_dir.glob("*.jpg")}
    annotation_files = {f.stem for f in annotations_dir.glob("*.txt")}
    
    validation_summary = {
        "total_images": len(image_files),
        "total_annotations": len(annotation_files),
        "missing_annotations": len(image_files - annotation_files),
        "orphaned_annotations": len(annotation_files - image_files),
        "valid_files": 0,
        "invalid_files": 0,
        "total_bboxes": 0,
        "total_errors": 0,
        "total_warnings": 0,
        "class_distribution": Counter(),
        "file_results": {}
    }
    
    # Validate each annotation file
    for annotation_file in annotations_dir.glob("*.txt"):
        result = validate_yolo_format(annotation_file)
        
        filename = annotation_file.name
        validation_summary["file_results"][filename] = result
        
        if result["valid"]:
            validation_summary["valid_files"] += 1
        else:
            validation_summary["invalid_files"] += 1
        
        validation_summary["total_bboxes"] += result["bbox_count"]
        validation_summary["total_errors"] += len(result["errors"])
        validation_summary["total_warnings"] += len(result["warnings"])
        validation_summary["class_distribution"] += result["class_distribution"]
    
    return validation_summary

def generate_quality_report(validation_summary: Dict):
    """Generate comprehensive quality report"""
    print("\n📊 Generating quality report...")
    
    pilot_dir = Path("/app/datasets/annotations/pilot_batch")
    report_dir = pilot_dir.parent / "quality_control" / "validation_reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_file = report_dir / f"validation_report_{timestamp}.md"
    
    # Calculate quality metrics
    total_files = validation_summary["total_annotations"]
    valid_files = validation_summary["valid_files"]
    error_rate = validation_summary["total_errors"] / max(total_files, 1)
    
    swimming_count = validation_summary["class_distribution"][0]
    drowning_count = validation_summary["class_distribution"][1]
    total_bboxes = validation_summary["total_bboxes"]
    
    class_balance = drowning_count / max(total_bboxes, 1) if total_bboxes > 0 else 0
    
    # Generate report content
    report_content = f"""# Annotation Validation Report

**Generated:** {time.strftime("%Y-%m-%d %H:%M:%S")}  
**Dataset:** Pilot Batch Annotations  
**Validator:** YOLO Format Validation Script

## 📊 Summary Statistics

| Metric | Value |
|--------|-------|
| Total Images | {validation_summary['total_images']} |
| Total Annotation Files | {validation_summary['total_annotations']} |
| Valid Files | {valid_files} |
| Invalid Files | {validation_summary['invalid_files']} |
| Missing Annotations | {validation_summary['missing_annotations']} |
| Orphaned Annotations | {validation_summary['orphaned_annotations']} |

## 📏 Annotation Quality

| Metric | Value |
|--------|-------|
| Total Bounding Boxes | {total_bboxes} |
| Total Errors | {validation_summary['total_errors']} |
| Total Warnings | {validation_summary['total_warnings']} |
| Error Rate | {error_rate:.3f} errors per file |
| Validation Success Rate | {valid_files/max(total_files,1)*100:.1f}% |

## 🏷️ Class Distribution

| Class | Count | Percentage |
|-------|-------|-----------|
| Swimming (0) | {swimming_count} | {swimming_count/max(total_bboxes,1)*100:.1f}% |
| Drowning (1) | {drowning_count} | {drowning_count/max(total_bboxes,1)*100:.1f}% |
| **Total** | **{total_bboxes}** | **100.0%** |

**Class Balance Ratio:** {class_balance:.3f} (drowning/total)

## ✅ Quality Assessment

"""
    
    # Quality thresholds
    quality_checks = []
    
    # File validation rate
    file_validation_rate = valid_files / max(total_files, 1)
    if file_validation_rate >= 0.95:
        quality_checks.append("✅ **File Validation Rate:** EXCELLENT (≥95%)")
    elif file_validation_rate >= 0.90:
        quality_checks.append("⚠️ **File Validation Rate:** GOOD (≥90%)")
    else:
        quality_checks.append("❌ **File Validation Rate:** NEEDS IMPROVEMENT (<90%)")
    
    # Error rate
    if error_rate <= 0.05:
        quality_checks.append("✅ **Error Rate:** EXCELLENT (≤0.05 errors/file)")
    elif error_rate <= 0.10:
        quality_checks.append("⚠️ **Error Rate:** ACCEPTABLE (≤0.10 errors/file)")
    else:
        quality_checks.append("❌ **Error Rate:** HIGH (>0.10 errors/file)")
    
    # Missing annotations
    missing_rate = validation_summary['missing_annotations'] / max(validation_summary['total_images'], 1)
    if missing_rate == 0:
        quality_checks.append("✅ **Completeness:** PERFECT (no missing annotations)")
    elif missing_rate <= 0.05:
        quality_checks.append("⚠️ **Completeness:** GOOD (≤5% missing)")
    else:
        quality_checks.append("❌ **Completeness:** INCOMPLETE (>5% missing)")
    
    # Class balance
    if 0.15 <= class_balance <= 0.40:  # Reasonable balance for drowning detection
        quality_checks.append("✅ **Class Balance:** GOOD (15-40% drowning)")
    elif 0.05 <= class_balance < 0.15:
        quality_checks.append("⚠️ **Class Balance:** LOW drowning representation")
    else:
        quality_checks.append("❌ **Class Balance:** NEEDS REVIEW")
    
    report_content += "\n".join(quality_checks)
    
    # Add detailed error analysis if errors exist
    if validation_summary["total_errors"] > 0:
        report_content += "\n\n## ❌ Detailed Error Analysis\n\n"
        
        error_files = []
        for filename, result in validation_summary["file_results"].items():
            if not result["valid"]:
                error_files.append((filename, result))
        
        # Show first 10 files with errors
        for filename, result in error_files[:10]:
            report_content += f"### {filename}\n"
            for error in result["errors"]:
                report_content += f"- ❌ {error}\n"
            report_content += "\n"
        
        if len(error_files) > 10:
            report_content += f"*... and {len(error_files) - 10} more files with errors*\n\n"
    
    # Add recommendations
    report_content += """
## 💡 Recommendations

### High Priority Actions:
"""
    
    if validation_summary["invalid_files"] > 0:
        report_content += f"- Fix {validation_summary['invalid_files']} files with format errors\n"
    
    if validation_summary["missing_annotations"] > 0:
        report_content += f"- Create annotations for {validation_summary['missing_annotations']} missing files\n"
    
    if error_rate > 0.10:
        report_content += "- Review annotation guidelines with team\n"
        report_content += "- Implement additional quality control measures\n"
    
    if class_balance < 0.10:
        report_content += "- Review class assignments - may need more drowning annotations\n"
    elif class_balance > 0.50:
        report_content += "- Review class assignments - may be over-labeling drowning\n"
    
    report_content += """
### General Recommendations:
- Regular quality checks every 50-100 annotations
- Peer review for difficult cases
- Consistent annotation standards
- Double-check class assignments based on behavior

### Next Steps:
1. Address high priority issues above
2. Continue with manual annotation correction
3. Implement peer review process
4. Schedule regular quality assessments
"""
    
    # Save report
    with open(report_file, 'w') as f:
        f.write(report_content)
    
    print(f"✅ Quality report saved: {report_file}")
    return report_file

def check_annotation_progress():
    """Check annotation progress and completeness"""
    print("\n📈 Checking annotation progress...")
    
    pilot_dir = Path("/app/datasets/annotations/pilot_batch")
    
    # Load metadata if available
    metadata_file = pilot_dir / "pilot_metadata.json"
    metadata = {}
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
    
    # Count files
    images_dir = pilot_dir / "images"
    annotations_dir = pilot_dir / "annotations"
    
    total_images = len(list(images_dir.glob("*.jpg"))) if images_dir.exists() else 0
    total_annotations = len(list(annotations_dir.glob("*.txt"))) if annotations_dir.exists() else 0
    
    # Calculate progress
    completion_rate = total_annotations / max(total_images, 1) * 100
    
    progress_report = {
        "total_images": total_images,
        "total_annotations": total_annotations,
        "completion_rate": completion_rate,
        "remaining": total_images - total_annotations
    }
    
    print(f"📊 Progress Report:")
    print(f"  Total images: {total_images}")
    print(f"  Completed annotations: {total_annotations}")
    print(f"  Completion rate: {completion_rate:.1f}%")
    print(f"  Remaining: {progress_report['remaining']}")
    
    # Update metadata if it exists
    if metadata and "annotation_progress" in metadata:
        metadata["annotation_progress"]["completed"] = total_annotations
        metadata["annotation_progress"]["completion_rate"] = completion_rate
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Progress updated in metadata file")
    
    return progress_report

def main():
    """Main validation function"""
    parser = argparse.ArgumentParser(description="Validate YOLO annotations")
    parser.add_argument("--report-only", action="store_true", 
                       help="Generate report from existing validation data")
    parser.add_argument("--progress-only", action="store_true",
                       help="Check progress only")
    
    args = parser.parse_args()
    
    print("🔍 Swimming Pool Drowning Detection - Annotation Validation")
    print("=" * 65)
    
    if args.progress_only:
        progress = check_annotation_progress()
        return
    
    # Validate annotations
    validation_summary = validate_pilot_batch()
    
    if validation_summary is None:
        print("❌ Validation failed - check directories")
        return
    
    # Save validation results
    pilot_dir = Path("/app/datasets/annotations/pilot_batch")
    results_file = pilot_dir / "validation_results.json"
    
    with open(results_file, 'w') as f:
        # Convert Counter objects to dict for JSON serialization
        summary_for_json = validation_summary.copy()
        summary_for_json["class_distribution"] = dict(summary_for_json["class_distribution"])
        
        json.dump(summary_for_json, f, indent=2, default=str)
    
    print(f"💾 Validation results saved: {results_file}")
    
    # Generate quality report
    report_file = generate_quality_report(validation_summary)
    
    # Check progress
    progress = check_annotation_progress()
    
    # Summary
    print("\n" + "=" * 65)
    print("📊 Validation Summary:")
    print(f"  Valid files: {validation_summary['valid_files']}/{validation_summary['total_annotations']}")
    print(f"  Total errors: {validation_summary['total_errors']}")
    print(f"  Total warnings: {validation_summary['total_warnings']}")
    print(f"  Completion: {progress['completion_rate']:.1f}%")
    
    if validation_summary['invalid_files'] == 0:
        print("\n✅ All annotation files are valid!")
    else:
        print(f"\n⚠️  {validation_summary['invalid_files']} files need attention")
    
    print(f"\n📄 Reports generated:")
    print(f"  Validation results: {results_file}")
    print(f"  Quality report: {report_file}")
    
    print(f"\n🎯 Next Steps:")
    if validation_summary['invalid_files'] > 0:
        print("1. Fix files with validation errors")
        print("2. Review quality report recommendations")
    if validation_summary['missing_annotations'] > 0:
        print("3. Complete missing annotations")
    print("4. Continue with annotation workflow")
    print("5. Regular quality checks every 50 annotations")

if __name__ == "__main__":
    main()