#!/usr/bin/env python3
"""
Image Normalization Module
Normalizes pixel values from [0-255] to [0-1] for neural network input
"""

import numpy as np
import cv2
from pathlib import Path
from typing import Union, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageNormalizer:
    """
    Normalize images for neural network input
    Supports various normalization strategies
    """
    
    def __init__(
        self,
        method: str = 'standard',
        mean: Optional[Tuple[float, float, float]] = None,
        std: Optional[Tuple[float, float, float]] = None
    ):
        """
        Initialize normalizer
        
        Args:
            method: Normalization method
                    - 'standard': [0-255] → [0-1]
                    - 'imagenet': ImageNet mean/std normalization
                    - 'custom': Custom mean/std
            mean: Custom mean values for each channel (R,G,B)
            std: Custom std values for each channel (R,G,B)
        """
        self.method = method
        
        if method == 'imagenet':
            # ImageNet normalization constants
            self.mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
            self.std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        elif method == 'custom':
            if mean is None or std is None:
                raise ValueError("Custom method requires mean and std parameters")
            self.mean = np.array(mean, dtype=np.float32)
            self.std = np.array(std, dtype=np.float32)
        elif method == 'standard':
            self.mean = None
            self.std = None
        else:
            raise ValueError(f"Unknown normalization method: {method}")
    
    def normalize(
        self,
        image: np.ndarray,
        to_float32: bool = True
    ) -> np.ndarray:
        """
        Normalize image
        
        Args:
            image: Input image (H x W x C), dtype uint8 [0-255]
            to_float32: Convert to float32
            
        Returns:
            Normalized image
        """
        if image is None or image.size == 0:
            raise ValueError("Invalid input image")
        
        # Convert to float
        if to_float32:
            normalized = image.astype(np.float32)
        else:
            normalized = image.copy()
        
        if self.method == 'standard':
            # Simple [0-255] → [0-1] normalization
            normalized = normalized / 255.0
        
        elif self.method in ['imagenet', 'custom']:
            # First scale to [0-1]
            normalized = normalized / 255.0
            
            # Then apply mean/std normalization
            # (x - mean) / std
            normalized = (normalized - self.mean) / self.std
        
        return normalized
    
    def denormalize(
        self,
        image: np.ndarray,
        to_uint8: bool = True
    ) -> np.ndarray:
        """
        Denormalize image back to [0-255] range
        
        Args:
            image: Normalized image
            to_uint8: Convert to uint8
            
        Returns:
            Denormalized image
        """
        denorm = image.copy()
        
        if self.method in ['imagenet', 'custom']:
            # Reverse: x_denorm = x * std + mean
            denorm = denorm * self.std + self.mean
        
        # Scale back to [0-255]
        denorm = denorm * 255.0
        
        # Clip to valid range
        denorm = np.clip(denorm, 0, 255)
        
        if to_uint8:
            denorm = denorm.astype(np.uint8)
        
        return denorm
    
    def normalize_batch(
        self,
        images: np.ndarray,
        to_float32: bool = True
    ) -> np.ndarray:
        """
        Normalize a batch of images
        
        Args:
            images: Batch of images (N x H x W x C)
            to_float32: Convert to float32
            
        Returns:
            Normalized batch
        """
        if len(images.shape) != 4:
            raise ValueError(f"Expected 4D batch, got shape {images.shape}")
        
        normalized = np.zeros_like(images, dtype=np.float32 if to_float32 else images.dtype)
        
        for i in range(images.shape[0]):
            normalized[i] = self.normalize(images[i], to_float32)
        
        return normalized
    
    @staticmethod
    def compute_dataset_statistics(
        image_dir: str,
        sample_size: int = 1000
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute mean and std across a dataset for custom normalization
        
        Args:
            image_dir: Directory containing images
            sample_size: Number of images to sample
            
        Returns:
            Tuple of (mean, std) for RGB channels
        """
        image_dir = Path(image_dir)
        
        # Find all images
        image_files = list(image_dir.glob("**/*.jpg"))
        image_files.extend(image_dir.glob("**/*.png"))
        
        # Sample images
        if len(image_files) > sample_size:
            import random
            image_files = random.sample(image_files, sample_size)
        
        logger.info(f"Computing statistics from {len(image_files)} images...")
        
        # Accumulate pixel values
        pixel_sum = np.zeros(3, dtype=np.float64)
        pixel_sq_sum = np.zeros(3, dtype=np.float64)
        pixel_count = 0
        
        for img_path in image_files:
            try:
                img = cv2.imread(str(img_path))
                if img is None:
                    continue
                
                # Convert BGR to RGB
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                
                # Normalize to [0-1]
                img = img.astype(np.float32) / 255.0
                
                # Accumulate statistics
                pixel_sum += img.sum(axis=(0, 1))
                pixel_sq_sum += (img ** 2).sum(axis=(0, 1))
                pixel_count += img.shape[0] * img.shape[1]
                
            except Exception as e:
                logger.warning(f"Failed to process {img_path.name}: {e}")
        
        # Compute mean and std
        mean = pixel_sum / pixel_count
        std = np.sqrt(pixel_sq_sum / pixel_count - mean ** 2)
        
        logger.info(f"Dataset statistics:")
        logger.info(f"  Mean (RGB): {mean}")
        logger.info(f"  Std (RGB):  {std}")
        
        return mean, std


def main():
    """Test normalization"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Image normalization")
    parser.add_argument('--compute-stats', help='Compute dataset statistics from directory')
    parser.add_argument('--test-image', help='Test normalization on single image')
    parser.add_argument('--method', default='standard',
                        choices=['standard', 'imagenet', 'custom'],
                        help='Normalization method')
    
    args = parser.parse_args()
    
    if args.compute_stats:
        mean, std = ImageNormalizer.compute_dataset_statistics(args.compute_stats)
        print(f"\n✅ Dataset Statistics:")
        print(f"Mean (RGB): [{mean[0]:.4f}, {mean[1]:.4f}, {mean[2]:.4f}]")
        print(f"Std  (RGB): [{std[0]:.4f}, {std[1]:.4f}, {std[2]:.4f}]")
    
    elif args.test_image:
        normalizer = ImageNormalizer(method=args.method)
        
        img = cv2.imread(args.test_image)
        if img is None:
            print(f"❌ Could not read image: {args.test_image}")
            return
        
        print(f"Original: shape={img.shape}, dtype={img.dtype}, range=[{img.min()}, {img.max()}]")
        
        normalized = normalizer.normalize(img)
        print(f"Normalized: shape={normalized.shape}, dtype={normalized.dtype}, range=[{normalized.min():.4f}, {normalized.max():.4f}]")
        
        denorm = normalizer.denormalize(normalized)
        print(f"Denormalized: shape={denorm.shape}, dtype={denorm.dtype}, range=[{denorm.min()}, {denorm.max()}]")
        
        print("\n✅ Normalization test complete")
    
    else:
        print("Please provide either --compute-stats or --test-image")


if __name__ == "__main__":
    main()