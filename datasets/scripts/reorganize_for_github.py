#!/usr/bin/env python3
"""
Reorganize Dataset for GitHub

Splits large directories (>1000 files) into smaller subdirectories
to avoid GitHub's directory listing limitation.

Usage:
    python reorganize_for_github.py
    python reorganize_for_github.py --max-files 1000 --dry-run
"""

import os
import sys
import shutil
import argparse
from pathlib import Path
from collections import defaultdict

try:
    from tqdm import tqdm
except ImportError:
    print("Installing tqdm...")
    os.system("pip install tqdm")
    from tqdm import tqdm


class DatasetReorganizer:
    """
    Reorganizes dataset by splitting large directories into smaller ones.
    """
    
    def __init__(self, dataset_dir, max_files_per_dir=1000, dry_run=False):
        self.dataset_dir = Path(dataset_dir)
        self.max_files = max_files_per_dir
        self.dry_run = dry_run
        self.stats = defaultdict(int)
    
    def count_files_in_dir(self, directory):
        """Count image files in directory."""
        image_extensions = {'.jpg', '.jpeg', '.png'}
        files = [f for f in directory.iterdir() 
                if f.is_file() and f.suffix.lower() in image_extensions]
        return files
    
    def split_directory(self, directory):
        """
        Split a directory into multiple subdirectories if it has >max_files.
        """
        files = self.count_files_in_dir(directory)
        num_files = len(files)
        
        if num_files <= self.max_files:
            print(f"  ✓ {directory.name}: {num_files} files (no split needed)")
            return
        
        # Calculate number of parts needed
        num_parts = (num_files + self.max_files - 1) // self.max_files
        
        print(f"\n  📁 {directory.name}: {num_files} files → splitting into {num_parts} parts")
        
        if self.dry_run:
            for i in range(num_parts):
                start_idx = i * self.max_files
                end_idx = min((i + 1) * self.max_files, num_files)
                count = end_idx - start_idx
                print(f"     Part {i+1}: {count} files")
            return
        
        # Get parent directory and class name
        parent_dir = directory.parent
        class_name = directory.name
        
        # Create temporary directory to hold parts
        temp_dir = parent_dir / f"{class_name}_temp"
        temp_dir.mkdir(exist_ok=True)
        
        # Split files into parts
        for part_num in range(num_parts):
            start_idx = part_num * self.max_files
            end_idx = min((part_num + 1) * self.max_files, num_files)
            part_files = files[start_idx:end_idx]
            
            # Create part directory
            part_dir = temp_dir / f"part{part_num + 1}"
            part_dir.mkdir(exist_ok=True)
            
            # Move files to part directory
            for file in tqdm(part_files, desc=f"    Moving to part{part_num + 1}"):
                # Move image file
                dest_file = part_dir / file.name
                shutil.move(str(file), str(dest_file))
                
                # Move annotation file if exists
                txt_file = file.with_suffix('.txt')
                if txt_file.exists():
                    dest_txt = part_dir / txt_file.name
                    shutil.move(str(txt_file), str(dest_txt))
                
                self.stats['files_moved'] += 1
        
        # Remove original directory
        if directory.exists() and not any(directory.iterdir()):
            directory.rmdir()
        
        # Rename temp directory to original name
        shutil.move(str(temp_dir), str(directory))
        
        print(f"  ✓ Split complete: {num_parts} parts created")
        self.stats['directories_split'] += 1
    
    def reorganize(self):
        """
        Main reorganization process.
        """
        print("="*70)
        print("DATASET REORGANIZATION FOR GITHUB")
        print("="*70)
        print(f"Dataset directory: {self.dataset_dir}")
        print(f"Max files per directory: {self.max_files}")
        print(f"Dry run: {self.dry_run}")
        print("="*70 + "\n")
        
        # Process each split
        for split_name in ['train', 'val', 'test']:
            split_dir = self.dataset_dir / split_name
            
            if not split_dir.exists():
                print(f"⚠️  {split_name}/ not found, skipping...")
                continue
            
            print(f"\n📂 Processing {split_name}/")
            print("-" * 70)
            
            # Process each class
            for class_name in ['swimming', 'drowning']:
                class_dir = split_dir / class_name
                
                if not class_dir.exists():
                    print(f"  ⚠️  {class_name}/ not found, skipping...")
                    continue
                
                self.split_directory(class_dir)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """
        Print reorganization summary.
        """
        print("\n" + "="*70)
        print("REORGANIZATION SUMMARY")
        print("="*70)
        
        if self.dry_run:
            print("Mode: DRY RUN (no changes made)")
        else:
            print("Mode: EXECUTED (changes applied)")
        
        print(f"\nDirectories split: {self.stats['directories_split']}")
        print(f"Files moved: {self.stats['files_moved']}")
        
        print("\n📊 New Structure:")
        self.print_structure()
        
        print("\n" + "="*70)
        print("RECOMMENDATIONS:")
        print("="*70)
        print("1. Review the new structure above")
        print("2. Verify a few files are in correct locations")
        print("3. Update your code to handle the new structure if needed")
        print("4. Add all changes to git: git add .")
        print("5. Commit: git commit -m 'Reorganize dataset for GitHub'")
        print("6. Push: git push origin main")
        print("="*70)
    
    def print_structure(self):
        """
        Print the new directory structure.
        """
        for split_name in ['train', 'val', 'test']:
            split_dir = self.dataset_dir / split_name
            
            if not split_dir.exists():
                continue
            
            print(f"\n{split_name}/")
            
            for class_dir in sorted(split_dir.iterdir()):
                if not class_dir.is_dir():
                    continue
                
                # Check if it has subdirectories (parts)
                subdirs = [d for d in class_dir.iterdir() if d.is_dir()]
                
                if subdirs:
                    # Has parts
                    print(f"├── {class_dir.name}/")
                    for i, subdir in enumerate(sorted(subdirs)):
                        num_files = len(self.count_files_in_dir(subdir))
                        is_last = i == len(subdirs) - 1
                        prefix = "└──" if is_last else "├──"
                        print(f"│   {prefix} {subdir.name}/ ({num_files} images)")
                else:
                    # No parts
                    num_files = len(self.count_files_in_dir(class_dir))
                    print(f"├── {class_dir.name}/ ({num_files} images)")


def main():
    parser = argparse.ArgumentParser(
        description="Reorganize dataset for GitHub by splitting large directories"
    )
    parser.add_argument(
        "--dataset-dir",
        type=str,
        default="..",
        help="Dataset directory path (default: ..)"
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=1000,
        help="Maximum files per directory (default: 1000)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    
    args = parser.parse_args()
    
    # Confirm if not dry run
    if not args.dry_run:
        print("\n⚠️  WARNING: This will reorganize your dataset!")
        print("It's recommended to run with --dry-run first.\n")
        response = input("Continue? (yes/no): ").lower().strip()
        if response != 'yes':
            print("Aborted.")
            return
    
    # Create reorganizer and run
    reorganizer = DatasetReorganizer(
        dataset_dir=args.dataset_dir,
        max_files_per_dir=args.max_files,
        dry_run=args.dry_run
    )
    
    reorganizer.reorganize()


if __name__ == "__main__":
    main()
