#!/usr/bin/env python3
"""
Data Augmentation Module
Implements all augmentation techniques for swimming pool drowning detection:
- Horizontal flip
- Brightness adjustment
- Contrast adjustment
- Gaussian noise
- Color jittering
- Random crop and resize
- Motion blur (simulate water movement)
"""

import cv2
import numpy as np
import albumentations as A
from albumentations.pytorch import ToTensorV2
from typing import Optional, Tuple, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataAugmentation:
    """
    Comprehensive data augmentation pipeline for training
    Uses Albumentations for efficient augmentation
    """
    
    def __init__(
        self,
        mode: str = 'train',
        img_size: Tuple[int, int] = (640, 640),
        augment_prob: float = 0.5
    ):
        """
        Initialize augmentation pipeline
        
        Args:
            mode: 'train', 'val', or 'test'
            img_size: Target image size (width, height)
            augment_prob: Probability of applying augmentations
        """
        self.mode = mode
        self.img_size = img_size
        self.augment_prob = augment_prob
        
        if mode == 'train':
            self.transform = self._get_train_transforms()
        elif mode in ['val', 'test']:
            self.transform = self._get_val_transforms()
        else:
            raise ValueError(f"Unknown mode: {mode}")
    
    def _get_train_transforms(self) -> A.Compose:
        """
        Get training augmentation pipeline
        
        Returns:
            Albumentations Compose object
        """
        return A.Compose([
            # Geometric transformations
            A.HorizontalFlip(p=0.5),  # 50% probability horizontal flip
            
            # Random crop and resize
            A.RandomResizedCrop(
                size=(self.img_size[1], self.img_size[0]),  # (height, width)
                scale=(0.8, 1.0),  # Crop 80-100% of image
                ratio=(0.9, 1.1),  # Maintain aspect ratio
                p=0.3
            ),
            
            # Color augmentations
            A.ColorJitter(
                brightness=0.2,  # ±20% brightness
                contrast=0.2,    # ±20% contrast
                saturation=0.15, # ±15% saturation
                hue=0.05,        # Small hue shift
                p=0.5
            ),
            
            # Brightness adjustment (additional control)
            A.RandomBrightnessContrast(
                brightness_limit=0.2,  # ±20%
                contrast_limit=0.2,    # ±20%
                p=0.5
            ),
            
            # Gaussian noise (σ=0.01)
            A.GaussNoise(
                var_limit=(5.0, 15.0),  # Variance range
                mean=0,
                p=0.3
            ),
            
            # Motion blur (simulate water movement)
            A.MotionBlur(
                blur_limit=(3, 7),  # Kernel size
                p=0.3
            ),
            
            # Additional useful augmentations
            A.Blur(blur_limit=3, p=0.2),  # General blur
            
            A.RandomGamma(
                gamma_limit=(80, 120),  # Gamma correction
                p=0.3
            ),
            
            # Optical distortion (simulate water refraction)
            A.OpticalDistortion(
                distort_limit=0.05,
                shift_limit=0.05,
                p=0.2
            ),
            
            # Grid distortion (water surface effects)
            A.GridDistortion(
                num_steps=5,
                distort_limit=0.1,
                p=0.2
            ),
            
            # HSV shift (underwater color variations)
            A.HueSaturationValue(
                hue_shift_limit=10,
                sat_shift_limit=15,
                val_shift_limit=10,
                p=0.3
            ),
            
            # Advanced: simulate reflections and lighting
            A.RandomShadow(
                shadow_roi=(0, 0.5, 1, 1),  # Shadow in upper half
                num_shadows_lower=1,
                num_shadows_upper=2,
                shadow_dimension=5,
                p=0.15
            ),
            
            # Normalize (optional - can be done separately)
            # A.Normalize(
            #     mean=[0.485, 0.456, 0.406],
            #     std=[0.229, 0.224, 0.225],
            #     max_pixel_value=255.0,
            #     p=1.0
            # ),
        ], bbox_params=A.BboxParams(
            format='yolo',  # YOLO format bounding boxes
            label_fields=['class_labels']
        ))
    
    def _get_val_transforms(self) -> A.Compose:
        """
        Get validation/test transforms (no augmentation)
        
        Returns:
            Albumentations Compose object
        """
        return A.Compose([
            # No augmentation for validation/test
            # Just resize if needed
            A.Resize(height=self.img_size[1], width=self.img_size[0], p=1.0),
        ], bbox_params=A.BboxParams(
            format='yolo',
            label_fields=['class_labels']
        ))
    
    def __call__(
        self,
        image: np.ndarray,
        bboxes: Optional[list] = None,
        class_labels: Optional[list] = None
    ) -> Dict:
        """
        Apply augmentation to image and bounding boxes
        
        Args:
            image: Input image (H x W x C), BGR format
            bboxes: List of bounding boxes in YOLO format [(cx, cy, w, h), ...]
            class_labels: List of class labels for each bbox
            
        Returns:
            Dictionary with 'image', 'bboxes', 'class_labels'
        """
        if image is None or image.size == 0:
            raise ValueError("Invalid input image")
        
        # Convert BGR to RGB (Albumentations expects RGB)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        if bboxes is None:
            bboxes = []
        if class_labels is None:
            class_labels = []
        
        # Apply transforms
        transformed = self.transform(
            image=image_rgb,
            bboxes=bboxes,
            class_labels=class_labels
        )
        
        # Convert back to BGR for OpenCV compatibility
        transformed['image'] = cv2.cvtColor(transformed['image'], cv2.COLOR_RGB2BGR)
        
        return transformed
    
    def augment_and_save(
        self,
        input_path: str,
        output_path: str,
        annotation_path: Optional[str] = None,
        output_annotation_path: Optional[str] = None,
        num_augmented: int = 1,
        quality: int = 95
    ) -> None:
        """
        Augment an image and save results
        
        Args:
            input_path: Path to input image
            output_path: Path to save augmented image
            annotation_path: Path to YOLO annotation file (optional)
            output_annotation_path: Path to save transformed annotations
            num_augmented: Number of augmented versions to generate
            quality: JPEG quality
        """
        from pathlib import Path
        
        # Read image
        image = cv2.imread(input_path)
        if image is None:
            raise ValueError(f"Could not read image: {input_path}")
        
        # Read annotations if provided
        bboxes = []
        class_labels = []
        
        if annotation_path and Path(annotation_path).exists():
            with open(annotation_path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) == 5:
                        class_id = int(parts[0])
                        bbox = [float(x) for x in parts[1:5]]
                        bboxes.append(bbox)
                        class_labels.append(class_id)
        
        # Generate augmented versions
        for i in range(num_augmented):
            # Apply augmentation
            result = self(image, bboxes, class_labels)
            
            # Save augmented image
            if num_augmented == 1:
                out_path = output_path
            else:
                out_path = str(Path(output_path).with_stem(
                    f"{Path(output_path).stem}_aug{i+1}"
                ))
            
            Path(out_path).parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(out_path, result['image'], [cv2.IMWRITE_JPEG_QUALITY, quality])
            
            # Save transformed annotations
            if output_annotation_path and bboxes:
                if num_augmented == 1:
                    out_ann_path = output_annotation_path
                else:
                    out_ann_path = str(Path(output_annotation_path).with_stem(
                        f"{Path(output_annotation_path).stem}_aug{i+1}"
                    ))
                
                Path(out_ann_path).parent.mkdir(parents=True, exist_ok=True)
                
                with open(out_ann_path, 'w') as f:
                    for bbox, label in zip(result['bboxes'], result['class_labels']):
                        f.write(f"{label} {bbox[0]:.6f} {bbox[1]:.6f} {bbox[2]:.6f} {bbox[3]:.6f}\n")


class CustomAugmentation:
    """
    Custom augmentation functions for specific water/pool scenarios
    """
    
    @staticmethod
    def add_water_reflection(image: np.ndarray, intensity: float = 0.3) -> np.ndarray:
        """
        Simulate water surface reflection
        
        Args:
            image: Input image
            intensity: Reflection intensity (0-1)
            
        Returns:
            Image with simulated reflection
        """
        h, w = image.shape[:2]
        
        # Create reflection mask (stronger at top)
        y_coords = np.linspace(0, 1, h)
        reflection_mask = (1 - y_coords) * intensity
        reflection_mask = reflection_mask[:, np.newaxis, np.newaxis]
        
        # Add reflection effect
        reflected = image.astype(np.float32)
        reflected = reflected + reflected * reflection_mask
        reflected = np.clip(reflected, 0, 255).astype(np.uint8)
        
        return reflected
    
    @staticmethod
    def add_underwater_tint(image: np.ndarray, blue_boost: float = 1.2) -> np.ndarray:
        """
        Simulate underwater blue/green tint
        
        Args:
            image: Input image
            blue_boost: Blue channel boost factor
            
        Returns:
            Image with underwater tint
        """
        tinted = image.astype(np.float32)
        
        # Boost blue channel, reduce red
        tinted[:, :, 0] = tinted[:, :, 0] * blue_boost  # Blue (BGR)
        tinted[:, :, 2] = tinted[:, :, 2] * 0.8         # Red reduction
        
        tinted = np.clip(tinted, 0, 255).astype(np.uint8)
        return tinted
    
    @staticmethod
    def add_water_turbidity(image: np.ndarray, turbidity: float = 0.2) -> np.ndarray:
        """
        Simulate murky/turbid water
        
        Args:
            image: Input image
            turbidity: Turbidity level (0-1)
            
        Returns:
            Image with turbidity effect
        """
        h, w = image.shape[:2]
        
        # Create turbidity mask
        noise = np.random.normal(0, 20 * turbidity, (h, w, 1))
        
        turbid = image.astype(np.float32) + noise
        turbid = np.clip(turbid, 0, 255).astype(np.uint8)
        
        # Reduce contrast (murky effect)
        turbid = cv2.addWeighted(turbid, 1 - turbidity * 0.5, 
                                 np.full_like(turbid, 128), turbidity * 0.5, 0)
        
        return turbid


def main():
    """Test augmentation pipeline"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test data augmentation")
    parser.add_argument('image', help='Input image path')
    parser.add_argument('--output', help='Output directory', default='./augmented')
    parser.add_argument('--num', type=int, default=5, help='Number of augmentations')
    parser.add_argument('--annotation', help='YOLO annotation file (optional)')
    
    args = parser.parse_args()
    
    from pathlib import Path
    
    # Create augmenter
    augmenter = DataAugmentation(mode='train')
    
    # Output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load image
    image = cv2.imread(args.image)
    if image is None:
        print(f"❌ Could not read image: {args.image}")
        return
    
    # Load annotations if provided
    bboxes = []
    class_labels = []
    
    if args.annotation and Path(args.annotation).exists():
        with open(args.annotation, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 5:
                    class_labels.append(int(parts[0]))
                    bboxes.append([float(x) for x in parts[1:5]])
    
    print(f"📸 Generating {args.num} augmented versions...")
    print(f"   Original image: {image.shape}")
    print(f"   Bounding boxes: {len(bboxes)}")
    
    # Generate augmentations
    for i in range(args.num):
        result = augmenter(image, bboxes, class_labels)
        
        output_path = output_dir / f"augmented_{i+1:02d}.jpg"
        cv2.imwrite(str(output_path), result['image'])
        
        # Save annotations
        if bboxes:
            ann_path = output_dir / f"augmented_{i+1:02d}.txt"
            with open(ann_path, 'w') as f:
                for bbox, label in zip(result['bboxes'], result['class_labels']):
                    f.write(f"{label} {bbox[0]:.6f} {bbox[1]:.6f} {bbox[2]:.6f} {bbox[3]:.6f}\n")
        
        print(f"  ✅ Saved: {output_path.name}")
    
    print(f"\n✅ Generated {args.num} augmented images in {output_dir}")


if __name__ == "__main__":
    main()
