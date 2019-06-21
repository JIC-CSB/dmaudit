"""Bioinformatics data management audit of a directory tree."""

import datetime
import json
import os
import sys

from operator import attrgetter
from time import time

import click
import magic

LEVEL_COLORS = [
    None,
    "bright_cyan",
    "bright_magenta",
    "blue",
    "magenta",
    "cyan",
    "bright_blue",
]

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

    def print(self):
        click.secho(sizeof_fmt(self.size_in_bytes) + " ", nl=False)
        click.secho(sizeof_fmt(self.size_in_bytes_text) + " ", nl=False)
        click.secho(sizeof_fmt(self.size_in_bytes_gzip) + " ", nl=False)
        click.secho("{:7d}".format(self.num_files) + " ", nl=False)
        click.secho(date_fmt(self.last_touched) + " ", nl=False)
        color_index = self.level % len(LEVEL_COLORS)
        level_color = LEVEL_COLORS[color_index]
        click.secho("-" * self.level + " ", nl=False, fg=level_color)
        click.secho(os.path.basename(self.path), fg=level_color)

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
    directory.print()
    sub_dirs_sorted = sorted(
        directory.subdirectories,
        key=attrgetter(SORT_LOOKUP[sort_by]),
        reverse=reverse
    )
    for subdir in sub_dirs_sorted:
        print_tree(subdir, sort_by, reverse)


@click.command()
@click.argument("directory")
@click.option("-l", "--level", type=int, default=2)
@click.option(
    "-s", "--sort-by",
    type=click.Choice(["size", "mtime", "name"]),
    default="size"
)
@click.option("-r", "--reverse", default=False)
def dmaudit(directory, level, sort_by, reverse):
    start = time()

    directory = build_tree(directory, level, 0)

    print("    Total      text    gzip    #files Last write")

    print_tree(directory, sort_by=sort_by, reverse=reverse)

    elapsed = time() - start

    print("Time in seconds: {}".format(elapsed))


if __name__ == "__main__":
    dmaudit()
