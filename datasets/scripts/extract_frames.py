#!/usr/bin/env python3
"""
Video Frame Extraction Script

Extracts frames from videos for dataset creation.

Usage:
    python extract_frames.py --video video.mp4
    python extract_frames.py --directory ../raw/youtube
    python extract_frames.py --video video.mp4 --fps 10 --output frames/
"""

import os
import sys
import argparse
from pathlib import Path

try:
    import cv2
    from tqdm import tqdm
except ImportError as e:
    print(f"Error: Required package not installed: {e}")
    print("Install with: pip install opencv-python tqdm")
    sys.exit(1)


def extract_frames_from_video(video_path, output_dir, fps=10, max_frames=None):
    """
    Extract frames from a video file.
    
    Args:
        video_path: Path to video file
        output_dir: Directory to save extracted frames
        fps: Target frames per second to extract
        max_frames: Maximum number of frames to extract (None = all)
    
    Returns:
        Number of frames extracted
    """
    video_path = Path(video_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Open video
    cap = cv2.VideoCapture(str(video_path))
    
    if not cap.isOpened():
        print(f"Error: Could not open video {video_path}")
        return 0
    
    # Get video properties
    original_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / original_fps if original_fps > 0 else 0
    
    print(f"\nProcessing: {video_path.name}")
    print(f"  Original FPS: {original_fps:.2f}")
    print(f"  Duration: {duration:.2f} seconds")
    print(f"  Total frames: {total_frames}")
    print(f"  Target FPS: {fps}")
    
    # Calculate frame skip
    frame_skip = int(original_fps / fps) if fps < original_fps else 1
    expected_frames = total_frames // frame_skip
    
    if max_frames:
        expected_frames = min(expected_frames, max_frames)
    
    print(f"  Extracting ~{expected_frames} frames (every {frame_skip} frames)")
    
    # Extract frames
    frame_count = 0
    extracted_count = 0
    video_name = video_path.stem
    
    with tqdm(total=expected_frames) as pbar:
        while True:
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # Extract frame at specified interval
            if frame_count % frame_skip == 0:
                frame_filename = output_dir / f"{video_name}_frame_{extracted_count:05d}.jpg"
                cv2.imwrite(str(frame_filename), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                extracted_count += 1
                pbar.update(1)
                
                if max_frames and extracted_count >= max_frames:
                    break
            
            frame_count += 1
    
    cap.release()
    
    print(f"  ✓ Extracted {extracted_count} frames to {output_dir}")
    
    return extracted_count


def process_directory(directory, output_base, fps=10, max_frames=None):
    """
    Process all videos in a directory.
    """
    directory = Path(directory)
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'}
    
    video_files = []
    for ext in video_extensions:
        video_files.extend(directory.glob(f"*{ext}"))
        video_files.extend(directory.glob(f"*{ext.upper()}"))
    
    if not video_files:
        print(f"No video files found in {directory}")
        return 0
    
    print(f"\nFound {len(video_files)} video(s) to process")
    
    total_extracted = 0
    
    for video_file in video_files:
        output_dir = Path(output_base) / video_file.stem
        extracted = extract_frames_from_video(video_file, output_dir, fps, max_frames)
        total_extracted += extracted
    
    return total_extracted


def main():
    parser = argparse.ArgumentParser(
        description="Extract frames from videos for dataset creation"
    )
    parser.add_argument(
        "--video",
        type=str,
        help="Single video file to process"
    )
    parser.add_argument(
        "--directory",
        type=str,
        help="Directory containing videos to process"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="../raw/extracted_frames",
        help="Output directory for extracted frames"
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=10,
        help="Target frames per second to extract (default: 10)"
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=None,
        help="Maximum frames to extract per video"
    )
    
    args = parser.parse_args()
    
    if not args.video and not args.directory:
        parser.print_help()
        print("\nError: Please provide --video or --directory")
        sys.exit(1)
    
    print("="*70)
    print("Video Frame Extraction")
    print("="*70)
    
    total_frames = 0
    
    if args.video:
        output_dir = Path(args.output) / Path(args.video).stem
        total_frames = extract_frames_from_video(
            args.video, output_dir, args.fps, args.max_frames
        )
    elif args.directory:
        total_frames = process_directory(
            args.directory, args.output, args.fps, args.max_frames
        )
    
    print("\n" + "="*70)
    print("EXTRACTION COMPLETE")
    print("="*70)
    print(f"Total frames extracted: {total_frames}")
    print(f"Output location: {args.output}")
    print("\nNext steps:")
    print("  1. Review extracted frames")
    print("  2. Manually label as swimming/drowning if needed")
    print("  3. Run organize_dataset.py to include in dataset")
    print("="*70)


if __name__ == "__main__":
    main()
