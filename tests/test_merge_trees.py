"""Test merging of trees."""

def test_tree_merge():
    from dmaudit.utils import DirectoryTreeSummary, merge_trees

    tree_1 = DirectoryTreeSummary("dir1", 1)
    tree_2 = DirectoryTreeSummary("dir2", 1)

    tree_1.size_in_bytes = 25
    tree_1.num_files = 3
    tree_1.last_touched = 1500000000
    tree_1.size_in_bytes_compressed = 14

    tree_2.size_in_bytes = 50
    tree_2.num_files = 4
    tree_2.last_touched = 1400000000
    tree_2.size_in_bytes_compressed = 16

    tree = merge_trees(".", 0, tree_1, tree_2)
    assert isinstance(tree, DirectoryTreeSummary)

    assert tree.size_in_bytes == 75
    assert tree.num_files == 7
    assert tree.last_touched == 1500000000
    assert tree.size_in_bytes_compressed == 30

    assert tree_1 in tree.subdirectories
    assert tree_2 in tree.subdirectories
