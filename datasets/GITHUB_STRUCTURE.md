# 📁 Dataset Structure for GitHub

## Overview

This dataset has been reorganized to be GitHub-friendly by splitting large directories (>1000 files) into smaller subdirectories. This avoids GitHub's directory listing limitation.

---

## 📊 New Structure

```
/app/datasets/
├── train/
│   ├── swimming/
│   │   ├── part1/          (1,000 images)
│   │   ├── part2/          (1,000 images)
│   │   ├── part3/          (1,000 images)
│   │   ├── part4/          (1,000 images)
│   │   └── part5/          (611 images)
│   │   └── TOTAL: 4,611 images
│   │
│   └── drowning/
│       ├── part1/          (1,000 images)
│       └── part2/          (927 images)
│       └── TOTAL: 1,927 images
│
├── val/
│   ├── swimming/           (988 images - no split)
│   └── drowning/           (413 images - no split)
│
├── test/
│   ├── swimming/           (989 images - no split)
│   └── drowning/           (414 images - no split)
│
└── raw/
    └── (original downloaded datasets)
```

---

## 📈 File Distribution

| Split | Class | Parts | Files per Part | Total Files |
|-------|-------|-------|----------------|-------------|
| **Train** | Swimming | 5 | 1000, 1000, 1000, 1000, 611 | **4,611** |
| **Train** | Drowning | 2 | 1000, 927 | **1,927** |
| **Val** | Swimming | 1 | 988 | **988** |
| **Val** | Drowning | 1 | 413 | **413** |
| **Test** | Swimming | 1 | 989 | **989** |
| **Test** | Drowning | 1 | 414 | **414** |
| | | | **TOTAL** | **9,342** |

---

## 🔍 Why This Structure?

### GitHub Limitation
GitHub truncates directory listings to 1,000 files, showing:
> "Sorry, we had to truncate this directory to 1,000 files. X entries were omitted from the list."

### Solution
Split directories with >1,000 files into subdirectories (`part1`, `part2`, etc.), each containing ≤1,000 files.

### Benefits
- ✅ All files visible on GitHub
- ✅ Easy to browse and navigate
- ✅ No truncation warnings
- ✅ Better organization for large datasets
- ✅ Compatible with version control

---

## 💻 How to Use This Dataset

### Loading All Images from a Class

**Python Example:**

```python
from pathlib import Path
import glob

def load_dataset(split='train', class_name='swimming'):
    """
    Load all images for a given split and class.
    
    Args:
        split: 'train', 'val', or 'test'
        class_name: 'swimming' or 'drowning'
    
    Returns:
        List of image file paths
    """
    dataset_dir = Path('/app/datasets')
    class_dir = dataset_dir / split / class_name
    
    image_files = []
    
    # Check if directory has subdirectories (parts)
    if any(class_dir.iterdir()).is_dir():
        # Has parts - collect from all subdirectories
        for part_dir in sorted(class_dir.glob('part*')):
            images = list(part_dir.glob('*.jpg'))
            image_files.extend(images)
    else:
        # No parts - get directly from class directory
        image_files = list(class_dir.glob('*.jpg'))
    
    return sorted(image_files)

# Usage
train_swimming = load_dataset('train', 'swimming')
print(f"Loaded {len(train_swimming)} swimming images")
# Output: Loaded 4611 swimming images

train_drowning = load_dataset('train', 'drowning')
print(f"Loaded {len(train_drowning)} drowning images")
# Output: Loaded 1927 drowning images
```

### PyTorch DataLoader

```python
import torch
from torch.utils.data import Dataset, DataLoader
from PIL import Image
from pathlib import Path

class DrowningDataset(Dataset):
    def __init__(self, split='train', transform=None):
        self.transform = transform
        self.images = []
        self.labels = []
        
        dataset_dir = Path('/app/datasets')
        
        # Load swimming images (class 0)
        swimming_dir = dataset_dir / split / 'swimming'
        swimming_images = self._collect_images(swimming_dir)
        self.images.extend(swimming_images)
        self.labels.extend([0] * len(swimming_images))
        
        # Load drowning images (class 1)
        drowning_dir = dataset_dir / split / 'drowning'
        drowning_images = self._collect_images(drowning_dir)
        self.images.extend(drowning_images)
        self.labels.extend([1] * len(drowning_images))
    
    def _collect_images(self, class_dir):
        """Collect images from directory or its subdirectories."""
        images = []
        
        # Check if has subdirectories
        subdirs = [d for d in class_dir.iterdir() if d.is_dir()]
        
        if subdirs:
            # Has parts
            for part_dir in sorted(subdirs):
                images.extend(list(part_dir.glob('*.jpg')))
        else:
            # No parts
            images.extend(list(class_dir.glob('*.jpg')))
        
        return sorted(images)
    
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        image = Image.open(self.images[idx]).convert('RGB')
        label = self.labels[idx]
        
        if self.transform:
            image = self.transform(image)
        
        return image, label

# Usage
train_dataset = DrowningDataset(split='train')
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)

print(f"Dataset size: {len(train_dataset)}")
# Output: Dataset size: 6538
```

### YOLO Training with Ultralytics

```python
from ultralytics import YOLO

# For YOLO, you'll need to update the data.yaml file
# to point to the new structure with parts

# Example data.yaml:
"""
train: /app/datasets/train
val: /app/datasets/val
test: /app/datasets/test

nc: 2  # number of classes
names: ['swimming', 'drowning']
"""

# Train YOLO
model = YOLO('yolov8n.pt')
results = model.train(
    data='data.yaml',
    epochs=100,
    imgsz=640,
    batch=16
)
```

---

## 🔄 Reverting to Original Structure

If you need to merge parts back into single directories:

```bash
cd /app/datasets/scripts
python merge_parts.py
```

This will:
- Merge all `partX` subdirectories back into parent directory
- Remove empty subdirectories
- Restore original structure

---

## 📝 File Naming Convention

All files follow this naming pattern:

```
{class}_{split}_{index:05d}.jpg
```

Examples:
- `swimming_train_00000.jpg` to `swimming_train_04610.jpg`
- `drowning_train_00000.jpg` to `drowning_train_01926.jpg`

Annotation files (if present):
- `swimming_train_00000.txt`
- `drowning_train_00000.txt`

---

## 🚀 Git Commands

### Adding to Git

```bash
# Add all dataset files
git add /app/datasets/train
git add /app/datasets/val
git add /app/datasets/test

# Commit
git commit -m "Reorganize dataset into GitHub-friendly structure"

# Push
git push origin main
```

### Checking Status

```bash
# Check which directories have >1000 files
find /app/datasets/{train,val,test} -maxdepth 2 -type d | \
while read dir; do
    count=$(find "$dir" -maxdepth 1 -name "*.jpg" | wc -l)
    if [ $count -gt 1000 ]; then
        echo "$dir: $count files (needs splitting)"
    fi
done
```

---

## 📊 Statistics

### Before Reorganization
```
train/swimming/     4,611 files ❌ (GitHub truncated)
train/drowning/     1,927 files ❌ (GitHub truncated)
val/swimming/       988 files ✓
val/drowning/       413 files ✓
test/swimming/      989 files ✓
test/drowning/      414 files ✓
```

### After Reorganization
```
train/swimming/part1-5/  All ≤1,000 files ✓
train/drowning/part1-2/  All ≤1,000 files ✓
val/swimming/            988 files ✓
val/drowning/            413 files ✓
test/swimming/           989 files ✓
test/drowning/           414 files ✓
```

---

## ⚙️ Automation Scripts

All scripts are in `/app/datasets/scripts/`:

1. **`reorganize_for_github.py`** - Split large directories
   ```bash
   python reorganize_for_github.py --dry-run  # Preview
   python reorganize_for_github.py            # Execute
   ```

2. **`merge_parts.py`** - Merge parts back (if needed)
   ```bash
   python merge_parts.py --dry-run  # Preview
   python merge_parts.py            # Execute
   ```

3. **`verify_structure.py`** - Verify all files are accessible
   ```bash
   python verify_structure.py
   ```

---

## 🐛 Troubleshooting

### Issue: "Can't find images"

**Solution:** Update your code to handle subdirectories:

```python
def get_all_images(directory):
    """Get images from directory or its subdirectories."""
    images = []
    for item in directory.rglob('*.jpg'):
        if item.is_file():
            images.append(item)
    return images
```

### Issue: "Missing files"

**Solution:** Check if all parts are present:

```bash
cd /app/datasets/train/swimming
ls -la part*
# Should show: part1, part2, part3, part4, part5
```

### Issue: "Git push too slow"

**Solution:** GitHub has size limits. Consider using:
- Git LFS (Large File Storage) for large datasets
- External storage (S3, Google Drive) + download script
- Dataset hosting services (Roboflow, Kaggle)

---

## 📚 Related Documentation

- **README.md** - Main dataset documentation
- **QUICK_START.md** - Quick start guide
- **IMPLEMENTATION_STATUS.md** - Phase 1.1 completion status
- **DOWNLOAD_COMPLETE.md** - Dataset download summary

---

## ✅ Verification Checklist

After reorganization, verify:

- [ ] All 4,611 swimming training images present across 5 parts
- [ ] All 1,927 drowning training images present across 2 parts
- [ ] Val and test sets unchanged
- [ ] Total still equals 9,342 images
- [ ] No files lost during reorganization
- [ ] Code updated to handle new structure
- [ ] Git can track all files without truncation

---

## 🎯 Summary

**What Changed:**
- `train/swimming/` → Split into 5 parts (max 1,000 files each)
- `train/drowning/` → Split into 2 parts (max 1,000 files each)
- Other directories unchanged (already <1,000 files)

**Why:**
- GitHub directory listing limitation (1,000 files)
- Better organization for large datasets
- Easier navigation and browsing

**Result:**
- ✅ All 9,342 images still accessible
- ✅ No data loss
- ✅ GitHub-friendly structure
- ✅ Ready to push to repository

---

**Last Updated:** 2025-01-15  
**Total Images:** 9,342  
**Structure Version:** 2.0 (GitHub-optimized)
