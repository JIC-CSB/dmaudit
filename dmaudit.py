"""Bioinformatics data management audit of a directory tree."""
import argparse
import datetime
import os
import sys

from operator import attrgetter
from time import time

SORT_LOOKUP = {
    "size": "size_in_bytes",
    "mtime": "last_touched",
    "name": "path",
    "num_files": "num_files",
}


class Directory(object):
    """Summary information about a directory."""

    def __init__(self, path, level):
        self.path = path
        self.level = level
        self.size_in_bytes = 0
        self.num_files = 0
        self.sub_directories = []
        self.last_touched = 0

    def __str__(self):
        return "{} {:7d} {} {}{}".format(
            sizeof_fmt(self.size_in_bytes),
            self.num_files,
            date_fmt(self.last_touched),
            "-" * self.level,
            os.path.basename(self.path)
        )

    def update_last_touched(self, timestamp):
        if timestamp > self.last_touched:
            self.last_touched = timestamp


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "{:6.1f}{:3s}".format(num, unit + suffix)
        num /= 1024.0
    return "{:6.1f}{:3s}".format(num, "Yi" + suffix)


def date_fmt(timestamp):
    timestamp = float(timestamp)
    datetime_obj = datetime.datetime.fromtimestamp(timestamp)
    return datetime_obj.strftime("%Y-%m-%d")


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
            directory.update_last_touched(sub_directory.last_touched)
        else:
            try:
                stat = entry.stat(follow_symlinks=False)
                directory.size_in_bytes += stat.st_size
                directory.num_files += 1
                last_touched = stat.st_mtime
                directory.update_last_touched(last_touched)
            except OSError as error:
                print('Error calling stat():', error, file=sys.stderr)
    return directory


def print_tree(directory, sort_by, reverse):
    print(directory)
    sub_dirs_sorted = sorted(
        directory.sub_directories,
        key=attrgetter(SORT_LOOKUP[sort_by]),
        reverse=reverse
    )
    for sub_directory in sub_dirs_sorted:
        print_tree(sub_directory, sort_by, reverse)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("directory")
    parser.add_argument("-s", "--sort-by", choices=["size", "mtime", "name"], default="size")  # NOQA
    parser.add_argument("-r", "--reverse", action="store_true")
    args = parser.parse_args()

    start = time()
    directory = build_tree(args.directory, 2, 0)
    print_tree(directory, sort_by=args.sort_by, reverse=args.reverse)
    elapsed = time() - start
    print("Time in seconds: {}".format(elapsed))
