"""Test the dmaudit command line tool."""

from click.testing import CliRunner
from dmaudit.cli import dmaudit

from . import TREE_DIR


def test_dmaudit():
    runner = CliRunner()
    result = runner.invoke(dmaudit, ['-l', '1', TREE_DIR])

    assert result.exit_code == 0

    assert result.output.find("    Total  #files Last write") != -1
    assert result.output.find(" 810.0B        27 2019-09-17 .") != -1
    assert result.output.find(" 432.0B         9 2019-09-17 - l1_d3") != -1
    assert result.output.find(" 270.0B         9 2019-09-17 - l1_d2") != -1
    assert result.output.find(" 108.0B         9 2019-09-17 - l1_d1") != -1

    assert len(result.output.split("\n")) == 17
