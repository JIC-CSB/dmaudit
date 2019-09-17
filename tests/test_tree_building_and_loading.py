import os

from . import DATA_DIR, TREE_DIR

def test_tree_building_and_loading():

    from dmaudit.utils import build_tree, DirectoryTreeSummary

    target_level = 1
    level = 0
    tree_l1 = build_tree(TREE_DIR, TREE_DIR, target_level, level)

    persisted_l1_fpath = os.path.join(DATA_DIR, "tree_l1.json")
    with open(persisted_l1_fpath, "r") as fh:
        tree_l1_from_persited = DirectoryTreeSummary.from_file(fh)

    assert tree_l1.to_dict() == tree_l1_from_persited.to_dict()
