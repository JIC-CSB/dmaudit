"""dmaudit command line interferface."""

import os
import datetime

from time import time
from operator import attrgetter

import click

from dmaudit import __version__
from dmaudit.utils import build_tree


LOGO = """     _                           _ _ _
    | |                         | (_) |
  __| |_ __ ___   __ _ _   _  __| |_| |_
 / _` | '_ ` _ \ / _` | | | |/ _` | | __|
| (_| | | | | | | (_| | |_| | (_| | | |_
 \__,_|_| |_| |_|\__,_|\__,_|\__,_|_|\__|
"""  # NOQA

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


def echo(tree, check_mimetype):
    click.secho(sizeof_fmt(tree.size_in_bytes) + " ", nl=False)

    if check_mimetype:
        click.secho(sizeof_fmt(tree.size_in_bytes_text) + " ", nl=False)
        click.secho(sizeof_fmt(tree.size_in_bytes_gzip) + " ", nl=False)

    click.secho("{:7d}".format(tree.num_files) + " ", nl=False)
    click.secho(date_fmt(tree.last_touched) + " ", nl=False)
    color_index = tree.level % len(LEVEL_COLORS)
    level_color = LEVEL_COLORS[color_index]
    if tree.level != 0:
        click.secho("-" * tree.level + " ", nl=False, fg=level_color)
    click.secho(os.path.basename(tree.path), fg=level_color)


def print_tree(directory, sort_by, reverse, check_mimetype=False):

    echo(directory, check_mimetype=check_mimetype)
    sub_dirs_sorted = sorted(
        directory.subdirectories,
        key=attrgetter(SORT_LOOKUP[sort_by]),
        reverse=reverse
    )
    for subdir in sub_dirs_sorted:
        print_tree(subdir, sort_by, reverse, check_mimetype)


@click.command()
@click.version_option(__version__)
@click.argument(
    "directory",
    type=click.Path(exists=True, file_okay=False, resolve_path=True)
)
@click.option(
    "-l", "--level",
    type=int,
    default=2,
    help="Number of levels of nesting to report (default 2)"
)
@click.option(
    "-s", "--sort-by",
    type=click.Choice(["size", "mtime", "name"]),
    default="size",
    help="Parameter to sort by (default size)"
)
@click.option("-r", "--reverse", default=False, is_flag=True)
@click.option(
    "-m", "--check-mimetype",
    is_flag=True,
    default=False,
    help="Report stats of file mimetypes (can be slow)"
)
def dmaudit(directory, level, sort_by, reverse, check_mimetype):
    start = time()

    click.secho(LOGO, fg="blue")
    click.secho("dmaudit version   : ", nl=False)
    click.secho(__version__, fg="green")
    click.secho("Auditing directory: ", nl=False)
    click.secho(directory, fg="green")

    directory = build_tree(
        path=directory,
        start_path=directory,
        target_level=level,
        level=0,
        check_mimetype=check_mimetype
    )

    elapsed = time() - start
    click.secho("Time in seconds   : ", nl=False)
    click.secho("{:.2f}".format(elapsed), fg="green")

    click.secho("")

    if sort_by == "size":
        # Want largest object first.
        reverse = not reverse

    header = "    Total  #files Last write"
    if check_mimetype:
        header = "    Total      text      gzip  #files Last write"

    click.secho(header, fg="blue")

    print_tree(
        directory=directory,
        sort_by=sort_by,
        reverse=reverse,
        check_mimetype=check_mimetype
    )
