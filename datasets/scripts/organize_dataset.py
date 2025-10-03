#!/usr/bin/env python3
"""
Dataset Organization Script

Organizes downloaded datasets into train/val/test splits with proper structure.

Usage:
    python organize_dataset.py
    python organize_dataset.py --split 0.7 0.15 0.15
    python organize_dataset.py --source ../raw --output ..
"""

import os
import sys
import shutil
import argparse
import random
from pathlib import Path
from collections import defaultdict
import json

try:
    import cv2
    from PIL import Image
    from tqdm import tqdm
except ImportError as e:
    print(f"Error: Required package not installed: {e}")
    print("Install with: pip install opencv-python pillow tqdm")
    sys.exit(1)


class DatasetOrganizer:
    """
    Organizes multiple datasets into unified train/val/test structure.
    """
    
    def __init__(self, source_dir, output_dir, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        
        # Statistics
        self.stats = {
            'total_images': 0,
            'swimming': 0,
            'drowning': 0,
            'train': 0,
            'val': 0,
            'test': 0,
            'duplicates_removed': 0,
            'invalid_removed': 0
        }
        
        # Track processed files to avoid duplicates
        self.processed_hashes = set()
    
    def get_image_hash(self, image_path):
        """Generate hash for image to detect duplicates."""
        try:
            with open(image_path, 'rb') as f:
                import hashlib
                return hashlib.md5(f.read()).hexdigest()
        except:
            return None
    
    def is_valid_image(self, image_path):
        """Check if image is valid and readable."""
        try:
            img = Image.open(image_path)
            img.verify()
            
            # Check minimum size
            if img.size[0] < 320 or img.size[1] < 240:
                return False
            
            return True
        except:
            return False
    
    def classify_image(self, image_path, annotation_path=None):
        """
        Determine if image belongs to 'swimming' or 'drowning' class.
        
        Logic:
        - Check directory name
        - Check filename
        - Check annotation if available
        - Default to 'swimming' if unclear
        """
        path_lower = str(image_path).lower()
        
        # Check directory and filename for keywords
        drowning_keywords = ['drown', 'sink', 'distress', 'emergency', 'alert']
        swimming_keywords = ['swim', 'normal', 'safe', 'float']
        
        for keyword in drowning_keywords:
            if keyword in path_lower:
                return 'drowning'
        
        for keyword in swimming_keywords:
            if keyword in path_lower:
                return 'swimming'
        
        # If annotation exists, try to parse it
        if annotation_path and os.path.exists(annotation_path):
            try:
                with open(annotation_path, 'r') as f:
                    content = f.read().lower()
                    if 'drown' in content:
                        return 'drowning'
            except:
                pass
        
        # Default to swimming (can be manually corrected later)
        return 'swimming'
    
    def collect_images(self):
        """
        Collect all images from source directory.
        """
        print("Collecting images from source directory...")
        
        images_by_class = {'swimming': [], 'drowning': []}
        
        # Supported image extensions
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        
        # Walk through source directory
        for root, dirs, files in os.walk(self.source_dir):
            for file in files:
                ext = Path(file).suffix.lower()
                if ext not in image_extensions:
                    continue
                
                image_path = Path(root) / file
                
                # Check for duplicates
                img_hash = self.get_image_hash(image_path)
                if img_hash in self.processed_hashes:
                    self.stats['duplicates_removed'] += 1
                    continue
                
                # Validate image
                if not self.is_valid_image(image_path):
                    self.stats['invalid_removed'] += 1
                    continue
                
                # Classify image
                annotation_path = image_path.with_suffix('.txt')
                class_label = self.classify_image(image_path, annotation_path)
                
                # Add to collection
                images_by_class[class_label].append({
                    'image': image_path,
                    'annotation': annotation_path if annotation_path.exists() else None
                })
                
                self.processed_hashes.add(img_hash)
                self.stats['total_images'] += 1
        
        self.stats['swimming'] = len(images_by_class['swimming'])
        self.stats['drowning'] = len(images_by_class['drowning'])
        
        print(f"✓ Collected {self.stats['total_images']} valid images")
        print(f"  - Swimming: {self.stats['swimming']}")
        print(f"  - Drowning: {self.stats['drowning']}")
        print(f"  - Duplicates removed: {self.stats['duplicates_removed']}")
        print(f"  - Invalid removed: {self.stats['invalid_removed']}")
        
        return images_by_class
    
    def split_data(self, images_by_class):
        """
        Split data into train/val/test sets.
        """
        print(f"\nSplitting data ({self.train_ratio}/{self.val_ratio}/{self.test_ratio})...")
        
        splits = {'train': {}, 'val': {}, 'test': {}}
        
        for class_label, images in images_by_class.items():
            # Shuffle
            random.shuffle(images)
            
            # Calculate split indices
            n = len(images)
            train_end = int(n * self.train_ratio)
            val_end = train_end + int(n * self.val_ratio)
            
            # Split
            splits['train'][class_label] = images[:train_end]
            splits['val'][class_label] = images[train_end:val_end]
            splits['test'][class_label] = images[val_end:]
            
            print(f"  {class_label}:")
            print(f"    - Train: {len(splits['train'][class_label])}")
            print(f"    - Val: {len(splits['val'][class_label])}")
            print(f"    - Test: {len(splits['test'][class_label])}")
        
        return splits
    
    def copy_files(self, splits):
        """
        Copy files to output directory structure.
        """
        print("\nCopying files to organized structure...")
        
        for split_name, classes in splits.items():
            for class_label, images in classes.items():
                # Create output directory
                output_dir = self.output_dir / split_name / class_label
                output_dir.mkdir(parents=True, exist_ok=True)
                
                # Copy files
                for i, item in enumerate(tqdm(images, desc=f"{split_name}/{class_label}")):
                    # Generate unique filename
                    base_name = f"{class_label}_{split_name}_{i:05d}"
                    
                    # Copy image
                    image_ext = item['image'].suffix
                    dest_image = output_dir / f"{base_name}{image_ext}"
                    shutil.copy2(item['image'], dest_image)
                    
                    # Copy annotation if exists
                    if item['annotation']:
                        dest_annotation = output_dir / f"{base_name}.txt"
                        shutil.copy2(item['annotation'], dest_annotation)
                    
                    # Update statistics
                    self.stats[split_name] += 1
        
        print("✓ Files copied successfully")
    
    def generate_report(self):
        """
        Generate organization report.
        """
        report_path = self.output_dir / 'organization_report.json'
        
        report = {
            'statistics': self.stats,
            'split_ratios': {
                'train': self.train_ratio,
                'val': self.val_ratio,
                'test': self.test_ratio
            },
            'directory_structure': {
                'train': {
                    'swimming': len(list((self.output_dir / 'train' / 'swimming').glob('*'))),
                    'drowning': len(list((self.output_dir / 'train' / 'drowning').glob('*')))
                },
                'val': {
                    'swimming': len(list((self.output_dir / 'val' / 'swimming').glob('*'))),
                    'drowning': len(list((self.output_dir / 'val' / 'drowning').glob('*')))
                },
                'test': {
                    'swimming': len(list((self.output_dir / 'test' / 'swimming').glob('*'))),
                    'drowning': len(list((self.output_dir / 'test' / 'drowning').glob('*')))
                }
            }
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n✓ Report saved to: {report_path}")
        
        return report
    
    def organize(self):
        """
        Main organization workflow.
        """
        print("="*60)
        print("Dataset Organization")
        print("="*60)
        print(f"Source: {self.source_dir}")
        print(f"Output: {self.output_dir}")
        print(f"Split: {self.train_ratio}/{self.val_ratio}/{self.test_ratio}")
        print("="*60 + "\n")
        
        # Collect images
        images_by_class = self.collect_images()
        
        if self.stats['total_images'] == 0:
            print("\n✗ No valid images found!")
            return
        
        # Split data
        splits = self.split_data(images_by_class)
        
        # Copy files
        self.copy_files(splits)
        
        # Generate report
        report = self.generate_report()
        
        # Summary
        print("\n" + "="*60)
        print("ORGANIZATION COMPLETE")
        print("="*60)
        print(f"Total images organized: {self.stats['total_images']}")
        print(f"  - Train: {self.stats['train']}")
        print(f"  - Val: {self.stats['val']}")
        print(f"  - Test: {self.stats['test']}")
        print(f"\nClass distribution:")
        print(f"  - Swimming: {self.stats['swimming']}")
        print(f"  - Drowning: {self.stats['drowning']}")
        print(f"\nOutput directory: {self.output_dir}")
        print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description="Organize datasets into train/val/test structure"
    )
    parser.add_argument(
        "--source",
        type=str,
        default="../raw",
        help="Source directory containing raw datasets"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="..",
        help="Output directory for organized dataset"
    )
    parser.add_argument(
        "--split",
        type=float,
        nargs=3,
        default=[0.7, 0.15, 0.15],
        metavar=('TRAIN', 'VAL', 'TEST'),
        help="Split ratios (default: 0.7 0.15 0.15)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    
    args = parser.parse_args()
    
    # Validate split ratios
    if abs(sum(args.split) - 1.0) > 0.01:
        print("Error: Split ratios must sum to 1.0")
        sys.exit(1)
    
    # Set random seed
    random.seed(args.seed)
    
    # Create organizer and run
    organizer = DatasetOrganizer(
        source_dir=args.source,
        output_dir=args.output,
        train_ratio=args.split[0],
        val_ratio=args.split[1],
        test_ratio=args.split[2]
    )
    
    organizer.organize()


if __name__ == "__main__":
    main()
