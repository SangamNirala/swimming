#!/usr/bin/env python3
"""
Dataset Verification Script

Verifies dataset quality and identifies issues.

Usage:
    python verify_dataset.py
    python verify_dataset.py --dataset-dir ..
"""

import os
import sys
import argparse
from pathlib import Path
from collections import defaultdict

try:
    from PIL import Image
    from tqdm import tqdm
except ImportError as e:
    print(f"Error: Required package not installed: {e}")
    print("Install with: pip install pillow tqdm")
    sys.exit(1)


class DatasetVerifier:
    """
    Verifies dataset quality and integrity.
    """
    
    def __init__(self, dataset_dir):
        self.dataset_dir = Path(dataset_dir)
        self.issues = defaultdict(list)
        self.stats = defaultdict(int)
    
    def verify_image(self, image_path):
        """
        Verify a single image.
        """
        try:
            # Try to open and verify
            img = Image.open(image_path)
            img.verify()
            
            # Re-open for size check (verify() closes file)
            img = Image.open(image_path)
            width, height = img.size
            
            # Check minimum resolution
            if width < 320 or height < 240:
                self.issues['low_resolution'].append((image_path, f"{width}x{height}"))
                return False
            
            # Check aspect ratio (should be reasonable)
            aspect_ratio = width / height
            if aspect_ratio < 0.5 or aspect_ratio > 3.0:
                self.issues['unusual_aspect_ratio'].append((image_path, f"{aspect_ratio:.2f}"))
            
            self.stats['valid_images'] += 1
            return True
            
        except Exception as e:
            self.issues['corrupted_images'].append((image_path, str(e)))
            self.stats['corrupted_images'] += 1
            return False
    
    def verify_annotation(self, annotation_path, image_path):
        """
        Verify YOLO format annotation.
        """
        try:
            with open(annotation_path, 'r') as f:
                lines = f.readlines()
            
            if not lines:
                self.issues['empty_annotations'].append(annotation_path)
                return False
            
            # Get image dimensions
            img = Image.open(image_path)
            img_width, img_height = img.size
            
            for line_num, line in enumerate(lines, 1):
                parts = line.strip().split()
                
                if len(parts) != 5:
                    self.issues['invalid_annotation_format'].append(
                        (annotation_path, f"Line {line_num}: Expected 5 values, got {len(parts)}")
                    )
                    continue
                
                try:
                    class_id, x_center, y_center, width, height = map(float, parts)
                    
                    # Check if values are in valid range [0, 1]
                    if not (0 <= x_center <= 1 and 0 <= y_center <= 1 and 
                           0 <= width <= 1 and 0 <= height <= 1):
                        self.issues['out_of_bounds'].append(
                            (annotation_path, f"Line {line_num}: Coordinates out of bounds")
                        )
                except ValueError:
                    self.issues['invalid_annotation_values'].append(
                        (annotation_path, f"Line {line_num}: Invalid numeric values")
                    )
            
            self.stats['valid_annotations'] += 1
            return True
            
        except Exception as e:
            self.issues['annotation_errors'].append((annotation_path, str(e)))
            return False
    
    def verify_split(self, split_name):
        """
        Verify a single split (train/val/test).
        """
        split_dir = self.dataset_dir / split_name
        
        if not split_dir.exists():
            self.issues['missing_splits'].append(split_name)
            return
        
        for class_name in ['swimming', 'drowning']:
            class_dir = split_dir / class_name
            
            if not class_dir.exists():
                self.issues['missing_classes'].append(f"{split_name}/{class_name}")
                continue
            
            # Get all images
            image_files = list(class_dir.glob('*.jpg')) + \
                         list(class_dir.glob('*.jpeg')) + \
                         list(class_dir.glob('*.png'))
            
            if not image_files:
                self.issues['empty_directories'].append(f"{split_name}/{class_name}")
            
            # Verify each image
            for img_path in tqdm(image_files, desc=f"Verifying {split_name}/{class_name}"):
                self.verify_image(img_path)
                
                # Check for annotation
                ann_path = img_path.with_suffix('.txt')
                if ann_path.exists():
                    self.verify_annotation(ann_path, img_path)
    
    def check_duplicates(self):
        """
        Check for duplicate images across splits.
        """
        print("\nChecking for duplicates across splits...")
        
        image_hashes = defaultdict(list)
        
        for split in ['train', 'val', 'test']:
            split_dir = self.dataset_dir / split
            if not split_dir.exists():
                continue
            
            for class_name in ['swimming', 'drowning']:
                class_dir = split_dir / class_name
                if not class_dir.exists():
                    continue
                
                image_files = list(class_dir.glob('*.jpg')) + \
                             list(class_dir.glob('*.jpeg')) + \
                             list(class_dir.glob('*.png'))
                
                for img_path in image_files:
                    try:
                        import hashlib
                        with open(img_path, 'rb') as f:
                            img_hash = hashlib.md5(f.read()).hexdigest()
                        image_hashes[img_hash].append(str(img_path))
                    except:
                        pass
        
        # Find duplicates
        for img_hash, paths in image_hashes.items():
            if len(paths) > 1:
                self.issues['duplicates'].append(paths)
        
        if self.issues['duplicates']:
            print(f"  Found {len(self.issues['duplicates'])} duplicate sets")
        else:
            print("  ✓ No duplicates found")
    
    def verify(self):
        """
        Run complete verification.
        """
        print("="*70)
        print("DATASET VERIFICATION")
        print("="*70)
        print(f"Dataset directory: {self.dataset_dir}\n")
        
        # Verify each split
        for split in ['train', 'val', 'test']:
            print(f"\nVerifying {split} split...")
            self.verify_split(split)
        
        # Check for duplicates
        self.check_duplicates()
        
        # Generate report
        self.print_report()
    
    def print_report(self):
        """
        Print verification report.
        """
        print("\n" + "="*70)
        print("VERIFICATION REPORT")
        print("="*70)
        
        # Summary
        print("\n📊 SUMMARY")
        print("-" * 70)
        print(f"Valid images: {self.stats['valid_images']}")
        print(f"Corrupted images: {self.stats['corrupted_images']}")
        print(f"Valid annotations: {self.stats['valid_annotations']}")
        
        # Issues
        total_issues = sum(len(v) for v in self.issues.values())
        
        if total_issues == 0:
            print("\n✓ No issues found! Dataset looks good.")
        else:
            print(f"\n⚠️  Found {total_issues} issue(s):\n")
            
            for issue_type, items in self.issues.items():
                if items:
                    print(f"\n{issue_type.replace('_', ' ').title()}: {len(items)}")
                    # Show first 5 examples
                    for item in items[:5]:
                        if isinstance(item, tuple):
                            print(f"  - {item[0]}: {item[1]}")
                        else:
                            print(f"  - {item}")
                    if len(items) > 5:
                        print(f"  ... and {len(items) - 5} more")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS")
        print("-" * 70)
        
        if self.issues['corrupted_images']:
            print("- Remove or replace corrupted images")
        
        if self.issues['low_resolution']:
            print("- Consider removing low-resolution images or upscaling")
        
        if self.issues['duplicates']:
            print("- Remove duplicate images to prevent data leakage")
        
        if self.issues['empty_annotations']:
            print("- Add annotations for images missing them")
        
        if total_issues == 0:
            print("✓ Dataset is ready for training!")
        
        print("\n" + "="*70)


def main():
    parser = argparse.ArgumentParser(
        description="Verify dataset quality and integrity"
    )
    parser.add_argument(
        "--dataset-dir",
        type=str,
        default="..",
        help="Dataset directory path"
    )
    
    args = parser.parse_args()
    
    # Check if dataset directory exists
    dataset_dir = Path(args.dataset_dir)
    if not dataset_dir.exists():
        print(f"Error: Dataset directory not found: {dataset_dir}")
        sys.exit(1)
    
    # Create verifier and run
    verifier = DatasetVerifier(dataset_dir)
    verifier.verify()


if __name__ == "__main__":
    main()
