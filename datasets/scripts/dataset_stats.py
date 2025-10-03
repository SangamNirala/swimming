#!/usr/bin/env python3
"""
Dataset Statistics Script

Generates comprehensive statistics about the organized dataset.

Usage:
    python dataset_stats.py
    python dataset_stats.py --dataset-dir ..
"""

import os
import sys
import argparse
from pathlib import Path
from collections import defaultdict
import json

try:
    from PIL import Image
    import numpy as np
except ImportError as e:
    print(f"Error: Required package not installed: {e}")
    print("Install with: pip install pillow numpy")
    sys.exit(1)


class DatasetStatistics:
    """
    Analyzes and reports dataset statistics.
    """
    
    def __init__(self, dataset_dir):
        self.dataset_dir = Path(dataset_dir)
        self.stats = defaultdict(lambda: defaultdict(int))
        self.image_sizes = defaultdict(list)
        self.file_sizes = defaultdict(list)
    
    def analyze_split(self, split_name):
        """
        Analyze a single split (train/val/test).
        """
        split_dir = self.dataset_dir / split_name
        
        if not split_dir.exists():
            return
        
        for class_name in ['swimming', 'drowning']:
            class_dir = split_dir / class_name
            
            if not class_dir.exists():
                continue
            
            # Count files
            image_files = list(class_dir.glob('*.jpg')) + \
                         list(class_dir.glob('*.jpeg')) + \
                         list(class_dir.glob('*.png'))
            
            annotation_files = list(class_dir.glob('*.txt'))
            
            self.stats[split_name][f'{class_name}_images'] = len(image_files)
            self.stats[split_name][f'{class_name}_annotations'] = len(annotation_files)
            
            # Analyze image properties
            for img_path in image_files[:100]:  # Sample first 100 for speed
                try:
                    img = Image.open(img_path)
                    self.image_sizes[split_name].append(img.size)
                    self.file_sizes[split_name].append(os.path.getsize(img_path))
                except:
                    pass
    
    def calculate_statistics(self):
        """
        Calculate overall statistics.
        """
        print("Analyzing dataset...\n")
        
        for split in ['train', 'val', 'test']:
            self.analyze_split(split)
        
        return self.generate_report()
    
    def generate_report(self):
        """
        Generate comprehensive statistics report.
        """
        report = {
            'splits': {},
            'totals': {
                'swimming': 0,
                'drowning': 0,
                'total': 0
            },
            'class_distribution': {},
            'image_properties': {}
        }
        
        # Per-split statistics
        for split_name, split_stats in self.stats.items():
            swimming = split_stats.get('swimming_images', 0)
            drowning = split_stats.get('drowning_images', 0)
            total = swimming + drowning
            
            report['splits'][split_name] = {
                'swimming': swimming,
                'drowning': drowning,
                'total': total,
                'annotations': split_stats.get('swimming_annotations', 0) + \
                              split_stats.get('drowning_annotations', 0)
            }
            
            # Update totals
            report['totals']['swimming'] += swimming
            report['totals']['drowning'] += drowning
            report['totals']['total'] += total
        
        # Class distribution
        total_images = report['totals']['total']
        if total_images > 0:
            report['class_distribution'] = {
                'swimming': f"{report['totals']['swimming'] / total_images * 100:.1f}%",
                'drowning': f"{report['totals']['drowning'] / total_images * 100:.1f}%"
            }
        
        # Image properties (from samples)
        for split_name, sizes in self.image_sizes.items():
            if sizes:
                widths = [s[0] for s in sizes]
                heights = [s[1] for s in sizes]
                
                report['image_properties'][split_name] = {
                    'avg_width': int(np.mean(widths)),
                    'avg_height': int(np.mean(heights)),
                    'min_width': min(widths),
                    'max_width': max(widths),
                    'min_height': min(heights),
                    'max_height': max(heights)
                }
        
        return report
    
    def print_report(self, report):
        """
        Print formatted report to console.
        """
        print("="*70)
        print("DATASET STATISTICS REPORT")
        print("="*70)
        
        # Overall statistics
        print("\n📊 OVERALL STATISTICS")
        print("-" * 70)
        print(f"Total Images: {report['totals']['total']}")
        print(f"  - Swimming: {report['totals']['swimming']}")
        print(f"  - Drowning: {report['totals']['drowning']}")
        
        # Class distribution
        if report['class_distribution']:
            print(f"\n📈 CLASS DISTRIBUTION")
            print("-" * 70)
            print(f"Swimming: {report['class_distribution']['swimming']}")
            print(f"Drowning: {report['class_distribution']['drowning']}")
        
        # Per-split statistics
        print(f"\n📁 SPLIT STATISTICS")
        print("-" * 70)
        print(f"{'Split':<10} {'Swimming':<12} {'Drowning':<12} {'Total':<10} {'Annotations':<12}")
        print("-" * 70)
        
        for split_name, split_data in report['splits'].items():
            print(f"{split_name.capitalize():<10} "
                  f"{split_data['swimming']:<12} "
                  f"{split_data['drowning']:<12} "
                  f"{split_data['total']:<10} "
                  f"{split_data['annotations']:<12}")
        
        # Image properties
        if report['image_properties']:
            print(f"\n🖼️  IMAGE PROPERTIES (sampled)")
            print("-" * 70)
            
            for split_name, props in report['image_properties'].items():
                print(f"\n{split_name.capitalize()}:")
                print(f"  Average size: {props['avg_width']}×{props['avg_height']}")
                print(f"  Width range: {props['min_width']} - {props['max_width']}")
                print(f"  Height range: {props['min_height']} - {props['max_height']}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        print("-" * 70)
        
        total = report['totals']['total']
        swimming = report['totals']['swimming']
        drowning = report['totals']['drowning']
        
        if total < 1000:
            print("⚠️  Dataset is small (<1000 images). Consider:")
            print("   - Downloading more datasets")
            print("   - Using heavy data augmentation")
            print("   - Transfer learning from pretrained models")
        
        if drowning < swimming * 0.5:
            print("⚠️  Drowning class is underrepresented. Consider:")
            print("   - Collecting more drowning examples")
            print("   - Using class weights during training")
            print("   - Augmenting drowning class more heavily")
        
        if total >= 2000 and abs(swimming - drowning) < total * 0.2:
            print("✓ Dataset size and balance look good!")
        
        print("\n" + "="*70)
    
    def save_report(self, report, filename='dataset_statistics.json'):
        """
        Save report to JSON file.
        """
        output_path = self.dataset_dir / filename
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n✓ Report saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate dataset statistics"
    )
    parser.add_argument(
        "--dataset-dir",
        type=str,
        default="..",
        help="Dataset directory path"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save report to JSON file"
    )
    
    args = parser.parse_args()
    
    # Check if dataset directory exists
    dataset_dir = Path(args.dataset_dir)
    if not dataset_dir.exists():
        print(f"Error: Dataset directory not found: {dataset_dir}")
        sys.exit(1)
    
    # Create statistics analyzer
    analyzer = DatasetStatistics(dataset_dir)
    
    # Calculate and display statistics
    report = analyzer.calculate_statistics()
    analyzer.print_report(report)
    
    # Save if requested
    if args.save:
        analyzer.save_report(report)


if __name__ == "__main__":
    main()
