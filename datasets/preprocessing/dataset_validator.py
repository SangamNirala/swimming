#!/usr/bin/env python3
"""
Dataset Validator Module
Validates train/val/test splits, checks data quality, generates statistics
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json
import logging
from collections import defaultdict
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatasetValidator:
    """
    Validate dataset structure, splits, and quality
    """
    
    def __init__(self, dataset_root: str):
        """
        Initialize validator
        
        Args:
            dataset_root: Root directory of dataset
        """
        self.dataset_root = Path(dataset_root)
        
    def validate_split_ratios(
        self,
        target_train: float = 0.70,
        target_val: float = 0.15,
        target_test: float = 0.15,
        tolerance: float = 0.02
    ) -> Dict:
        """
        Validate train/val/test split ratios
        
        Args:
            target_train: Target train ratio (default: 0.70)
            target_val: Target validation ratio (default: 0.15)
            target_test: Target test ratio (default: 0.15)
            tolerance: Acceptable deviation (default: 0.02)
            
        Returns:
            Dictionary with validation results
        """
        splits = ['train', 'val', 'test']
        classes = ['swimming', 'drowning']
        
        counts = defaultdict(lambda: defaultdict(int))
        
        # Count images in each split/class
        for split in splits:
            for class_name in classes:
                class_dir = self.dataset_root / split / class_name
                if class_dir.exists():
                    image_files = list(class_dir.glob("**/*.jpg"))
                    image_files.extend(class_dir.glob("**/*.png"))
                    counts[split][class_name] = len(image_files)
        
        # Calculate totals
        total_train = sum(counts['train'].values())
        total_val = sum(counts['val'].values())
        total_test = sum(counts['test'].values())
        total_all = total_train + total_val + total_test
        
        if total_all == 0:
            return {'valid': False, 'error': 'No images found'}
        
        # Calculate ratios
        actual_train = total_train / total_all
        actual_val = total_val / total_all
        actual_test = total_test / total_all
        
        # Check if within tolerance
        train_ok = abs(actual_train - target_train) <= tolerance
        val_ok = abs(actual_val - target_val) <= tolerance
        test_ok = abs(actual_test - target_test) <= tolerance
        
        all_ok = train_ok and val_ok and test_ok
        
        results = {
            'valid': all_ok,
            'counts': dict(counts),
            'totals': {
                'train': total_train,
                'val': total_val,
                'test': total_test,
                'total': total_all
            },
            'ratios': {
                'train': actual_train,
                'val': actual_val,
                'test': actual_test
            },
            'targets': {
                'train': target_train,
                'val': target_val,
                'test': target_test
            },
            'within_tolerance': {
                'train': train_ok,
                'val': val_ok,
                'test': test_ok
            }
        }
        
        return results
    
    def check_class_balance(self, split: str = 'train') -> Dict:
        """
        Check class balance within a split
        
        Args:
            split: Dataset split to check
            
        Returns:
            Dictionary with balance statistics
        """
        classes = ['swimming', 'drowning']
        counts = {}
        
        for class_name in classes:
            class_dir = self.dataset_root / split / class_name
            if class_dir.exists():
                image_files = list(class_dir.glob("**/*.jpg"))
                image_files.extend(class_dir.glob("**/*.png"))
                counts[class_name] = len(image_files)
            else:
                counts[class_name] = 0
        
        total = sum(counts.values())
        if total == 0:
            return {'valid': False, 'error': f'No images in {split} split'}
        
        ratios = {cls: count / total for cls, count in counts.items()}
        
        # Calculate imbalance ratio
        max_count = max(counts.values())
        min_count = min(counts.values()) if min(counts.values()) > 0 else 1
        imbalance_ratio = max_count / min_count
        
        results = {
            'split': split,
            'counts': counts,
            'total': total,
            'ratios': ratios,
            'imbalance_ratio': imbalance_ratio,
            'balanced': imbalance_ratio < 3.0  # Consider balanced if ratio < 3
        }
        
        return results
    
    def check_image_quality(
        self,
        num_samples: int = 100
    ) -> Dict:
        """
        Check image quality across dataset
        
        Args:
            num_samples: Number of images to sample
            
        Returns:
            Dictionary with quality statistics
        """
        # Find all images
        all_images = []
        for split in ['train', 'val', 'test']:
            for class_name in ['swimming', 'drowning']:
                class_dir = self.dataset_root / split / class_name
                if class_dir.exists():
                    images = list(class_dir.glob("**/*.jpg"))
                    all_images.extend(images)
        
        if not all_images:
            return {'valid': False, 'error': 'No images found'}
        
        # Sample images
        import random
        sample_size = min(num_samples, len(all_images))
        sampled = random.sample(all_images, sample_size)
        
        # Check quality
        resolutions = []
        corrupted = []
        sizes_kb = []
        aspect_ratios = []
        
        for img_path in sampled:
            try:
                img = cv2.imread(str(img_path))
                if img is None:
                    corrupted.append(str(img_path))
                    continue
                
                h, w = img.shape[:2]
                resolutions.append((w, h))
                aspect_ratios.append(w / h)
                
                size_kb = img_path.stat().st_size / 1024
                sizes_kb.append(size_kb)
                
            except Exception as e:
                corrupted.append(str(img_path))
        
        if not resolutions:
            return {'valid': False, 'error': 'All sampled images corrupted'}
        
        # Calculate statistics
        resolutions_array = np.array(resolutions)
        aspect_ratios_array = np.array(aspect_ratios)
        sizes_array = np.array(sizes_kb)
        
        results = {
            'valid': len(corrupted) == 0,
            'total_images': len(all_images),
            'sampled': sample_size,
            'corrupted': len(corrupted),
            'corrupted_files': corrupted[:10],  # First 10
            'resolution': {
                'mean': tuple(resolutions_array.mean(axis=0).astype(int)),
                'min': tuple(resolutions_array.min(axis=0)),
                'max': tuple(resolutions_array.max(axis=0)),
                'std': tuple(resolutions_array.std(axis=0).astype(int))
            },
            'aspect_ratio': {
                'mean': float(aspect_ratios_array.mean()),
                'min': float(aspect_ratios_array.min()),
                'max': float(aspect_ratios_array.max()),
                'std': float(aspect_ratios_array.std())
            },
            'file_size_kb': {
                'mean': float(sizes_array.mean()),
                'min': float(sizes_array.min()),
                'max': float(sizes_array.max()),
                'std': float(sizes_array.std())
            }
        }
        
        return results
    
    def check_annotations(
        self,
        annotations_root: str
    ) -> Dict:
        """
        Check annotation files match images
        
        Args:
            annotations_root: Root directory of annotations
            
        Returns:
            Dictionary with annotation validation results
        """
        annotations_root = Path(annotations_root)
        
        results = {
            'images_without_annotations': [],
            'annotations_without_images': [],
            'total_images': 0,
            'total_annotations': 0,
            'matched': 0
        }
        
        for split in ['train', 'val', 'test']:
            for class_name in ['swimming', 'drowning']:
                # Get images
                img_dir = self.dataset_root / split / class_name
                if not img_dir.exists():
                    continue
                
                image_files = list(img_dir.glob("**/*.jpg"))
                image_stems = {img.stem for img in image_files}
                results['total_images'] += len(image_files)
                
                # Get annotations
                ann_dir = annotations_root / split / class_name
                if not ann_dir.exists():
                    results['images_without_annotations'].extend([str(img) for img in image_files])
                    continue
                
                annotation_files = list(ann_dir.glob("**/*.txt"))
                annotation_stems = {ann.stem for ann in annotation_files}
                results['total_annotations'] += len(annotation_files)
                
                # Find mismatches
                images_without_ann = image_stems - annotation_stems
                ann_without_images = annotation_stems - image_stems
                
                results['images_without_annotations'].extend([
                    str(img_dir / f"{stem}.jpg") for stem in images_without_ann
                ])
                results['annotations_without_images'].extend([
                    str(ann_dir / f"{stem}.txt") for stem in ann_without_images
                ])
                
                results['matched'] += len(image_stems & annotation_stems)
        
        results['valid'] = (
            len(results['images_without_annotations']) == 0 and
            len(results['annotations_without_images']) == 0
        )
        
        # Limit to first 100 for readability
        results['images_without_annotations'] = results['images_without_annotations'][:100]
        results['annotations_without_images'] = results['annotations_without_images'][:100]
        
        return results
    
    def generate_full_report(
        self,
        annotations_root: Optional[str] = None,
        output_file: Optional[str] = None
    ) -> Dict:
        """
        Generate comprehensive validation report
        
        Args:
            annotations_root: Root directory of annotations (optional)
            output_file: Path to save report JSON (optional)
            
        Returns:
            Complete validation report
        """
        logger.info("Generating dataset validation report...")
        
        report = {
            'dataset_root': str(self.dataset_root),
            'validation_timestamp': str(pd.Timestamp.now()) if 'pd' in dir() else str(datetime.now()),
            'split_validation': self.validate_split_ratios(),
            'class_balance': {
                'train': self.check_class_balance('train'),
                'val': self.check_class_balance('val'),
                'test': self.check_class_balance('test')
            },
            'image_quality': self.check_image_quality(num_samples=100)
        }
        
        if annotations_root:
            report['annotation_validation'] = self.check_annotations(annotations_root)
        
        # Save report
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Report saved to {output_path}")
        
        return report
    
    def print_report(self, report: Dict):
        """
        Print validation report in readable format
        
        Args:
            report: Report dictionary from generate_full_report
        """
        print("\n" + "="*70)
        print("📊 DATASET VALIDATION REPORT")
        print("="*70)
        
        # Split validation
        split_val = report['split_validation']
        print("\n1️⃣  SPLIT RATIOS:")
        print(f"   Train: {split_val['totals']['train']:,} images ({split_val['ratios']['train']:.1%}) - Target: {split_val['targets']['train']:.1%}")
        print(f"   Val:   {split_val['totals']['val']:,} images ({split_val['ratios']['val']:.1%}) - Target: {split_val['targets']['val']:.1%}")
        print(f"   Test:  {split_val['totals']['test']:,} images ({split_val['ratios']['test']:.1%}) - Target: {split_val['targets']['test']:.1%}")
        print(f"   Total: {split_val['totals']['total']:,} images")
        print(f"   ✅ Valid: {split_val['valid']}")
        
        # Class balance
        print("\n2️⃣  CLASS BALANCE:")
        for split, balance in report['class_balance'].items():
            if 'counts' in balance:
                swimming = balance['counts'].get('swimming', 0)
                drowning = balance['counts'].get('drowning', 0)
                total = balance['total']
                ratio = balance['imbalance_ratio']
                print(f"   {split.capitalize()}:")
                print(f"      Swimming: {swimming:,} ({swimming/total:.1%})")
                print(f"      Drowning: {drowning:,} ({drowning/total:.1%})")
                print(f"      Imbalance Ratio: {ratio:.2f}x {'✅' if ratio < 3.0 else '⚠️'}")
        
        # Image quality
        quality = report['image_quality']
        if quality.get('valid'):
            print("\n3️⃣  IMAGE QUALITY:")
            print(f"   Sampled: {quality['sampled']} images")
            print(f"   Corrupted: {quality['corrupted']}")
            res = quality['resolution']
            print(f"   Resolution:")
            print(f"      Mean: {res['mean']}")
            print(f"      Range: {res['min']} - {res['max']}")
            aspect = quality['aspect_ratio']
            print(f"   Aspect Ratio: {aspect['mean']:.2f} (±{aspect['std']:.2f})")
            size = quality['file_size_kb']
            print(f"   File Size: {size['mean']:.1f} KB (±{size['std']:.1f})")
        
        # Annotation validation
        if 'annotation_validation' in report:
            ann_val = report['annotation_validation']
            print("\n4️⃣  ANNOTATION VALIDATION:")
            print(f"   Total Images: {ann_val['total_images']:,}")
            print(f"   Total Annotations: {ann_val['total_annotations']:,}")
            print(f"   Matched: {ann_val['matched']:,}")
            print(f"   Images without annotations: {len(ann_val['images_without_annotations'])}")
            print(f"   Annotations without images: {len(ann_val['annotations_without_images'])}")
            print(f"   ✅ Valid: {ann_val['valid']}")
        
        print("\n" + "="*70 + "\n")


def main():
    """Test dataset validation"""
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="Validate dataset")
    parser.add_argument('dataset', help='Dataset root directory')
    parser.add_argument('--annotations', help='Annotations root directory')
    parser.add_argument('--output', help='Output report JSON file')
    
    args = parser.parse_args()
    
    validator = DatasetValidator(args.dataset)
    
    report = validator.generate_full_report(
        annotations_root=args.annotations,
        output_file=args.output
    )
    
    validator.print_report(report)


if __name__ == "__main__":
    main()