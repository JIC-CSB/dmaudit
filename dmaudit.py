"""Bioinformatics data management audit of a directory tree."""
import argparse
import datetime
import json
import os
import sys

from operator import attrgetter
from time import time

import magic

SORT_LOOKUP = {
    "size": "size_in_bytes",
    "mtime": "last_touched",
    "name": "path",
    "num_files": "num_files",
}


class DirectoryTreeSummary(object):
    """Summary information about a directory tree."""

    def __init__(self, path, level):
        self.path = path
        self.level = level
        self.size_in_bytes = 0
        self.num_files = 0
        self.last_touched = 0
        self.subdirectories = []

        self.size_in_bytes_text = 0
        self.size_in_bytes_gzip = 0

    def __str__(self):
        return "{} {:7} {:7} {:7d} {} {}{}".format(
            sizeof_fmt(self.size_in_bytes),
            sizeof_fmt(self.size_in_bytes_text),
            sizeof_fmt(self.size_in_bytes_gzip),
            self.num_files,
            date_fmt(self.last_touched),
            "-" * self.level,
            os.path.basename(self.path)
        )

    def update_last_touched(self, timestamp):
        if timestamp > self.last_touched:
            self.last_touched = timestamp

    def as_dict(self):
        """Return dictionary representation of the directory tree summary."""
        data = {
            "path": self.path,
            "level": self.level,
            "size_in_bytes": self.size_in_bytes,
            "size_in_bytes_text": self.size_in_bytes_text,
            "size_in_bytes_gzip": self.size_in_bytes_gzip,
            "num_files": self.num_files,
            "last_touched": self.last_touched,
            "subdirectories": [],
        }
        for d in self.subdirectories:
            data["subdirectories"].append(d.as_dict())
        return data

    def to_json(self, fh=None):
        """Return DirectoryTreeSummary as JSON string."""
        if fh is None:
            json.dumps(self.as_dict(), indent=2)
        else:
            json.dumps(self.as_dict(), fh, indent=2)

    @classmethod
    def from_dict(cls, data):
        """Return DirectoryTreeSummary from Python dictionary."""
        dts = cls(data["path"], data["level"])
        dts.size_in_bytes = data["size_in_bytes"]
        dts.size_in_bytes_text = data["size_in_bytes_text"]
        dts.size_in_bytes_gzip = data["size_in_bytes_gzip"]
        dts.num_files = data["num_files"]
        dts.last_touched = data["last_touched"]

        dts.subdirectories = []

        for subdir in data["subdirectories"]:
            dts.subdirectories.append(cls.from_dict(subdir))

        return dts

    @classmethod
    def from_json(cls, json_str):
        """Return DirectoryTreeSummary from JSON string."""
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def from_file(cls, fh):
        """Return DirectoryTreeSummary from JSON file handle."""
        return cls.from_dict(json.load(fh))


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
    directory = DirectoryTreeSummary(path, level)
    for entry in os.scandir(path):
        try:
            is_dir = entry.is_dir(follow_symlinks=False)
        except OSError as error:
            print('Error calling is_dir():', error, file=sys.stderr)
            continue
        if is_dir:
            subdir = build_tree(entry.path, target_level, level+1)
            if level < target_level:
                directory.subdirectories.append(subdir)
            directory.size_in_bytes += subdir.size_in_bytes
            directory.num_files += subdir.num_files
            directory.update_last_touched(subdir.last_touched)
        else:
            try:
                stat = entry.stat(follow_symlinks=False)
                directory.size_in_bytes += stat.st_size
                directory.num_files += 1
                directory.update_last_touched(stat.st_mtime)
                mimetype = magic.from_file(entry.path, mime=True)
                if mimetype.startswith("text"):
                    directory.size_in_bytes_text = stat.st_size
                elif mimetype == "application/x-gzip":
                    directory.size_in_bytes_gzip = stat.st_size
            except OSError as error:
                print('Error calling stat():', error, file=sys.stderr)
    return directory


def print_tree(directory, sort_by, reverse):
    print(directory)
    sub_dirs_sorted = sorted(
        directory.subdirectories,
        key=attrgetter(SORT_LOOKUP[sort_by]),
        reverse=reverse
    )
    for subdir in sub_dirs_sorted:
        print_tree(subdir, sort_by, reverse)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("directory")
    parser.add_argument("-s", "--sort-by", choices=["size", "mtime", "name"], default="size")  # NOQA
    parser.add_argument("-r", "--reverse", action="store_true")
    args = parser.parse_args()

    start = time()

    directory = build_tree(args.directory, 2, 0)

    print("    Total      text    gzip    #files Last write")

    print_tree(directory, sort_by=args.sort_by, reverse=args.reverse)

    elapsed = time() - start

    print("Time in seconds: {}".format(elapsed))
