"""
Media File Renamer

Author: Redouane Elkaboussi
Date: Sat Apr 27

Description:
This script renames media files into a known pattern to organize them efficiently.
"""

# exiftool file rename
# exiftool '-filename<DateTimeOriginal' -d '%Y-%m-%d_%H-%M-%S.%%e' -r .
# '%Y-%m-%d_%H-%M-%S.%%e'

import re
import sys
from dataclasses import dataclass
from pathlib import Path
import argparse
import shutil
import subprocess


@dataclass
class FileMetaData:
    year: int
    month: int
    day: int
    hour: int
    minute: int
    second: int
    extension: str


def parse_filename(filename: Path) -> FileMetaData:
    pattern = (
        r"(\d{4})-(\d{2})-(\d{2}) (\d{2})\.(\d{2})\.(\d{2})\.(\w+)|"  # 2021-01-01 01.01.01.jpg
        r"IMG_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})_(\d+)\.(\w+)|"  # IMG_20210101_010101_123.jpg
        r"PXL_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})(\d+)\.(\w+)|"  # PXL_20210101_010101_123.jpg
        r"Screenshot from (\d{4})-(\d{2})-(\d{2}) (\d{2})-(\d{2})-(\d{2})\.(\w+)|"  # Screenshot from 2021-01-01 01-01-01.jpg
        r"VID_(\d{4})(\d{2})(\d{2})_(\w{2})(\d{4})\.(\w+)|"  # VID_20210101_WA0000.mp4
        r"PXL_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})(\d{3})\.(\w+)|"  # PXL_20210101_010101_123.jpg
        r"IMG_(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{3})\.(\w+)|"  # IMG_2021-01-01-01-01-01-123.jpg
        r"IMG_(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{3})-(\d+)\.(\w+)|"  # IMG_2021-01-01-01-01-01-123-1.jpg
        r"(\d{4})-(\d{2})-(\d{2}) (\d{2})\.(\d{2})\.(\d{2})_(\d+)\.(\w+)"  # 2021-01-01 01.01.01_123.jpg
    )

    match = re.match(pattern, filename.name)
    if not match:
        return None
    groups = [g for g in match.groups() if g is not None]
    year, month, day = map(int, groups[:3])
    extension = filename.suffix[1:]
    if "WA" in filename.name:
        hour, minute, second = int(groups[4]), 0, 0
    elif len(groups) == 6 and "VID" in filename.name:
        hour = int(groups[3])
        minute = int(groups[4][:2])
        second = int(groups[4][2:])
    else:
        hour, minute, second = map(int, groups[3:6])
    return FileMetaData(year, month, day, hour, minute, second, extension)


def get_filename_format(directory: Path, metadata: FileMetaData) -> Path:
    filename = f"{metadata.year:04d}-{metadata.month:02d}-{metadata.day:02d}_{metadata.hour:02d}-{metadata.minute:02d}-{metadata.second:02d}.{metadata.extension}"
    return Path(directory / filename)


def get_unique_filepath(directory: Path, metadata: FileMetaData) -> Path:
    base_filepath = get_filename_format(directory, metadata)
    for i in range(1, 100):
        new_filepath = base_filepath.with_name(
            f"{base_filepath.stem}_{i}{base_filepath.suffix}"
        )
        if not new_filepath.exists():
            return new_filepath
    raise Exception("Could not find a unique filename")


def rename_files(directory: Path, args) -> int:
    try:
        for filepath in directory.iterdir():
            if not filepath.is_file():
                continue
            metadata = parse_filename(filepath)
            if not metadata:
                continue
            new_filepath: Path = get_unique_filepath(directory, metadata)
            if args.verbose:
                print(f"renaming: {filepath} to {new_filepath}.")
            if args.rename and (
                args.yes
                or input(f"Rename? {filepath} -> {new_filepath} (y/n): ").lower() == "y"
            ):
                filepath.rename(new_filepath)
                if args.verbose:
                    print(f"Renamed: {filepath} -> {new_filepath}")
    except Exception as e:
        print(e, file=sys.stderr)
        return 1
    return 0


def run_exiftool(directory: Path) -> int:
    exiftool_path = shutil.which("exiftool")
    if not exiftool_path:
        print("exiftool not found.", file=sys.stderr)
        return 1
    rc = subprocess.call(
        [exiftool_path, "-filename<DateTimeOriginal", "-d", "%Y-%m-%d_%H-%M-%S.%%e", "-r", directory.name, "."]
    )
    if rc != 0:
        print("exiftool failed.", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Rename files in a directory.")
    parser.add_argument(
        "directory", type=str, help="Path to the directory containing files to rename"
    )
    parser.add_argument(
        "-r", "--rename", action="store_true", help="Rename files (default: dry-run)"
    )
    parser.add_argument(
        "-y", "--yes", action="store_true", help="Don't ask for confirmation"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Print verbose output"
    )
    # add args to run exitool
    parser.add_argument(
        "-e", "--exiftool", action="store_true", help="Run exiftool"
    )
    args = parser.parse_args()

    if args.exiftool:
        run_exiftool(Path(args.directory))

    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"{directory} is not a directory.", file=sys.stderr)
        return 1

    return rename_files(directory, args)


if __name__ == "__main__":
    sys.exit(main())
 
