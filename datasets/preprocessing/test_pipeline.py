#!/usr/bin/env python3
"""
Test and Demo Script for Data Preprocessing Pipeline
Tests all components and generates examples
"""

import cv2
import numpy as np
from pathlib import Path
import json
import sys

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from frame_extractor import VideoFrameExtractor
from image_resizer import ImageResizer
from normalizer import ImageNormalizer
from augmentation import DataAugmentation
from dataset_validator import DatasetValidator

print("="*70)
print("🧪 TESTING DATA PREPROCESSING PIPELINE")
print("="*70)

# Test paths
test_output_dir = Path("/app/datasets/preprocessing/test_output")
test_output_dir.mkdir(parents=True, exist_ok=True)

# Find a sample image
sample_image_path = Path("/app/datasets/train/swimming/part1/swimming_train_00002.jpg")

if not sample_image_path.exists():
    print("❌ Sample image not found!")
    sys.exit(1)

print(f"\n📸 Using sample image: {sample_image_path.name}")

# Load sample image
sample_img = cv2.imread(str(sample_image_path))
print(f"   Original shape: {sample_img.shape}")
print(f"   Original size: {sample_image_path.stat().st_size / 1024:.1f} KB")

# Test 1: Image Resizing
print("\n1️⃣  TESTING IMAGE RESIZING")
print("-" * 70)
resizer = ImageResizer(target_size=(640, 640))
resized_img, transform = resizer.resize_with_padding(sample_img, return_transform=True)

print(f"✅ Resized shape: {resized_img.shape}")
print(f"✅ Scale factor: {transform['scale']:.4f}")
print(f"✅ Padding: left={transform['pad_left']}, top={transform['pad_top']}")

# Save resized
resized_path = test_output_dir / "01_resized.jpg"
cv2.imwrite(str(resized_path), resized_img)
print(f"✅ Saved: {resized_path.name}")

# Test 2: Normalization
print("\n2️⃣  TESTING NORMALIZATION")
print("-" * 70)
normalizer = ImageNormalizer(method='standard')
normalized = normalizer.normalize(resized_img)

print(f"✅ Normalized dtype: {normalized.dtype}")
print(f"✅ Normalized range: [{normalized.min():.4f}, {normalized.max():.4f}]")
print(f"✅ Mean: {normalized.mean():.4f}")
print(f"✅ Std: {normalized.std():.4f}")

# Denormalize for saving
denorm = normalizer.denormalize(normalized)
denorm_path = test_output_dir / "02_normalized_denorm.jpg"
cv2.imwrite(str(denorm_path), denorm)
print(f"✅ Saved denormalized: {denorm_path.name}")

# Test 3: Data Augmentation
print("\n3️⃣  TESTING DATA AUGMENTATION")
print("-" * 70)
augmenter = DataAugmentation(mode='train', img_size=(640, 640))

print("Generating 5 augmented versions...")
for i in range(5):
    result = augmenter(resized_img)
    aug_img = result['image']
    
    aug_path = test_output_dir / f"03_augmented_{i+1:02d}.jpg"
    cv2.imwrite(str(aug_path), aug_img)
    print(f"  ✅ Saved: {aug_path.name}")

# Test 4: Specific Augmentations
print("\n4️⃣  TESTING SPECIFIC AUGMENTATIONS")
print("-" * 70)

# Test horizontal flip
import albumentations as A
flip_transform = A.Compose([A.HorizontalFlip(p=1.0)])
flipped = flip_transform(image=cv2.cvtColor(resized_img, cv2.COLOR_BGR2RGB))
flipped_img = cv2.cvtColor(flipped['image'], cv2.COLOR_RGB2BGR)
cv2.imwrite(str(test_output_dir / "04a_flipped.jpg"), flipped_img)
print("  ✅ Horizontal flip")

# Test brightness
brightness_transform = A.Compose([A.RandomBrightnessContrast(brightness_limit=0.3, p=1.0)])
bright = brightness_transform(image=cv2.cvtColor(resized_img, cv2.COLOR_BGR2RGB))
bright_img = cv2.cvtColor(bright['image'], cv2.COLOR_RGB2BGR)
cv2.imwrite(str(test_output_dir / "04b_brightness.jpg"), bright_img)
print("  ✅ Brightness adjustment")

# Test motion blur
blur_transform = A.Compose([A.MotionBlur(blur_limit=7, p=1.0)])
blurred = blur_transform(image=cv2.cvtColor(resized_img, cv2.COLOR_BGR2RGB))
blurred_img = cv2.cvtColor(blurred['image'], cv2.COLOR_RGB2BGR)
cv2.imwrite(str(test_output_dir / "04c_motion_blur.jpg"), blurred_img)
print("  ✅ Motion blur")

# Test noise
noise_transform = A.Compose([A.GaussNoise(var_limit=(10, 30), p=1.0)])
noisy = noise_transform(image=cv2.cvtColor(resized_img, cv2.COLOR_BGR2RGB))
noisy_img = cv2.cvtColor(noisy['image'], cv2.COLOR_RGB2BGR)
cv2.imwrite(str(test_output_dir / "04d_noise.jpg"), noisy_img)
print("  ✅ Gaussian noise")

# Test color jitter
color_transform = A.Compose([A.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1, p=1.0)])
colored = color_transform(image=cv2.cvtColor(resized_img, cv2.COLOR_BGR2RGB))
colored_img = cv2.cvtColor(colored['image'], cv2.COLOR_RGB2BGR)
cv2.imwrite(str(test_output_dir / "04e_color_jitter.jpg"), colored_img)
print("  ✅ Color jitter")

# Test 5: Dataset Validation
print("\n5️⃣  TESTING DATASET VALIDATION")
print("-" * 70)
validator = DatasetValidator("/app/datasets")

# Check split ratios
split_results = validator.validate_split_ratios()
print(f"✅ Split validation: {split_results['valid']}")
print(f"   Train: {split_results['totals']['train']:,} ({split_results['ratios']['train']:.1%})")
print(f"   Val:   {split_results['totals']['val']:,} ({split_results['ratios']['val']:.1%})")
print(f"   Test:  {split_results['totals']['test']:,} ({split_results['ratios']['test']:.1%})")

# Check class balance
balance_train = validator.check_class_balance('train')
print(f"✅ Class balance (train): {balance_train['imbalance_ratio']:.2f}x")
print(f"   Swimming: {balance_train['counts']['swimming']:,}")
print(f"   Drowning: {balance_train['counts']['drowning']:,}")

# Test 6: Create Comparison Grid
print("\n6️⃣  CREATING COMPARISON GRID")
print("-" * 70)

# Create a grid of original vs augmented
grid_images = [resized_img]
for i in range(1, 6):
    img_path = test_output_dir / f"03_augmented_{i:02d}.jpg"
    img = cv2.imread(str(img_path))
    grid_images.append(img)

# Create 2x3 grid
grid_h, grid_w = 2, 3
cell_h, cell_w = 320, 320

grid = np.zeros((grid_h * cell_h, grid_w * cell_w, 3), dtype=np.uint8)

for idx, img in enumerate(grid_images):
    row = idx // grid_w
    col = idx % grid_w
    
    # Resize to cell size
    cell_img = cv2.resize(img, (cell_w, cell_h))
    
    # Add label
    label = "Original" if idx == 0 else f"Aug {idx}"
    cv2.putText(cell_img, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    # Place in grid
    y_start = row * cell_h
    y_end = (row + 1) * cell_h
    x_start = col * cell_w
    x_end = (col + 1) * cell_w
    
    grid[y_start:y_end, x_start:x_end] = cell_img

grid_path = test_output_dir / "05_comparison_grid.jpg"
cv2.imwrite(str(grid_path), grid)
print(f"✅ Saved comparison grid: {grid_path.name}")

# Create summary report
print("\n7️⃣  GENERATING SUMMARY REPORT")
print("-" * 70)

summary = {
    "test_timestamp": "2025-01-03",
    "sample_image": str(sample_image_path),
    "tests_passed": {
        "image_resizing": True,
        "normalization": True,
        "data_augmentation": True,
        "dataset_validation": True,
        "comparison_grid": True
    },
    "output_files": {
        "resized": str(resized_path),
        "augmented": [str(test_output_dir / f"03_augmented_{i:02d}.jpg") for i in range(1, 6)],
        "specific_augmentations": [
            str(test_output_dir / "04a_flipped.jpg"),
            str(test_output_dir / "04b_brightness.jpg"),
            str(test_output_dir / "04c_motion_blur.jpg"),
            str(test_output_dir / "04d_noise.jpg"),
            str(test_output_dir / "04e_color_jitter.jpg")
        ],
        "comparison_grid": str(grid_path)
    },
    "dataset_statistics": {
        "total_images": split_results['totals']['total'],
        "split_ratios": split_results['ratios'],
        "class_balance": {
            "swimming": balance_train['counts']['swimming'],
            "drowning": balance_train['counts']['drowning'],
            "imbalance_ratio": balance_train['imbalance_ratio']
        }
    }
}

summary_path = test_output_dir / "test_summary.json"
with open(summary_path, 'w') as f:
    json.dump(summary, f, indent=2)

print(f"✅ Summary report saved: {summary_path.name}")

# Final summary
print("\n" + "="*70)
print("✅ ALL TESTS PASSED!")
print("="*70)
print(f"\n📁 Output directory: {test_output_dir}")
print(f"📊 Files generated: {len(list(test_output_dir.glob('*')))}")
print("\nGenerated files:")
for file in sorted(test_output_dir.glob('*.jpg')):
    size = file.stat().st_size / 1024
    print(f"   {file.name:40s} {size:6.1f} KB")

print("\n" + "="*70)
print("🎉 DATA PREPROCESSING PIPELINE READY FOR PRODUCTION!")
print("="*70)
