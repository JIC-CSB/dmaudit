"""Test the dmaudit command line tool."""

import os

from click.testing import CliRunner
from dmaudit.cli import dmaudit

from . import TREE_DIR, DATA_DIR


def test_dmaudit_report():
    runner = CliRunner()
    result = runner.invoke(dmaudit, ['report', '-l', '1', TREE_DIR])

    assert result.exit_code == 0

    assert result.output.find("    Total  #files Last write") != -1
    assert result.output.find(" 810.0B        27 2019-09-17 .") != -1
    assert result.output.find(" 432.0B         9 2019-09-17 - l1_d3") != -1
    assert result.output.find(" 270.0B         9 2019-09-17 - l1_d2") != -1
    assert result.output.find(" 108.0B         9 2019-09-17 - l1_d1") != -1

    assert len(result.output.split("\n")) == 17


def test_dmaudit_mimetype():
    runner = CliRunner()

    fpath = os.path.join(DATA_DIR, "tree.tar.gz")
    result = runner.invoke(dmaudit, ['mimetype', fpath])

    assert result.exit_code == 0

    assert result.output.strip() == "application/x-gzip"


def test_dmaudit_mimetype_on_empty_file():
    runner = CliRunner()

    fpath = os.path.join(DATA_DIR, "empty.txt")
    result = runner.invoke(dmaudit, ['mimetype', fpath])

    assert result.exit_code == 0

    assert result.output.strip() == "unknown/unknown"
