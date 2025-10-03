#!/usr/bin/env python3
"""
Create Pilot Batch for Annotation Quality Control
Selects 200-300 representative images for initial annotation and validation
"""

import os
import shutil
import random
import json
from pathlib import Path
from collections import defaultdict
import argparse

def analyze_dataset_structure():
    """Analyze the current dataset structure"""
    print("📊 Analyzing dataset structure...")
    
    dataset_dir = Path("/app/datasets")
    structure = {}
    
    for split in ["train", "val", "test"]:
        structure[split] = {}
        for class_name in ["swimming", "drowning"]:
            class_dir = dataset_dir / split / class_name
            if class_dir.exists():
                # Count images across subdirectories (part1, part2, etc.)
                image_count = 0
                image_files = []
                
                # Check if there are subdirectories (part1, part2, etc.)
                subdirs = [d for d in class_dir.iterdir() if d.is_dir()]
                if subdirs:
                    for subdir in subdirs:
                        subdir_images = list(subdir.glob("*.jpg"))
                        image_files.extend(subdir_images)
                        image_count += len(subdir_images)
                else:
                    # Images directly in class directory
                    image_files = list(class_dir.glob("*.jpg"))
                    image_count = len(image_files)
                
                structure[split][class_name] = {
                    "count": image_count,
                    "files": image_files
                }
            else:
                structure[split][class_name] = {"count": 0, "files": []}
    
    return structure

def select_pilot_images(structure, pilot_size=250):
    """Select representative images for pilot batch"""
    print(f"\n🎯 Selecting {pilot_size} images for pilot batch...")
    
    # Calculate proportional selection from each split and class
    total_images = sum(
        structure[split][class_name]["count"]
        for split in structure
        for class_name in structure[split]
    )
    
    print(f"📊 Total dataset: {total_images} images")
    
    selected_images = []
    selection_report = {}
    
    for split in ["train", "val", "test"]:
        selection_report[split] = {}
        
        for class_name in ["swimming", "drowning"]:
            class_data = structure[split][class_name]
            class_count = class_data["count"]
            
            if class_count == 0:
                selection_report[split][class_name] = 0
                continue
            
            # Calculate how many to select from this class/split
            proportion = class_count / total_images
            target_count = max(1, int(pilot_size * proportion))
            
            # Don't select more than available
            actual_count = min(target_count, class_count)
            
            # Randomly select images
            if class_data["files"]:
                selected = random.sample(class_data["files"], actual_count)
                
                for img_path in selected:
                    selected_images.append({
                        "source_path": img_path,
                        "split": split,
                        "class": class_name,
                        "filename": img_path.name
                    })
                
                selection_report[split][class_name] = actual_count
                print(f"  ✅ {split}/{class_name}: {actual_count}/{class_count} images")
            else:
                selection_report[split][class_name] = 0
    
    print(f"\n✅ Selected {len(selected_images)} images for pilot batch")
    return selected_images, selection_report

def copy_pilot_images(selected_images):
    """Copy selected images to pilot batch directory"""
    print(f"\n📁 Copying images to pilot batch directory...")
    
    pilot_dir = Path("/app/datasets/annotations/pilot_batch")
    images_dir = pilot_dir / "images"
    annotations_dir = pilot_dir / "annotations"
    
    # Create directories
    images_dir.mkdir(parents=True, exist_ok=True)
    annotations_dir.mkdir(parents=True, exist_ok=True)
    
    copied_count = 0
    copy_report = defaultdict(int)
    
    for img_info in selected_images:
        source_path = img_info["source_path"]
        filename = img_info["filename"]
        
        # Create unique filename to avoid conflicts
        new_filename = f"{img_info['split']}_{img_info['class']}_{filename}"
        dest_path = images_dir / new_filename
        
        try:
            shutil.copy2(source_path, dest_path)
            copied_count += 1
            copy_report[f"{img_info['split']}_{img_info['class']}"] += 1
            
            # Update the image info with new path
            img_info["pilot_path"] = dest_path
            img_info["pilot_filename"] = new_filename
            
        except Exception as e:
            print(f"❌ Failed to copy {source_path}: {e}")
    
    print(f"✅ Successfully copied {copied_count} images")
    
    # Print copy summary
    print("\n📊 Copy Summary:")
    for key, count in copy_report.items():
        print(f"  {key}: {count} images")
    
    return copied_count

def create_pilot_metadata(selected_images, selection_report):
    """Create metadata file for pilot batch"""
    print(f"\n📝 Creating pilot batch metadata...")
    
    pilot_dir = Path("/app/datasets/annotations/pilot_batch")
    metadata_file = pilot_dir / "pilot_metadata.json"
    
    metadata = {
        "creation_date": "2025-01-15",
        "total_images": len(selected_images),
        "selection_report": selection_report,
        "images": [
            {
                "filename": img["pilot_filename"],
                "original_path": str(img["source_path"]),
                "split": img["split"],
                "class": img["class"],
                "annotated": False,
                "reviewed": False
            }
            for img in selected_images
        ],
        "annotation_progress": {
            "total": len(selected_images),
            "completed": 0,
            "reviewed": 0,
            "quality_approved": False
        }
    }
    
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Metadata saved to: {metadata_file}")
    return metadata_file

def create_annotation_checklist():
    """Create checklist for annotators"""
    print(f"\n📋 Creating annotation checklist...")
    
    pilot_dir = Path("/app/datasets/annotations/pilot_batch")
    checklist_file = pilot_dir / "annotation_checklist.md"
    
    checklist_content = """# Pilot Batch Annotation Checklist

## 🎯 Goal
Annotate 200-300 images to establish annotation quality and consistency standards.

## 📋 Pre-Annotation Checklist
- [ ] Read annotation guidelines thoroughly
- [ ] LabelImg properly installed and configured
- [ ] Understand class definitions (swimming vs drowning)
- [ ] Comfortable with bounding box drawing
- [ ] Know keyboard shortcuts (W, A/D, Ctrl+S)

## 🎨 Annotation Process (Per Image)
- [ ] Open image in LabelImg
- [ ] Identify all people in the image
- [ ] For each person:
  - [ ] Draw tight bounding box around person
  - [ ] Assign correct class (swimming=0, drowning=1)
  - [ ] Verify box doesn't extend beyond image boundaries
- [ ] Double-check all annotations
- [ ] Save annotation file (.txt format)
- [ ] Mark image as completed in checklist

## 🔍 Quality Control (Every 10 Images)
- [ ] Review last 10 annotations for consistency
- [ ] Check for missed people
- [ ] Verify class assignments are correct
- [ ] Ensure bounding boxes are tight and accurate
- [ ] Confirm YOLO format is proper

## 📊 Progress Tracking
- [ ] Update progress in pilot_metadata.json
- [ ] Note any challenging images for review
- [ ] Flag any unclear cases for discussion
- [ ] Maintain annotation quality log

## ✅ Completion Criteria
- [ ] All pilot images annotated
- [ ] Self-review completed
- [ ] Quality metrics meet standards:
  - [ ] >95% of people properly annotated
  - [ ] >90% correct class assignments
  - [ ] <5% bounding box errors
- [ ] Ready for peer review

## 🚨 Common Issues to Watch
- [ ] Boxes too large (including too much background)
- [ ] Missing people in crowded scenes
- [ ] Confusing normal underwater swimming with drowning
- [ ] Inconsistent box sizing
- [ ] Wrong class assignments

## 📞 When to Ask for Help
- Unclear whether behavior is swimming vs drowning
- Technical issues with LabelImg
- Unusual edge cases
- Quality concerns
- Process questions

---

**Remember:** Quality over speed! Take time to do it right.
"""
    
    with open(checklist_file, 'w') as f:
        f.write(checklist_content)
    
    print(f"✅ Checklist saved to: {checklist_file}")
    return checklist_file

def create_quick_start_guide():
    """Create quick start guide for pilot batch"""
    print(f"\n📖 Creating quick start guide...")
    
    pilot_dir = Path("/app/datasets/annotations/pilot_batch")
    guide_file = pilot_dir / "QUICK_START.md"
    
    guide_content = """# Pilot Batch Annotation - Quick Start Guide

## 🚀 Getting Started (5 Minutes)

### Step 1: Verify Setup
```bash
# Check if images are ready
ls /app/datasets/annotations/pilot_batch/images | wc -l
# Should show ~250 images

# Check if LabelImg is installed
python -c "import labelImg; print('✅ LabelImg ready')"
```

### Step 2: Launch LabelImg
```bash
cd /app/datasets/annotations/tools
python launch_labelimg.py
```

### Step 3: Configure LabelImg (First Time Only)
1. **Set format to YOLO:** View → Auto Save → Format: YOLO
2. **Load classes:** File → Change Save Dir → Select annotations directory
3. **Verify classes:** Should see "swimming" and "drowning"

### Step 4: Start Annotating
1. **Open first image**
2. **Press W** to create bounding box
3. **Draw box around person**
4. **Select class:** swimming (0) or drowning (1)
5. **Press Ctrl+S** to save
6. **Press D** for next image

## 🎯 Annotation Goals

### Target for Pilot Batch:
- **250 images** total
- **~175 swimming class** (normal behavior)
- **~75 drowning class** (distress behavior)
- **Quality threshold:** >95% accuracy

### Key Quality Metrics:
- All people in image annotated
- Bounding boxes tight around people
- Correct class assignments
- Valid YOLO format output

## 💡 Pro Tips

### Efficient Workflow:
1. **Use keyboard shortcuts:**
   - W: Create box
   - A/D: Previous/Next image
   - Ctrl+S: Save
   - Del: Delete selected box

2. **Quality checks:**
   - Zoom in for small people
   - Check image corners for partially visible people
   - Verify classes match behavior

3. **Consistency rules:**
   - When in doubt, choose "swimming"
   - Brief underwater = swimming
   - Extended struggle = drowning
   - Vertical position + distress = drowning

## 📊 Progress Tracking

### Daily Goals:
- **Day 1:** 30-50 images (get comfortable)
- **Day 2:** 50-75 images (build speed)
- **Day 3:** 75-100 images (maintain quality)
- **Day 4:** Complete remaining images

### Quality Check Points:
- After 25 images: Self-review
- After 50 images: Peer review (if available)
- After 100 images: Comprehensive review
- Final: Complete quality validation

## 🔧 Troubleshooting

### Common Issues:

**Issue:** LabelImg won't start
**Solution:** 
```bash
pip install PyQt5
python tools/setup_labelimg.py
```

**Issue:** Classes not showing
**Solution:** 
- Check predefined_classes.txt exists
- Restart LabelImg
- Manually load classes file

**Issue:** Annotations not saving
**Solution:**
- Check write permissions
- Verify save directory path
- Try saving manually (Ctrl+S)

**Issue:** Can't decide on class
**Solution:**
- Review annotation guidelines
- When uncertain, choose "swimming"
- Flag for review with team

## 📁 File Structure

```
pilot_batch/
├── images/                    # 250 selected images
│   ├── train_swimming_*.jpg
│   ├── train_drowning_*.jpg
│   ├── val_swimming_*.jpg
│   └── ...
├── annotations/               # YOLO format annotations
│   ├── train_swimming_*.txt
│   └── ...
├── pilot_metadata.json       # Progress tracking
├── annotation_checklist.md   # Quality checklist
└── QUICK_START.md           # This file
```

## ✅ Success Criteria

Pilot batch is complete when:
- [ ] All ~250 images annotated
- [ ] Quality review passed (>95% accuracy)
- [ ] Consistent standards established
- [ ] Ready to scale to full dataset
- [ ] Team approved to proceed

## 🎓 Next Steps After Pilot

1. **Quality Review:** External validation of annotations
2. **Guidelines Refinement:** Update based on learnings
3. **Full Dataset Planning:** Batch processing strategy
4. **Team Training:** Scale annotation team if needed
5. **Automation Setup:** Integrate with pre-annotation

---

**Estimated Time:** 8-12 hours for 250 images (experienced annotator)  
**Quality Focus:** Accuracy over speed in pilot phase
"""
    
    with open(guide_file, 'w') as f:
        f.write(guide_content)
    
    print(f"✅ Guide saved to: {guide_file}")
    return guide_file

def main():
    """Main function to create pilot batch"""
    parser = argparse.ArgumentParser(description="Create pilot batch for annotation")
    parser.add_argument("--size", type=int, default=250, help="Number of images in pilot batch")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible selection")
    
    args = parser.parse_args()
    
    print("🎯 Swimming Pool Drowning Detection - Pilot Batch Creation")
    print("=" * 65)
    
    # Set random seed for reproducible results
    random.seed(args.seed)
    
    # Step 1: Analyze dataset structure
    structure = analyze_dataset_structure()
    
    # Print dataset summary
    print(f"\n📊 Dataset Summary:")
    total_swimming = sum(structure[split]["swimming"]["count"] for split in structure)
    total_drowning = sum(structure[split]["drowning"]["count"] for split in structure)
    print(f"  Swimming: {total_swimming} images")
    print(f"  Drowning: {total_drowning} images")
    print(f"  Total: {total_swimming + total_drowning} images")
    
    # Step 2: Select pilot images
    selected_images, selection_report = select_pilot_images(structure, args.size)
    
    # Step 3: Copy images to pilot directory
    copied_count = copy_pilot_images(selected_images)
    
    # Step 4: Create metadata
    metadata_file = create_pilot_metadata(selected_images, selection_report)
    
    # Step 5: Create supporting documents
    checklist_file = create_annotation_checklist()
    guide_file = create_quick_start_guide()
    
    # Summary
    print("\n" + "=" * 65)
    print("🎉 Pilot Batch Creation Complete!")
    
    print(f"\n📊 Pilot Batch Summary:")
    print(f"  Total Images: {len(selected_images)}")
    print(f"  Successfully Copied: {copied_count}")
    
    # Print selection breakdown
    print(f"\n📋 Selection Breakdown:")
    for split in ["train", "val", "test"]:
        for class_name in ["swimming", "drowning"]:
            count = selection_report.get(split, {}).get(class_name, 0)
            if count > 0:
                print(f"  {split}/{class_name}: {count} images")
    
    print(f"\n📁 Files Created:")
    print(f"  📊 Metadata: {metadata_file}")
    print(f"  📋 Checklist: {checklist_file}")
    print(f"  📖 Guide: {guide_file}")
    
    print(f"\n🎯 Next Steps:")
    print("1. Review pilot images for quality and diversity")
    print("2. Run pre-annotation: python tools/pre_annotate.py")
    print("3. Launch LabelImg: python tools/launch_labelimg.py")
    print("4. Start annotation following the checklist")
    print("5. Quality review after 50-100 annotations")
    
    print(f"\n💡 Quick Commands:")
    print("# Start annotating:")
    print("cd /app/datasets/annotations/tools")
    print("python launch_labelimg.py")
    print()
    print("# Check progress:")
    print("python tools/check_pilot_progress.py")

if __name__ == "__main__":
    main()