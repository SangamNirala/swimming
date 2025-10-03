#!/usr/bin/env python3
"""
Roboflow Dataset Downloader

Downloads multiple drowning detection datasets from Roboflow Universe.

Usage:
    python download_roboflow.py
    python download_roboflow.py --api-key YOUR_API_KEY
    python download_roboflow.py --output /path/to/datasets

Requires:
    - Roboflow API key (set in .env or pass as argument)
    - Internet connection
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
import time

try:
    from roboflow import Roboflow
except ImportError:
    print("Error: roboflow package not installed.")
    print("Install with: pip install roboflow")
    sys.exit(1)

# Load environment variables
load_dotenv()

# Dataset configurations
DATASETS = [
    {
        "name": "Maritime Swimmer Dataset",
        "workspace": "maritime-cumkb",
        "project": "swimmer--swimmer",
        "version": 1,
        "format": "yolov8",
        "description": "Swimmer detection with bounding boxes"
    },
    {
        "name": "Drowning Detection (Zidan)",
        "workspace": "zidan-nlsjs",
        "project": "drowning-detection-e6kbk",
        "version": 1,
        "format": "yolov8",
        "description": "Swimming and drowning classification"
    },
    {
        "name": "Swimming & Drowning Detection",
        "workspace": "kittipat-blwh5",
        "project": "swimming-drowning-ndf8f",
        "version": 1,
        "format": "yolov8",
        "description": "Pool surveillance dataset"
    },
    {
        "name": "Drowning Prevention in Pools",
        "workspace": "machine-learning-computer-vision",
        "project": "drowning-detection-and-prevention-in-swimming-pools-ooq1f",
        "version": 1,
        "format": "yolov8",
        "description": "Comprehensive pool safety dataset"
    }
]


def download_dataset(rf, dataset_config, output_dir):
    """
    Download a single dataset from Roboflow.
    
    Args:
        rf: Roboflow instance
        dataset_config: Dataset configuration dictionary
        output_dir: Output directory path
    
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"Downloading: {dataset_config['name']}")
    print(f"Description: {dataset_config['description']}")
    print(f"{'='*60}")
    
    try:
        # Access workspace and project
        workspace = rf.workspace(dataset_config['workspace'])
        project = workspace.project(dataset_config['project'])
        version = project.version(dataset_config['version'])
        
        # Create output directory
        dataset_dir = os.path.join(
            output_dir,
            f"{dataset_config['project']}_v{dataset_config['version']}"
        )
        os.makedirs(dataset_dir, exist_ok=True)
        
        print(f"Output directory: {dataset_dir}")
        print(f"Format: {dataset_config['format']}")
        print("Downloading... (this may take a few minutes)")
        
        # Download dataset
        dataset = version.download(
            model_format=dataset_config['format'],
            location=dataset_dir,
            overwrite=False
        )
        
        print(f"✓ Successfully downloaded to: {dataset_dir}")
        print(f"  Dataset location: {dataset.location}")
        
        # Display dataset info
        if hasattr(dataset, 'name'):
            print(f"  Dataset name: {dataset.name}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error downloading {dataset_config['name']}: {str(e)}")
        print(f"  This might be due to:")
        print(f"    - Invalid API key")
        print(f"    - Dataset not publicly available")
        print(f"    - Network issues")
        print(f"    - Incorrect workspace/project names")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Download drowning detection datasets from Roboflow"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Roboflow API key (or set ROBOFLOW_API_KEY in .env)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="../raw",
        help="Output directory for downloaded datasets"
    )
    parser.add_argument(
        "--datasets",
        type=str,
        nargs="+",
        default=None,
        help="Specific datasets to download (by index: 0-3)"
    )
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or os.getenv("ROBOFLOW_API_KEY")
    
    if not api_key:
        print("Error: Roboflow API key not found.")
        print("\nPlease either:")
        print("  1. Set ROBOFLOW_API_KEY in .env file")
        print("  2. Pass --api-key argument")
        print("\nTo get an API key:")
        print("  1. Sign up at https://roboflow.com")
        print("  2. Go to Settings > Roboflow API")
        print("  3. Copy your API key")
        sys.exit(1)
    
    # Initialize Roboflow
    print("Initializing Roboflow...")
    try:
        rf = Roboflow(api_key=api_key)
        print("✓ Successfully authenticated with Roboflow")
    except Exception as e:
        print(f"✗ Error authenticating with Roboflow: {str(e)}")
        sys.exit(1)
    
    # Create output directory
    output_dir = os.path.abspath(args.output)
    os.makedirs(output_dir, exist_ok=True)
    print(f"\nOutput directory: {output_dir}")
    
    # Select datasets to download
    if args.datasets:
        try:
            indices = [int(i) for i in args.datasets]
            datasets_to_download = [DATASETS[i] for i in indices]
        except (ValueError, IndexError) as e:
            print(f"Error: Invalid dataset indices. Use 0-{len(DATASETS)-1}")
            sys.exit(1)
    else:
        datasets_to_download = DATASETS
    
    print(f"\nDownloading {len(datasets_to_download)} dataset(s)...\n")
    
    # Download each dataset
    successful = 0
    failed = 0
    
    for i, dataset_config in enumerate(datasets_to_download, 1):
        print(f"\n[{i}/{len(datasets_to_download)}] Processing...")
        
        if download_dataset(rf, dataset_config, output_dir):
            successful += 1
        else:
            failed += 1
        
        # Rate limiting (be nice to Roboflow API)
        if i < len(datasets_to_download):
            print("\nWaiting 5 seconds before next download...")
            time.sleep(5)
    
    # Summary
    print("\n" + "="*60)
    print("DOWNLOAD SUMMARY")
    print("="*60)
    print(f"Total datasets: {len(datasets_to_download)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Output directory: {output_dir}")
    print("\nNext steps:")
    print("  1. Review downloaded datasets")
    print("  2. Run organize_dataset.py to merge and split data")
    print("  3. Run verify_dataset.py to check data quality")
    print("="*60)


if __name__ == "__main__":
    main()
