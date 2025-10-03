#!/usr/bin/env python3
"""
Image Resizer Module
Resizes images to 640x640 (YOLO standard) while maintaining aspect ratio with padding
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Union
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageResizer:
    """
    Resize images to target size with aspect ratio preservation
    Adds padding to maintain aspect ratio (letterboxing)
    """
    
    def __init__(
        self,
        target_size: Tuple[int, int] = (640, 640),
        pad_color: Tuple[int, int, int] = (114, 114, 114)
    ):
        """
        Initialize image resizer
        
        Args:
            target_size: Target (width, height) - default (640, 640) for YOLO
            pad_color: RGB color for padding (default: gray 114,114,114)
        """
        self.target_size = target_size
        self.pad_color = pad_color
        
    def resize_with_padding(
        self,
        image: np.ndarray,
        return_transform: bool = False
    ) -> Union[np.ndarray, Tuple[np.ndarray, dict]]:
        """
        Resize image to target size with letterboxing (padding)
        
        Args:
            image: Input image (H x W x C)
            return_transform: Whether to return transformation parameters
            
        Returns:
            Resized image with padding, optionally with transform dict
        """
        if image is None or image.size == 0:
            raise ValueError("Invalid input image")
        
        original_h, original_w = image.shape[:2]
        target_w, target_h = self.target_size
        
        # Calculate scaling factor (maintain aspect ratio)
        scale = min(target_w / original_w, target_h / original_h)
        
        # Calculate new dimensions
        new_w = int(original_w * scale)
        new_h = int(original_h * scale)
        
        # Resize image
        resized = cv2.resize(
            image,
            (new_w, new_h),
            interpolation=cv2.INTER_LINEAR
        )
        
        # Create padded image
        padded = np.full(
            (target_h, target_w, 3),
            self.pad_color,
            dtype=np.uint8
        )
        
        # Calculate padding offsets (center the image)
        pad_top = (target_h - new_h) // 2
        pad_left = (target_w - new_w) // 2
        
        # Place resized image in center
        padded[pad_top:pad_top + new_h, pad_left:pad_left + new_w] = resized
        
        if return_transform:
            transform = {
                'original_size': (original_w, original_h),
                'resized_size': (new_w, new_h),
                'scale': scale,
                'pad_left': pad_left,
                'pad_top': pad_top,
                'target_size': self.target_size
            }
            return padded, transform
        
        return padded
    
    def transform_bbox(
        self,
        bbox: Tuple[float, float, float, float],
        transform: dict,
        format: str = 'yolo'
    ) -> Tuple[float, float, float, float]:
        """
        Transform bounding box coordinates according to resize transform
        
        Args:
            bbox: Original bounding box
            transform: Transform dictionary from resize_with_padding
            format: 'yolo' (normalized) or 'coco' (absolute pixels)
            
        Returns:
            Transformed bounding box in same format
        """
        if format == 'yolo':
            # YOLO format: (center_x, center_y, width, height) normalized
            center_x, center_y, width, height = bbox
            orig_w, orig_h = transform['original_size']
            
            # Convert to absolute pixels
            abs_center_x = center_x * orig_w
            abs_center_y = center_y * orig_h
            abs_width = width * orig_w
            abs_height = height * orig_h
            
            # Apply scale and padding
            scale = transform['scale']
            new_center_x = abs_center_x * scale + transform['pad_left']
            new_center_y = abs_center_y * scale + transform['pad_top']
            new_width = abs_width * scale
            new_height = abs_height * scale
            
            # Normalize to target size
            target_w, target_h = transform['target_size']
            norm_center_x = new_center_x / target_w
            norm_center_y = new_center_y / target_h
            norm_width = new_width / target_w
            norm_height = new_height / target_h
            
            return (norm_center_x, norm_center_y, norm_width, norm_height)
        
        elif format == 'coco':
            # COCO format: (x, y, width, height) in pixels
            x, y, width, height = bbox
            scale = transform['scale']
            
            new_x = x * scale + transform['pad_left']
            new_y = y * scale + transform['pad_top']
            new_width = width * scale
            new_height = height * scale
            
            return (new_x, new_y, new_width, new_height)
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def resize_image_file(
        self,
        input_path: str,
        output_path: str,
        quality: int = 95
    ) -> None:
        """
        Resize an image file and save to output path
        
        Args:
            input_path: Input image file path
            output_path: Output image file path
            quality: JPEG quality (0-100)
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Image not found: {input_path}")
        
        # Read image
        image = cv2.imread(str(input_path))
        if image is None:
            raise ValueError(f"Could not read image: {input_path}")
        
        # Resize with padding
        resized = self.resize_with_padding(image)
        
        # Create output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save resized image
        cv2.imwrite(
            str(output_path),
            resized,
            [cv2.IMWRITE_JPEG_QUALITY, quality]
        )
    
    def batch_resize(
        self,
        input_dir: str,
        output_dir: str,
        quality: int = 95,
        verbose: bool = True
    ) -> int:
        """
        Batch resize all images in a directory
        
        Args:
            input_dir: Input directory path
            output_dir: Output directory path
            quality: JPEG quality
            verbose: Print progress
            
        Returns:
            Number of images processed
        """
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        
        # Find all image files
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        image_files = []
        for ext in image_extensions:
            image_files.extend(input_dir.glob(f"**/*{ext}"))
        
        if verbose:
            logger.info(f"Found {len(image_files)} images to resize")
        
        processed = 0
        for img_path in image_files:
            try:
                # Maintain directory structure
                relative_path = img_path.relative_to(input_dir)
                output_path = output_dir / relative_path.parent / f"{relative_path.stem}.jpg"
                
                self.resize_image_file(str(img_path), str(output_path), quality)
                processed += 1
                
                if verbose and processed % 100 == 0:
                    logger.info(f"  Processed {processed}/{len(image_files)} images...")
                    
            except Exception as e:
                logger.error(f"Failed to resize {img_path.name}: {e}")
        
        if verbose:
            logger.info(f"✅ Resized {processed} images to {output_dir}")
        
        return processed


def main():
    """Test image resizing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Resize images with padding")
    parser.add_argument('input', help='Input image or directory')
    parser.add_argument('output', help='Output image or directory')
    parser.add_argument('--size', type=int, nargs=2, default=[640, 640],
                        help='Target size (width height), default: 640 640')
    parser.add_argument('--quality', type=int, default=95,
                        help='JPEG quality (default: 95)')
    
    args = parser.parse_args()
    
    resizer = ImageResizer(target_size=tuple(args.size))
    
    input_path = Path(args.input)
    
    if input_path.is_file():
        # Single image
        resizer.resize_image_file(args.input, args.output, args.quality)
        print(f"✅ Resized image saved to {args.output}")
    elif input_path.is_dir():
        # Batch resize
        count = resizer.batch_resize(args.input, args.output, args.quality)
        print(f"✅ Resized {count} images to {args.output}")
    else:
        print(f"❌ Invalid input path: {args.input}")


if __name__ == "__main__":
    main()