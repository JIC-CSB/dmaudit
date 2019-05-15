"""Bioinformatics data management audit of a directory tree."""
import argparse
import os
import sys

from operator import attrgetter
from time import time


class Directory(object):
    """Summary information about a directory."""

    def __init__(self, path, level):
        self.path = path
        self.level = level
        self.size_in_bytes = 0
        self.num_files = 0
        self.sub_directories = []

    def __str__(self):
        return "{} {:7d} {}{}".format(
            sizeof_fmt(self.size_in_bytes),
            self.num_files,
            "  " * self.level,
            os.path.basename(self.path)
        )


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "{:6.1f}{:3s}".format(num, unit + suffix)
        num /= 1024.0
    return "{:6.1f}{:3s}".format(num, "Yi" + suffix)


def build_tree(path, target_level, level):
    """Return total size of files in path and subdirs. If
    is_dir() or stat() fails, print an error message to stderr
    and assume zero size (for example, file has been deleted).
    """
    total_size = 0
    num_files = 0
    directory = Directory(path, level)
    for entry in os.scandir(path):
        try:
            is_dir = entry.is_dir(follow_symlinks=False)
        except OSError as error:
            print('Error calling is_dir():', error, file=sys.stderr)
            continue
        if is_dir:
            sub_directory = build_tree(entry.path, target_level, level+1)
            if level < target_level:
                directory.sub_directories.append(sub_directory)
            directory.size_in_bytes += sub_directory.size_in_bytes
            directory.num_files += sub_directory.num_files
        else:
            try:
                size_in_bytes += entry.stat(follow_symlinks=False).st_size
                directory.size_in_bytes += size_in_bytes
                directory.num_files += 1
            except OSError as error:
                print('Error calling stat():', error, file=sys.stderr)
    return directory


def print_tree(directory):
    print(directory)
    sub_dirs_sorted = sorted(
        directory.sub_directories,
        key=attrgetter("size_in_bytes"),
        reverse=True
    )
    for sub_directory in sub_dirs_sorted:
        print_tree(sub_directory)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("directory")
    args = parser.parse_args()

    start = time()
    directory = build_tree(args.directory, 2, 0)
    print_tree(directory)
    elapsed = time() - start
    print("Time in seconds: {}".format(elapsed))
