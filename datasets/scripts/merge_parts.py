#!/usr/bin/env python3
"""
Merge Split Parts Back to Original Structure

Reverses the reorganization by merging partX subdirectories back into parent.

Usage:
    python merge_parts.py
    python merge_parts.py --dry-run
"""

import os
import shutil
import argparse
from pathlib import Path

try:
    from tqdm import tqdm
except ImportError:
    os.system("pip install tqdm")
    from tqdm import tqdm


def merge_parts(dataset_dir, dry_run=False):
    """
    Merge part subdirectories back into parent directory.
    """
    dataset_dir = Path(dataset_dir)
    
    print("="*70)
    print("MERGE SPLIT PARTS")
    print("="*70)
    print(f"Dataset directory: {dataset_dir}")
    print(f"Dry run: {dry_run}")
    print("="*70 + "\n")
    
    merged_count = 0
    files_moved = 0
    
    # Process each split
    for split_name in ['train', 'val', 'test']:
        split_dir = dataset_dir / split_name
        
        if not split_dir.exists():
            continue
        
        print(f"\n📂 Processing {split_name}/")
        
        # Process each class
        for class_dir in split_dir.iterdir():
            if not class_dir.is_dir():
                continue
            
            # Check if has part subdirectories
            part_dirs = sorted([d for d in class_dir.glob('part*') if d.is_dir()])
            
            if not part_dirs:
                print(f"  ✓ {class_dir.name}: No parts to merge")
                continue
            
            print(f"  📁 {class_dir.name}: Found {len(part_dirs)} parts to merge")
            
            if dry_run:
                total_files = sum(len(list(p.glob('*.jpg'))) for p in part_dirs)
                print(f"     Would merge {total_files} files")
                continue
            
            # Move all files from parts to parent
            for part_dir in part_dirs:
                files = list(part_dir.glob('*'))
                
                for file in tqdm(files, desc=f"    Merging {part_dir.name}"):
                    dest = class_dir / file.name
                    shutil.move(str(file), str(dest))
                    files_moved += 1
                
                # Remove empty part directory
                part_dir.rmdir()
            
            merged_count += 1
            print(f"  ✓ Merged {len(part_dirs)} parts")
    
    # Summary
    print("\n" + "="*70)
    print("MERGE SUMMARY")
    print("="*70)
    
    if dry_run:
        print("Mode: DRY RUN (no changes made)")
    else:
        print("Mode: EXECUTED (changes applied)")
        print(f"\nDirectories merged: {merged_count}")
        print(f"Files moved: {files_moved}")
    
    print("="*70)


def main():
    parser = argparse.ArgumentParser(
        description="Merge part subdirectories back into parent"
    )
    parser.add_argument(
        "--dataset-dir",
        type=str,
        default="..",
        help="Dataset directory path (default: ..)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    
    args = parser.parse_args()
    
    # Confirm if not dry run
    if not args.dry_run:
        print("\n⚠️  WARNING: This will merge all parts back!")
        response = input("Continue? (yes/no): ").lower().strip()
        if response != 'yes':
            print("Aborted.")
            return
    
    merge_parts(args.dataset_dir, args.dry_run)


if __name__ == "__main__":
    main()
