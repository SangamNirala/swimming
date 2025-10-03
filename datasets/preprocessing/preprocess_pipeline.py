#!/usr/bin/env python3
"""
Complete Data Preprocessing Pipeline for Swimming Pool Drowning Detection
Implements all steps from Phase 1.3:
1. Video → Frame extraction (5-10 FPS)
2. Resize frames to 640x640 (YOLO standard)
3. Normalization (0-255 → 0-1)
4. Data augmentation (all techniques)
5. Train/Val/Test split verification (70/15/15)
"""

import cv2
import numpy as np
from pathlib import Path
import argparse
import logging
import json
from tqdm import tqdm

from frame_extractor import VideoFrameExtractor
from image_resizer import ImageResizer
from normalizer import ImageNormalizer
from augmentation import DataAugmentation
from dataset_validator import DatasetValidator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PreprocessingPipeline:
    """
    Complete preprocessing pipeline for drowning detection dataset
    """
    
    def __init__(
        self,
        dataset_root: str,
        target_size: tuple = (640, 640),
        target_fps: int = 10,
        normalize_method: str = 'standard'
    ):
        """
        Initialize preprocessing pipeline
        
        Args:
            dataset_root: Root directory of dataset
            target_size: Target image size (width, height)
            target_fps: Target FPS for frame extraction
            normalize_method: Normalization method
        """
        self.dataset_root = Path(dataset_root)
        self.target_size = target_size
        self.target_fps = target_fps
        
        # Initialize components
        self.frame_extractor = VideoFrameExtractor(target_fps=target_fps)
        self.resizer = ImageResizer(target_size=target_size)
        self.normalizer = ImageNormalizer(method=normalize_method)
        self.augmenter_train = DataAugmentation(mode='train', img_size=target_size)
        self.augmenter_val = DataAugmentation(mode='val', img_size=target_size)
        self.validator = DatasetValidator(str(dataset_root))
        
    def extract_frames_from_videos(
        self,
        video_dir: str,
        output_dir: str,
        class_name: str = 'swimming'
    ) -> dict:
        """
        Extract frames from all videos in a directory
        
        Args:
            video_dir: Directory containing video files
            output_dir: Output directory for extracted frames
            class_name: Class name for organizing frames
            
        Returns:
            Dictionary with extraction statistics
        """
        logger.info(f"Extracting frames from {video_dir}")
        
        video_dir = Path(video_dir)
        output_dir = Path(output_dir)
        
        # Find all video files
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.MP4', '.AVI']
        video_files = []
        for ext in video_extensions:
            video_files.extend(video_dir.glob(f"**/*{ext}"))
        
        if not video_files:
            logger.warning(f"No video files found in {video_dir}")
            return {'total_videos': 0, 'total_frames': 0}
        
        logger.info(f"Found {len(video_files)} videos")
        
        total_frames = 0
        successful_videos = 0
        
        for video_path in tqdm(video_files, desc="Extracting frames"):
            try:
                video_output_dir = output_dir / class_name / video_path.stem
                
                frame_count, _ = self.frame_extractor.extract_frames(
                    str(video_path),
                    str(video_output_dir),
                    prefix=f"{class_name}_{video_path.stem}"
                )
                
                total_frames += frame_count
                successful_videos += 1
                
            except Exception as e:
                logger.error(f"Failed to extract from {video_path.name}: {e}")
        
        results = {
            'total_videos': len(video_files),
            'successful_videos': successful_videos,
            'total_frames': total_frames
        }
        
        logger.info(f"Extracted {total_frames} frames from {successful_videos} videos")
        
        return results
    
    def resize_dataset(
        self,
        input_dir: str,
        output_dir: str,
        quality: int = 95
    ) -> int:
        """
        Resize all images in dataset to target size
        
        Args:
            input_dir: Input directory
            output_dir: Output directory
            quality: JPEG quality
            
        Returns:
            Number of images resized
        """
        logger.info(f"Resizing images from {input_dir} to {self.target_size}")
        
        count = self.resizer.batch_resize(
            input_dir,
            output_dir,
            quality=quality,
            verbose=True
        )
        
        logger.info(f"Resized {count} images")
        return count
    
    def augment_training_data(
        self,
        train_dir: str,
        output_dir: str,
        augmentations_per_image: int = 3,
        max_images: int = None
    ) -> dict:
        """
        Apply data augmentation to training set
        
        Args:
            train_dir: Training data directory
            output_dir: Output directory for augmented images
            augmentations_per_image: Number of augmented versions per image
            max_images: Maximum images to augment (for testing)
            
        Returns:
            Dictionary with augmentation statistics
        """
        logger.info(f"Augmenting training data from {train_dir}")
        
        train_dir = Path(train_dir)
        output_dir = Path(output_dir)
        
        # Find all training images
        image_files = list(train_dir.glob("**/*.jpg"))
        
        if max_images:
            image_files = image_files[:max_images]
        
        logger.info(f"Augmenting {len(image_files)} images ({augmentations_per_image}x each)")
        
        augmented_count = 0
        
        for img_path in tqdm(image_files, desc="Augmenting"):
            try:
                # Determine class and split from path
                relative_path = img_path.relative_to(train_dir)
                
                for aug_idx in range(augmentations_per_image):
                    output_path = output_dir / relative_path.parent / f"{img_path.stem}_aug{aug_idx+1}.jpg"
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Read image
                    image = cv2.imread(str(img_path))
                    if image is None:
                        continue
                    
                    # Apply augmentation
                    result = self.augmenter_train(image)
                    
                    # Save augmented image
                    cv2.imwrite(str(output_path), result['image'])
                    augmented_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to augment {img_path.name}: {e}")
        
        logger.info(f"Generated {augmented_count} augmented images")
        
        return {
            'original_images': len(image_files),
            'augmented_images': augmented_count,
            'augmentations_per_image': augmentations_per_image
        }
    
    def validate_dataset(
        self,
        annotations_root: str = None
    ) -> dict:
        """
        Run complete dataset validation
        
        Args:
            annotations_root: Root directory of annotations (optional)
            
        Returns:
            Validation report dictionary
        """
        logger.info("Running dataset validation...")
        
        report = self.validator.generate_full_report(
            annotations_root=annotations_root
        )
        
        self.validator.print_report(report)
        
        return report
    
    def preprocess_complete_dataset(
        self,
        resize: bool = True,
        augment: bool = False,
        validate: bool = True,
        annotations_root: str = None
    ) -> dict:
        """
        Run complete preprocessing pipeline
        
        Args:
            resize: Whether to resize images
            augment: Whether to apply augmentation
            validate: Whether to validate dataset
            annotations_root: Annotations directory for validation
            
        Returns:
            Dictionary with all processing results
        """
        results = {
            'dataset_root': str(self.dataset_root),
            'target_size': self.target_size,
            'target_fps': self.target_fps
        }
        
        # Resize images if requested
        if resize:
            logger.info("\n" + "="*70)
            logger.info("STEP 1: Resizing Images to 640x640")
            logger.info("="*70)
            
            resized_dir = self.dataset_root / "resized"
            
            for split in ['train', 'val', 'test']:
                split_dir = self.dataset_root / split
                if split_dir.exists():
                    count = self.resize_dataset(
                        str(split_dir),
                        str(resized_dir / split)
                    )
                    results[f'resized_{split}'] = count
        
        # Augment training data if requested
        if augment:
            logger.info("\n" + "="*70)
            logger.info("STEP 2: Data Augmentation")
            logger.info("="*70)
            
            train_dir = self.dataset_root / "resized" / "train" if resize else self.dataset_root / "train"
            augmented_dir = self.dataset_root / "augmented" / "train"
            
            aug_results = self.augment_training_data(
                str(train_dir),
                str(augmented_dir),
                augmentations_per_image=2  # Generate 2 augmented versions
            )
            results['augmentation'] = aug_results
        
        # Validate dataset if requested
        if validate:
            logger.info("\n" + "="*70)
            logger.info("STEP 3: Dataset Validation")
            logger.info("="*70)
            
            validation_report = self.validate_dataset(annotations_root)
            results['validation'] = validation_report
        
        return results


def main():
    """Main preprocessing script"""
    parser = argparse.ArgumentParser(
        description="Complete Data Preprocessing Pipeline"
    )
    
    # Required arguments
    parser.add_argument(
        'dataset',
        help='Dataset root directory'
    )
    
    # Optional arguments
    parser.add_argument(
        '--size',
        type=int,
        nargs=2,
        default=[640, 640],
        help='Target image size (width height), default: 640 640'
    )
    
    parser.add_argument(
        '--fps',
        type=int,
        default=10,
        help='Target FPS for frame extraction, default: 10'
    )
    
    parser.add_argument(
        '--normalize',
        choices=['standard', 'imagenet', 'custom'],
        default='standard',
        help='Normalization method, default: standard'
    )
    
    # Processing flags
    parser.add_argument(
        '--extract-videos',
        help='Extract frames from videos in this directory'
    )
    
    parser.add_argument(
        '--resize',
        action='store_true',
        help='Resize images to target size'
    )
    
    parser.add_argument(
        '--augment',
        action='store_true',
        help='Apply data augmentation to training set'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate dataset splits and quality'
    )
    
    parser.add_argument(
        '--annotations',
        help='Annotations root directory for validation'
    )
    
    parser.add_argument(
        '--output-report',
        help='Output JSON file for results'
    )
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = PreprocessingPipeline(
        dataset_root=args.dataset,
        target_size=tuple(args.size),
        target_fps=args.fps,
        normalize_method=args.normalize
    )
    
    # Extract frames from videos if requested
    if args.extract_videos:
        logger.info("Extracting frames from videos...")
        pipeline.extract_frames_from_videos(
            video_dir=args.extract_videos,
            output_dir=args.dataset,
            class_name='swimming'  # Can be parameterized
        )
    
    # Run preprocessing pipeline
    results = pipeline.preprocess_complete_dataset(
        resize=args.resize,
        augment=args.augment,
        validate=args.validate,
        annotations_root=args.annotations
    )
    
    # Save results if requested
    if args.output_report:
        output_path = Path(args.output_report)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"\n✅ Results saved to {output_path}")
    
    logger.info("\n" + "="*70)
    logger.info("✅ PREPROCESSING PIPELINE COMPLETE")
    logger.info("="*70)


if __name__ == "__main__":
    main()
