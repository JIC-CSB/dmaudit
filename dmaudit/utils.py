"""Bioinformatics data management audit of a directory tree."""

import json
import logging
import multiprocessing
import os


import puremagic

logger = logging.Logger(__name__)

COMPRESSED_MIMETYPES = set([
    "application/x-bzip2",
    "application/x-gzip",
    "application/x-lzip",
    "application/x-lzma",
    "application/x-lzop",
    "application/x-snappy-framed",
    "application/x-xz",
    "application/x-compress",
    "application/x-7z-compressed",
    "application/x-ace-compressed",
    "application/x-astrotite-afa",
    "application/x-alz-compressed",
    "application/vnd.android.package-archive",
    "application/octet-stream",
    "application/x-freearc",
    "application/x-arj",
    "application/x-b1",
    "application/vnd.ms-cab-compressed",
    "application/x-cfs-compressed",
    "application/x-dar",
    "application/x-dgc-compressed",
    "application/x-apple-diskimage",
    "application/x-gca-compressed",
    "application/java-archive",
    "application/x-lzh",
    "application/x-lzx",
    "application/x-rar-compressed",
    "application/x-stuffit",
    "application/x-gtar",
    "application/x-ms-wim",
    "application/x-xar",
    "application/zip",
    "application/x-zoo"
])


def is_compressed(mimetype):
    return mimetype in COMPRESSED_MIMETYPES


class DirectoryTreeSummary(object):
    """Summary information about a directory tree."""

    def __init__(self, relpath, level):
        self.relpath = relpath
        self.level = level
        self.size_in_bytes = 0
        self.num_files = 0
        self.last_touched = 0
        self.subdirectories = []

        self.size_in_bytes_compressed = 0

    def update_last_touched(self, timestamp):
        if timestamp > self.last_touched:
            self.last_touched = timestamp

    def to_dict(self):
        """Return dictionary representation of the directory tree summary."""
        data = {
            "relpath": self.relpath,
            "level": self.level,
            "size_in_bytes": self.size_in_bytes,
            "size_in_bytes_compressed": self.size_in_bytes_compressed,
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
        dts = cls(data["path"],  data["level"])
        dts.size_in_bytes = data["size_in_bytes"]
        dts.size_in_bytes_compressed = data["size_in_bytes_compressed"]
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


def get_mimetype(fpath):
    """Return mimetype of a file."""
    try:
        possibilities = puremagic.magic_file(fpath)
    except ValueError:  # File is empty.
        return "unknown/unknown"
    if len(possibilities) > 0:
        return possibilities[0].mime_type
    else:
        return "unknown/unknown"


def build_tree(path, start_path, target_level, level, check_mimetype=False):
    """Return total size of files in path and subdirs. If
    is_dir() or stat() fails, log the error message
    and assume zero size (for example, file has been deleted).
    """
    relpath = os.path.relpath(path, start_path)
    directory = DirectoryTreeSummary(relpath, level)
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
                directory.size_in_bytes_compressed += subdir.size_in_bytes_compressed  # NOQA
                directory.num_files += subdir.num_files
                directory.update_last_touched(subdir.last_touched)
            else:
                try:
                    stat = entry.stat(follow_symlinks=False)
                    directory.size_in_bytes += stat.st_size
                    directory.num_files += 1
                    directory.update_last_touched(stat.st_mtime)
                    if check_mimetype:
                        mimetype = get_mimetype(entry.path)
                        if is_compressed(mimetype):
                            directory.size_in_bytes_compressed += stat.st_size
                except OSError as error:
                    logger.info('Error calling stat(): {}'.format(error))
    except (FileNotFoundError, PermissionError) as error:
        # FileNotFoundError: Directory of interested deleted before os.scandir
        #                    called.
        # PermissionError: Lacking permissions to read directory of interest.
        # Assume zero size.
        logger.info("Error calling os.scandir({}): {}".format(path, error))

    return directory


def add_subtree(tree, subtree):
    """Return merged tree."""
    tree.size_in_bytes = tree.size_in_bytes + subtree.size_in_bytes
    tree.num_files = tree.num_files + subtree.num_files
    tree.size_in_bytes_compressed = tree.size_in_bytes_compressed + subtree.size_in_bytes_compressed  # NOQA
    if tree.last_touched < subtree.last_touched:
        tree.last_touched = subtree.last_touched
    tree.subdirectories.append(subtree)


def build_tree_multiprocessing(path, start_path, target_level, level, check_mimetype):
    jobs = []
    try:
        for entry in os.scandir(path):
            try:
                is_dir = entry.is_dir(follow_symlinks=False)
            except OSError as error:
                logger.info('Error calling is_dir(): {}'.format(error))
                continue
            if is_dir:
                j = (
                    entry.path,
                    start_path,
                    target_level,
                    1,
                    check_mimetype
                )
                jobs.append(j)
    except (FileNotFoundError, PermissionError) as error:
        logger.info("Error calling os.scandir({}): {}".format(path, error))



    tree = DirectoryTreeSummary(".", 0)
    with multiprocessing.Pool(processes=4) as p:
        for subtree in p.starmap(build_tree, jobs):
            add_subtree(tree, subtree)

    return tree
