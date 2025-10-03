#!/usr/bin/env python3
"""
Reorganize annotations into batches of 1000 files per folder
Solves GitHub's 1000 file limit per directory issue
"""

import os
import shutil
from pathlib import Path
import json

def reorganize_annotations_with_batches(
    source_root: Path,
    output_root: Path,
    batch_size: int = 1000
):
    """
    Reorganize annotations into batched folders
    
    Structure changes from:
        train/swimming/*.txt (6000+ files)
    To:
        train/swimming/batch_001/*.txt (1000 files)
        train/swimming/batch_002/*.txt (1000 files)
        ...
    """
    
    print(f"\n🔄 Reorganizing Annotations for GitHub Compatibility")
    print(f"📁 Source: {source_root}")
    print(f"💾 Output: {output_root}")
    print(f"📦 Batch Size: {batch_size} files per folder")
    print("="*70)
    
    stats = {
        "total_files": 0,
        "total_batches": 0,
        "splits": {}
    }
    
    splits = ['train', 'val', 'test']
    classes = ['swimming', 'drowning']
    
    for split in splits:
        stats["splits"][split] = {}
        
        for class_name in classes:
            source_dir = source_root / split / class_name
            
            if not source_dir.exists():
                print(f"⚠️  Skipping {split}/{class_name} (not found)")
                continue
            
            # Get all annotation files
            annotation_files = sorted(list(source_dir.glob("*.txt")))
            total_files = len(annotation_files)
            
            if total_files == 0:
                print(f"⚠️  Skipping {split}/{class_name} (empty)")
                continue
            
            print(f"\n📊 Processing {split}/{class_name}")
            print(f"   Total files: {total_files}")
            
            # Calculate number of batches needed
            num_batches = (total_files + batch_size - 1) // batch_size
            print(f"   Creating {num_batches} batch(es)")
            
            stats["total_files"] += total_files
            stats["splits"][split][class_name] = {
                "total_files": total_files,
                "num_batches": num_batches
            }
            
            # Create batches
            for batch_num in range(num_batches):
                start_idx = batch_num * batch_size
                end_idx = min(start_idx + batch_size, total_files)
                batch_files = annotation_files[start_idx:end_idx]
                
                # Create batch directory
                batch_dir = output_root / split / class_name / f"batch_{batch_num+1:03d}"
                batch_dir.mkdir(parents=True, exist_ok=True)
                
                # Copy files to batch directory
                for file in batch_files:
                    dest_file = batch_dir / file.name
                    shutil.copy2(file, dest_file)
                
                print(f"      ✅ Batch {batch_num+1:03d}: {len(batch_files)} files")
                stats["total_batches"] += 1
    
    # Save reorganization stats
    stats_file = output_root / "reorganization_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    # Print summary
    print("\n" + "="*70)
    print("✅ REORGANIZATION COMPLETE!")
    print("="*70)
    print(f"\n📊 Summary:")
    print(f"   Total Files: {stats['total_files']:,}")
    print(f"   Total Batches: {stats['total_batches']}")
    print(f"   Batch Size: {batch_size} files per folder")
    
    print(f"\n📁 Split Details:")
    for split, split_data in stats["splits"].items():
        if split_data:
            print(f"\n   {split.capitalize()}:")
            for class_name, class_data in split_data.items():
                print(f"      {class_name}: {class_data['total_files']} files → {class_data['num_batches']} batch(es)")
    
    print(f"\n💾 Output Directory: {output_root}")
    print(f"📊 Stats File: {stats_file}")
    print("\n✅ All annotations organized into GitHub-friendly batches!")
    print("="*70)

def main():
    source_root = Path("/app/datasets/annotations/yolov8s_annotations")
    output_root = Path("/app/datasets/annotations/yolov8s_annotations_batched")
    
    if not source_root.exists():
        print(f"❌ Source directory not found: {source_root}")
        return
    
    # Create output directory
    output_root.mkdir(parents=True, exist_ok=True)
    
    # Reorganize with 1000 files per batch
    reorganize_annotations_with_batches(source_root, output_root, batch_size=1000)

if __name__ == "__main__":
    main()
