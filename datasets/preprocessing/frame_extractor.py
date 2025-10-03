#!/usr/bin/env python3
"""
Video Frame Extraction Module
Extracts frames from videos at specified FPS for training/inference
"""

import cv2
import os
from pathlib import Path
from typing import Optional, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoFrameExtractor:
    """
    Extract frames from video files at specified FPS
    Supports various video formats: mp4, avi, mov, mkv
    """
    
    def __init__(self, target_fps: int = 10):
        """
        Initialize frame extractor
        
        Args:
            target_fps: Target frames per second to extract (default: 10)
        """
        self.target_fps = target_fps
        
    def extract_frames(
        self,
        video_path: str,
        output_dir: str,
        prefix: str = "frame",
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        quality: int = 95
    ) -> Tuple[int, List[str]]:
        """
        Extract frames from video at target FPS
        
        Args:
            video_path: Path to input video file
            output_dir: Directory to save extracted frames
            prefix: Prefix for frame filenames
            start_time: Start time in seconds (optional)
            end_time: End time in seconds (optional)
            quality: JPEG quality (0-100, default: 95)
            
        Returns:
            Tuple of (frame_count, list of saved frame paths)
        """
        video_path = Path(video_path)
        output_dir = Path(output_dir)
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Open video
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        # Get video properties
        original_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / original_fps if original_fps > 0 else 0
        
        logger.info(f"Video: {video_path.name}")
        logger.info(f"  Original FPS: {original_fps:.2f}")
        logger.info(f"  Duration: {duration:.2f} seconds")
        logger.info(f"  Total Frames: {total_frames}")
        logger.info(f"  Target FPS: {self.target_fps}")
        
        # Calculate frame skip interval
        frame_interval = int(original_fps / self.target_fps) if self.target_fps < original_fps else 1
        
        # Calculate start and end frames
        start_frame = int(start_time * original_fps) if start_time else 0
        end_frame = int(end_time * original_fps) if end_time else total_frames
        
        extracted_frames = []
        frame_count = 0
        current_frame = 0
        
        logger.info(f"Extracting frames from {start_frame} to {end_frame} at interval {frame_interval}...")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Check if we're in the extraction range
            if current_frame < start_frame:
                current_frame += 1
                continue
            
            if current_frame > end_frame:
                break
            
            # Extract frame at intervals
            if (current_frame - start_frame) % frame_interval == 0:
                # Generate output filename
                output_path = output_dir / f"{prefix}_{frame_count:06d}.jpg"
                
                # Save frame
                cv2.imwrite(
                    str(output_path),
                    frame,
                    [cv2.IMWRITE_JPEG_QUALITY, quality]
                )
                
                extracted_frames.append(str(output_path))
                frame_count += 1
                
                if frame_count % 100 == 0:
                    logger.info(f"  Extracted {frame_count} frames...")
            
            current_frame += 1
        
        cap.release()
        
        logger.info(f"✅ Extracted {frame_count} frames to {output_dir}")
        
        return frame_count, extracted_frames
    
    def batch_extract(
        self,
        video_paths: List[str],
        output_base_dir: str,
        **kwargs
    ) -> dict:
        """
        Extract frames from multiple videos
        
        Args:
            video_paths: List of video file paths
            output_base_dir: Base output directory
            **kwargs: Additional arguments for extract_frames
            
        Returns:
            Dictionary with extraction results per video
        """
        results = {}
        
        for video_path in video_paths:
            video_path = Path(video_path)
            video_name = video_path.stem
            
            output_dir = Path(output_base_dir) / video_name
            
            try:
                frame_count, frames = self.extract_frames(
                    str(video_path),
                    str(output_dir),
                    prefix=video_name,
                    **kwargs
                )
                results[video_name] = {
                    'status': 'success',
                    'frame_count': frame_count,
                    'frames': frames
                }
            except Exception as e:
                logger.error(f"Failed to extract from {video_name}: {e}")
                results[video_name] = {
                    'status': 'failed',
                    'error': str(e)
                }
        
        return results


def main():
    """Test frame extraction"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract frames from video")
    parser.add_argument('video', help='Path to video file')
    parser.add_argument('output', help='Output directory')
    parser.add_argument('--fps', type=int, default=10, help='Target FPS (default: 10)')
    parser.add_argument('--start', type=float, help='Start time in seconds')
    parser.add_argument('--end', type=float, help='End time in seconds')
    parser.add_argument('--quality', type=int, default=95, help='JPEG quality (default: 95)')
    
    args = parser.parse_args()
    
    extractor = VideoFrameExtractor(target_fps=args.fps)
    frame_count, _ = extractor.extract_frames(
        args.video,
        args.output,
        start_time=args.start,
        end_time=args.end,
        quality=args.quality
    )
    
    print(f"\n✅ Extraction complete: {frame_count} frames saved to {args.output}")


if __name__ == "__main__":
    main()