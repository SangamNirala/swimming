#!/usr/bin/env python3
"""
YouTube Video Downloader

Downloads swimming pool videos from YouTube for dataset creation.

Usage:
    python download_youtube.py --url <video_url>
    python download_youtube.py --playlist <playlist_url>
    python download_youtube.py --search "swimming pool surveillance"

Requires: yt-dlp
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    print("Error: yt-dlp not installed.")
    print("Install with: pip install yt-dlp")
    sys.exit(1)


def download_video(url, output_dir):
    """
    Download a single video from YouTube.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    ydl_opts = {
        'format': 'best[ext=mp4]',
        'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Downloading: {url}")
            ydl.download([url])
            print("✓ Download complete")
            return True
    except Exception as e:
        print(f"✗ Error downloading video: {e}")
        return False


def download_playlist(url, output_dir):
    """
    Download all videos from a YouTube playlist.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    ydl_opts = {
        'format': 'best[ext=mp4]',
        'outtmpl': str(output_dir / '%(playlist_index)s_%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Downloading playlist: {url}")
            ydl.download([url])
            print("✓ Playlist download complete")
            return True
    except Exception as e:
        print(f"✗ Error downloading playlist: {e}")
        return False


def search_and_download(query, max_results, output_dir):
    """
    Search YouTube and download videos.
    """
    print(f"Searching YouTube for: {query}")
    print("Note: This feature requires additional configuration.")
    print("Please manually search YouTube and use --url or --playlist options.")
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Download swimming pool videos from YouTube"
    )
    parser.add_argument(
        "--url",
        type=str,
        help="Single video URL to download"
    )
    parser.add_argument(
        "--playlist",
        type=str,
        help="Playlist URL to download"
    )
    parser.add_argument(
        "--search",
        type=str,
        help="Search query (manual search recommended)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="../raw/youtube",
        help="Output directory for downloaded videos"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=10,
        help="Maximum number of search results"
    )
    
    args = parser.parse_args()
    
    if not any([args.url, args.playlist, args.search]):
        parser.print_help()
        print("\nError: Please provide --url, --playlist, or --search")
        sys.exit(1)
    
    print("="*60)
    print("YouTube Video Downloader")
    print("="*60)
    print(f"Output directory: {args.output}\n")
    
    if args.url:
        download_video(args.url, args.output)
    elif args.playlist:
        download_playlist(args.playlist, args.output)
    elif args.search:
        search_and_download(args.search, args.max_results, args.output)
    
    print("\n" + "="*60)
    print("Next steps:")
    print("1. Review downloaded videos")
    print("2. Annotate videos with drowning/swimming labels")
    print("3. Extract frames: python extract_frames.py")
    print("4. Run organize_dataset.py to include in dataset")
    print("="*60)


if __name__ == "__main__":
    main()
