"""Bioinformatics data management audit of a directory tree."""

import json
import logging
import os


import magic

logger = logging.Logger(__name__)


class DirectoryTreeSummary(object):
    """Summary information about a directory tree."""

    def __init__(self, path, start_path, level):
        self.path = os.path.relpath(path, start_path)
        self.level = level
        self.size_in_bytes = 0
        self.num_files = 0
        self.last_touched = 0
        self.subdirectories = []

        self.size_in_bytes_text = 0
        self.size_in_bytes_gzip = 0

    def update_last_touched(self, timestamp):
        if timestamp > self.last_touched:
            self.last_touched = timestamp

    def to_dict(self):
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
            data["subdirectories"].append(d.to_dict())
        return data

    def to_json(self, fh=None):
        """Return DirectoryTreeSummary as JSON string."""
        if fh is None:
            json.dumps(self.to_dict(), indent=2)
        else:
            json.dump(self.to_dict(), fh, indent=2)

    @classmethod
    def from_dict(cls, data):
        """Return DirectoryTreeSummary from Python dictionary."""
        dts = cls(data["path"], ".", data["level"])
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


def build_tree(path, start_path, target_level, level, check_mimetype=False):
    """Return total size of files in path and subdirs. If
    is_dir() or stat() fails, log the error message
    and assume zero size (for example, file has been deleted).
    """
    directory = DirectoryTreeSummary(path, start_path, level)
    try:
        for entry in os.scandir(path):
            try:
                is_dir = entry.is_dir(follow_symlinks=False)
            except OSError as error:
                logger.info('Error calling is_dir(): {}'.format(error))
                continue
            if is_dir:
                subdir = build_tree(
                    path=entry.path,
                    start_path=start_path,
                    target_level=target_level,
                    level=level+1,
                    check_mimetype=check_mimetype)
                if level < target_level:
                    directory.subdirectories.append(subdir)
                directory.size_in_bytes += subdir.size_in_bytes
                directory.size_in_bytes_text += subdir.size_in_bytes_text
                directory.size_in_bytes_gzip += subdir.size_in_bytes_gzip
                directory.num_files += subdir.num_files
                directory.update_last_touched(subdir.last_touched)
            else:
                try:
                    stat = entry.stat(follow_symlinks=False)
                    directory.size_in_bytes += stat.st_size
                    directory.num_files += 1
                    directory.update_last_touched(stat.st_mtime)
                    if check_mimetype:
                        mimetype = magic.from_file(entry.path, mime=True)
                        if mimetype.startswith("text"):
                            directory.size_in_bytes_text += stat.st_size
                        elif mimetype == "application/x-gzip":
                            directory.size_in_bytes_gzip += stat.st_size
                except OSError as error:
                    logger.info('Error calling stat(): {}'.format(error))
    except (FileNotFoundError, PermissionError) as error:
        # FileNotFoundError: Directory of interested deleted before os.scandir
        #                    called.
        # PermissionError: Lacking permissions to read directory of interest.
        # Assume zero size.
        logger.info("Error calling os.scandir({}): {}".format(path, error))

    return directory
